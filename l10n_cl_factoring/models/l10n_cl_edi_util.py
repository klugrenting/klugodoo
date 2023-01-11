# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import base64
import logging
import re
import textwrap
import collections
import urllib3
from werkzeug.urls import url_join
import requests
from markupsafe import Markup
from functools import wraps
from html import unescape
from lxml import etree
from odoo import _, models, fields
from zeep import Client
from urllib3.exceptions import NewConnectionError
from requests.exceptions import ConnectionError, HTTPError
from zeep.exceptions import TransportError
from zeep.transports import Transport
from odoo.tools import xml_utils
TIMEOUT = 30 # default timeout for all remote operations
pool = urllib3.PoolManager(timeout=TIMEOUT)

_logger = logging.getLogger(__name__)

SERVER_URL = {
    'SIITEST': 'https://maullin.sii.cl/DTEWS/',
    'SII': 'https://palena.sii.cl/DTEWS/',
}

MAX_RETRIES = 20
TIMEOUT_REST = 5

def l10n_cl_edi_retry(max_retries=MAX_RETRIES, logger=None, custom_msg=None):
    """
    This custom decorator allows to manage retries during connection request to SII.
    This is needed because Zeep library cannot manage the parsing of HTML format responses
    that sometimes are delivered by SII instead of XML format.
    """

    def deco_retry(func):
        @wraps(func)
        def wrapper_retry(self, *args):
            retries = max_retries
            while retries > 0:
                try:
                    return func(self, *args)
                except (TransportError, NewConnectionError, HTTPError, ConnectionError) as error:
                    if custom_msg is not None:
                        logger.error(custom_msg)
                    if logger is not None:
                        logger.error(error)
                    retries -= 1
                except Exception as error:
                    self._report_connection_err(error)
                    logger.error(error)
                    break
            msg = _('- It was not possible to get a seed after %s retries.') % max_retries
            if custom_msg is not None:
                msg = custom_msg + msg
            self._report_connection_err(msg)

        return wrapper_retry

    return deco_retry

class L10nClEdiUtilMixin(models.AbstractModel):
    _inherit = 'l10n_cl.edi.util'

    def _xml_validator(self, xml_to_validate, validation_type, is_doc_type_voucher=False):
        """
        This method validates the format description of the xml files
        http://www.sii.cl/factura_electronica/formato_dte.pdf
        http://www.sii.cl/factura_electronica/formato_retenedores.pdf
        http://www.sii.cl/factura_electronica/formato_iecv.pdf
        http://www.sii.cl/factura_electronica/formato_lgd.pdf
        http://www.sii.cl/factura_electronica/formato_ic.pdf
        http://www.sii.cl/factura_electronica/desc_19983.pdf
        http://www.sii.cl/factura_electronica/boletas_elec.pdf
        http://www.sii.cl/factura_electronica/libros_boletas.pdf
        http://www.sii.cl/factura_electronica/consumo_folios.pdf

        :param xml_to_validate: xml to validate
        :param validation_type: the type of the document
        :return: whether the xml is valid. If the XSD files are not found returns True
        """
        validation_types = {
            'doc': 'DTE_v10.xsd',
            'env': 'EnvioDTE_v10.xsd',
            'bol': 'EnvioBOLETA_v11.xsd',
            'recep': 'Recibos_v10.xsd',
            'env_recep': 'EnvioRecibos_v10.xsd',
            'env_resp': 'RespuestaEnvioDTE_v10.xsd',
            'sig': 'xmldsignature_v10.xsd',
            'book': 'LibroCV_v10.xsd',
            'consu': 'ConsumoFolio_v10.xsd',
            'aec': 'AEC_v10.xsd',
            'dte_cedido': 'DTECedido_v10.xsd',
            'recibos': 'Recibos_v10.xsd',
            'cesion': 'Cesion_v10.xsd',
        }
        # Token document doesn't required validation and the "Boleta" document is not validated since the DescuentoPct
        # tag doesn't work properly
        if validation_type in ('token', 'bol') or (validation_type == 'doc' and is_doc_type_voucher):
            return True
        xsd_fname = validation_types[validation_type]
        try:
            return xml_utils._check_with_xsd(xml_to_validate, xsd_fname, self.sudo().env)
        except FileNotFoundError:
            _logger.warning(
                _('The XSD validation files from SII has not been found, please run manually the cron: "Download XSD"'))
            return True

    def _l10n_cl_append_sig(self, xml_type, sign, message):
        tag_to_replace = {
            'doc': '</DTE>',
            'bol': '</EnvioBOLETA>',
            'env': '</EnvioDTE>',
            'recep': '</Recibo>',
            'env_recep': '</EnvioRecibos>',
            'env_resp': '</RespuestaDTE>',
            'consu': '</ConsumoFolios>',
            'token': '</getToken>',
            'dte_cedido': '</DTECedido>',
            'cesion': '</Cesion>',
            'aec': '</AEC>'
        }
        tag = tag_to_replace.get(xml_type, '</EnvioBOLETA>')
        return message.replace(tag, '%s%s' % (sign, tag))

    def _sign_full_xml_cesion(self, message, digital_signature, uri, xml_type, is_doc_type_voucher=False):
        """
        Signed the xml following the SII documentation:
        http://www.sii.cl/factura_electronica/factura_mercado/instructivo_emision.pdf
        """
        digest_value = re.sub(r'\n\s*$', '', message, flags=re.MULTILINE)
        digest_value =  digest_value.replace('&lt;', '<').replace('&gt;', '>').replace('&#34;', '"') if '&lt;' in digest_value and '&gt;' in digest_value and '&#34' in digest_value else digest_value
        digest_value_tree = etree.tostring(etree.fromstring(digest_value)[0])
        if xml_type in ['doc', 'recep', 'token']:
            signed_info_template = self.env.ref('l10n_cl_edi.signed_info_template')
        else:
            signed_info_template = self.env.ref('l10n_cl_edi.signed_info_template_with_xsi')
        signed_info = signed_info_template._render({
            'uri': '#{}'.format(uri),
            'digest_value': base64.b64encode(
                self._get_sha1_digest(etree.tostring(etree.fromstring(digest_value_tree), method='c14n'))).decode(),
        })
        signed_info_c14n = Markup(etree.tostring(etree.fromstring(signed_info), method='c14n', exclusive=False,
                                          with_comments=False, inclusive_ns_prefixes=None).decode())
        signature = self.env.ref('l10n_cl_edi.signature_template')._render({
            'signed_info': signed_info_c14n,
            'signature_value': self._sign_message(
                signed_info_c14n.encode('utf-8'), digital_signature.private_key.encode('ascii')),
            'modulus': digital_signature._get_private_key_modulus(),
            'exponent': digital_signature._get_private_key_exponent(),
            'certificate': '\n' + textwrap.fill(digital_signature.certificate, 64),
        })
        # The validation of the signature document
        self._xml_validator(signature, 'sig')
        full_doc = self._l10n_cl_append_sig(xml_type, signature, digest_value)
        # The validation of the full document
        # self._xml_validator(full_doc, xml_type, is_doc_type_voucher)
        return '{header}{full_doc}'.format(
            header='<?xml version="1.0" encoding="ISO-8859-1" ?>' if xml_type == 'aec' else '',
            full_doc=full_doc
        )

    def _send_xml_cesion_to_sii(self, mode, company_website, company_vat, file_name, xml_message, digital_signature,
                         post='/cgi_rtc/RTC/RTCAnotEnvio.cgi'):
                         #post='/cgi_rtc/RTC/RTCAnotEnvio.cgi'):
        """
        The header used here is explicitly stated as is, in SII documentation. See
        http://www.sii.cl/factura_electronica/factura_mercado/envio.pdf
        it says: as mentioned previously, the client program must include in the request header the following.....
        """
        digital_signature.last_token = False
        token = self._get_token(mode, digital_signature)
        if token is None:
            self._report_connection_err(_('No response trying to get a token'))
            return False
        url = SERVER_URL[mode].replace('/DTEWS/', '')
        headers = {
            'Accept': 'image/gif, image/x-xbitmap, image/jpeg, image/pjpeg, */*',
            'Accept-Language': 'es-cl',
            'Accept-Encoding': 'gzip, deflate',
            'User-Agent': 'Mozilla/4.0 (compatible; PROG 1.0; Windows NT 5.0; YComp 5.0.2.4)',
            'Referer': '{}'.format(company_website),
            'Connection': 'Keep-Alive',
            'Cache-Control': 'no-cache',
            'Cookie': 'TOKEN={}'.format(token),
        }
        params = collections.OrderedDict({
            'emailNotif': self.company_id.email,
            'rutCompany': self._l10n_cl_format_vat(company_vat)[:8],
            'dvCompany': self._l10n_cl_format_vat(company_vat)[-1],
            'archivo': (file_name, xml_message, 'text/xml'),
        })
        multi = urllib3.filepost.encode_multipart_formdata(params)
        headers.update({'Content-Length': '{}'.format(len(multi[0]))})
        try:
            response = pool.request_encode_body('POST', url + post, params, headers)
        except Exception as error:
            self._report_connection_err(_('Sending DTE to SII failed due to:') + '<br /> %s' % error)
            digital_signature.last_token = False
            return False
        print(response.data)
        return response.data
        # we tried to use requests. The problem is that we need the Content-Lenght and seems that requests
        # had the ability to send this provided the file is in binary mode, but did not work.
        # response = requests._post(url + post, headers=headers, files=params)
        # if response.status_code != 200:
        #     response.raise_for_status()
        # else:
        #     return response.text

    @l10n_cl_edi_retry(logger=_logger)
    def _get_send_status_ws_cesion(self, mode, company_vat, track_id, token, docType, folio):
        transport = Transport(operation_timeout=TIMEOUT)
        #return Client(SERVER_URL[mode] + 'services/wsRPETCConsulta?wsdl', transport=transport).service.getEstCesion(company_vat[:-2], company_vat[-1], track_id, token)
        serv =Client(SERVER_URL[mode] + 'services/wsRPETCConsulta?wsdl', transport=transport).service
        return serv.getEstEnvio(token, track_id)

    def _get_send_status_cesion(self, mode, track_id, company_vat, digital_signature, docType, folio):
        """
        Request the status of a DTE file sent to the SII.
        """
        digital_signature.last_token = False
        token = self._get_token(mode, digital_signature)
        if token is None:
            self._report_connection_err(_('Token cannot be generated. Please try again'))
            return False
        resp = self._get_send_status_ws_cesion(mode, company_vat, track_id, token, docType, folio)
        return resp