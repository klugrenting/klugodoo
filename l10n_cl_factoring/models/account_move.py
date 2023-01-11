from odoo import fields, models, api, _
import base64
import logging
from markupsafe import Markup
from html import unescape
from lxml import etree
from odoo.addons.l10n_cl_edi.models.l10n_cl_edi_util import UnexpectedXMLResponse
from odoo.tools.float_utils import float_repr, float_round

_logger = logging.getLogger(__name__)

class AccountMove(models.Model):
    _inherit = 'account.move'

    cesion_number = fields.Integer(copy=False, string='Cesion Number', default=0)
    declaracion_jurada = fields.Text(copy=False, string='Declaración Jurada')
    cesionario_id = fields.Many2one(comodel_name='res.partner', string="Cesionario")
    l10n_cl_dte_status_factoring = fields.Selection([
        ('not_sent', 'Pendiente de ser enviado'),
        ('ask_for_status', 'Consultar Estado Doc'),
        ('accepted', 'Aceptado'),
        ('objected', 'Aceptado con reparo'),
        ('rejected', 'Rechazado'),
        ('cancelled', 'Anulado'),
        ('manual', 'Manual'),
    ], string='SII CESION status', copy=False, tracking=True, help="""Status of sending the DTE to the SII:
        - Not sent: the DTE has not been sent to SII but it has created.
        - Ask For Status: The DTE is asking for its status to the SII.
        - Accepted: The DTE has been accepted by SII.
        - Accepted With Objections: The DTE has been accepted with objections by SII.
        - Rejected: The DTE has been rejected by SII.
        - Cancelled: The DTE has been deleted by the user.
        - Manual: The DTE is sent manually, i.e.: the DTE will not be sending manually.""")
    sii_cesion_message = fields.Text(
        string='SII Message',
        copy=False,
    )
    sii_xml_cesion_response = fields.Text(
        string='SII XML Response',
        copy=False)
    l10n_cl_dte_file_factoring = fields.Many2one('ir.attachment', string='DTE file factoring', copy=False)
    l10n_cl_sii_cesion_send_ident = fields.Text(string='SII Send Identification(Track ID)', readonly=False,
                                         copy=False, tracking=True)
    # imagen_ar_ids = fields.One2many(
    #     'account.move.imagen_ar',
    #     'move_id',
    #     string="Imagenes de acuse de recibo",
    # )

    @api.onchange('cesionario_id')
    def set_declaracion(self):
        if self.cesionario_id:
            declaracion_jurada = u'''Se declara bajo juramento que {0}, RUT {1} \
    ha puesto a disposicion del cesionario {2}, RUT {3}, el o los documentos donde constan los recibos de las mercaderías entregadas o servicios prestados, \
    entregados por parte del deudor de la factura {4}, RUT {5}, de acuerdo a lo establecido en la Ley No. 19.983'''.format(
                self.company_id.partner_id.name,
                self.company_id.partner_id.vat,
                self.cesionario_id.name,
                self.cesionario_id.vat,
                self.partner_id.commercial_partner_id.name,
                self.partner_id.commercial_partner_id.vat,
            )
            self.declaracion_jurada = declaracion_jurada

    def validate_cesion(self):
        for inv in self.with_context(lang='es_CL'):
            inv.l10n_cl_dte_status_factoring = 'not_sent'
            if inv.move_type in ['out_invoice'] and inv.l10n_latam_document_type_id.code in ['33', '34']:
                if inv.journal_id.l10n_latam_use_documents and inv.journal_id.l10n_cl_point_of_sale_type == 'manual':
                    inv.l10n_cl_dte_status_factoring = 'manual'
                else:
                    inv.cesion_number += 1
                    inv._l10n_cl_create_dte_cesion()

    # def create_dte(self):
    #     _logger.info('Creando DTE')
    #     folio = int(self.l10n_latam_document_number)
    #     doc_id_number = 'F{}T{}'.format(folio, self.l10n_latam_document_type_id.code)
    #     dte_barcode_xml = self._l10n_cl_get_dte_barcode_xml()
    #     self.l10n_cl_sii_barcode = dte_barcode_xml['barcode']
    #     dte = self.env.ref('l10n_cl_edi.dte_template')._render({
    #         'move': self,
    #         'format_vat': self._l10n_cl_format_vat,
    #         'get_cl_current_strftime': self._get_cl_current_strftime,
    #         'format_length': self._format_length,
    #         'float_repr': float_repr,
    #         'doc_id': doc_id_number,
    #         'caf': self.l10n_latam_document_type_id._get_caf_file(self.company_id.id,
    #                                                               int(self.l10n_latam_document_number)),
    #         'amounts': self._l10n_cl_get_amounts(),
    #         'withholdings': self._l10n_cl_get_withholdings(),
    #         'dte': dte_barcode_xml['ted'],
    #     })
    #     dte = unescape(dte.decode('utf-8')).replace(r'&', '&amp;')
    #     digital_signature = self.company_id._get_digital_signature(user_id=self.env.user.id)
    #     _logger.info('Validando y firmando DTE')
    #     signed_dte = self._sign_full_xml_cesion(
    #         dte, digital_signature, doc_id_number, 'doc', self.l10n_latam_document_type_id._is_doc_type_voucher())
    #     return signed_dte

    def create_factoring_document(self):
        _logger.info('Creando DTE Cedido')
        doc_id_number = 'DocCed_{}'.format(str(int(self.l10n_latam_document_number)))
        #signed_dte = self.create_dte()
        signed_dte = base64.b64decode(self.l10n_cl_dte_file.datas).decode('ISO-8859-1').replace('<?xml version="1.0" encoding="ISO-8859-1" ?>\n', '').strip()
        dte = self.env.ref('l10n_cl_factoring.factoring_document')._render({
            'doc_id': doc_id_number,
            'signed_dte': signed_dte,
            'stamp': self._get_cl_current_strftime()
        })
        digital_signature = self.company_id._get_digital_signature(user_id=self.env.user.id)
        _logger.info('Validando y firmando DTE Cedido')
        signed_dte = self._sign_full_xml_cesion(
            dte, digital_signature, doc_id_number, 'dte_cedido', self.l10n_latam_document_type_id._is_doc_type_voucher())
        return signed_dte

    def create_cesion_document(self):
        _logger.info('Creando Cesion')
        folio = str(self.cesion_number)
        doc_id_number = 'DocCed_{}'.format(folio)
        dte = self.env.ref('l10n_cl_factoring.cesion_document')._render({
            'move': self,
            'doc_id': doc_id_number,
            'format_length': self._format_length,
            'float_repr': float_repr,
            'format_vat': self._l10n_cl_format_vat,
            'amounts': self._l10n_cl_get_amounts(),
            'stamp': self._get_cl_current_strftime()
        })
        digital_signature = self.company_id._get_digital_signature(user_id=self.env.user.id)
        _logger.info('Validando y firmando CESION')
        signed_dte = self._sign_full_xml_cesion(
            dte, digital_signature, doc_id_number, 'cesion', self.l10n_latam_document_type_id._is_doc_type_voucher())
        return signed_dte

    def _l10n_cl_create_dte_cesion(self):
        folio = int(self.l10n_latam_document_number)
        doc_id_number = 'C%s%s' % (self.l10n_latam_document_type_id.doc_code_prefix, folio)
        dte_barcode_xml = self._l10n_cl_get_dte_barcode_xml()
        factoring_dte = self.create_factoring_document()
        cesion_dte = self.create_cesion_document()
        digital_signature = self.company_id._get_digital_signature(user_id=self.env.user.id)
        dte_cesion = self.env.ref('l10n_cl_factoring.dte_factoring')._render({
            'move': self,
            'signature': digital_signature,
            'format_vat': self._l10n_cl_format_vat,
            'get_cl_current_strftime': self._get_cl_current_strftime,
            'format_length': self._format_length,
            'float_repr': float_repr,
            'doc_id': doc_id_number,
            'amounts': self._l10n_cl_get_amounts(),
            'withholdings': self._l10n_cl_get_withholdings(),
            'dte': dte_barcode_xml['ted'],
            'factoring_dte': factoring_dte,
            'cesion_dte': cesion_dte,
            'stamp': self._get_cl_current_strftime()
        })
        digital_signature = self.company_id._get_digital_signature(user_id=self.env.user.id)
        _logger.info('Validando XML AEC')
        dte_cesion = self._sign_full_xml_cesion(
            dte_cesion, digital_signature, doc_id_number, 'aec', self.l10n_latam_document_type_id._is_doc_type_voucher())
        dte_attachment = self.env['ir.attachment'].create({
            'name': 'CES_{}_{}.xml'.format(self.l10n_latam_document_type_id.code, self.l10n_latam_document_number),
            'res_model': self._name,
            'res_id': self.id,
            'type': 'binary',
            'datas': base64.b64encode(dte_cesion.encode('ISO-8859-1'))
        })
        self.l10n_cl_dte_file_factoring = dte_attachment.id

    def l10n_cl_send_dte_cesion_to_sii(self, retry_send=True):
        """
        Send the DTE to the SII. It will be
        """
        digital_signature = self.company_id._get_digital_signature(user_id=self.env.user.id)
        response = self._send_xml_cesion_to_sii(
            self.company_id.l10n_cl_dte_service_provider,
            self.company_id.website,
            self.company_id.vat,
            self.l10n_cl_dte_file_factoring.name,
            base64.b64decode(self.l10n_cl_dte_file_factoring.datas),
            digital_signature
        )
        if not response:
            return None
        
        response_parsed = etree.fromstring(response)
        self.l10n_cl_sii_cesion_send_ident = response_parsed.findtext('TRACKID')
        sii_response_status = response_parsed.findtext('STATUS')
        if sii_response_status == '5':
            digital_signature.last_token = False
            _logger.error('The response status is %s. Clearing the token.' %
                          self._l10n_cl_get_sii_reception_status_message(sii_response_status))
            if retry_send:
                _logger.info('Retrying send DTE to SII')
                self.l10n_cl_send_dte_cesion_to_sii(retry_send=False)

            # cleans the token and keeps the l10n_cl_dte_status until new attempt to connect
            # would like to resend from here, because we cannot wait till tomorrow to attempt
            # a new send
        else:
            self.l10n_cl_dte_status_factoring = 'ask_for_status' if sii_response_status == '0' else 'rejected'
        self.message_post(body=('La CESION del DTE ha sido enviada al SII con la siguiente respuesta: %s.') %
                               self._l10n_cl_get_sii_reception_status_message(sii_response_status))

    def _analyze_sii_cesion_result(self, xml_message):
        """
        Returns the status of the DTE from the sii_message. The status could be:
        - ask_for_status
        - accepted
        - rejected
        """
        result_dict = {
            'ask_for_status': ['SDK', 'CRT', 'PDR', '-11', 'SOK'],
            'rejected': ['-3', 'PRD', 'RCH', 'RFR', 'RSC', 'RCT', '2', '106', 'DNK', 'RLV', '05'],
        }
        status = xml_message.find('{http://www.sii.cl/XMLSchema}RESP_HDR/{http://www.sii.cl/XMLSchema}ESTADO')
        for key, values in result_dict.items():
            if status is not None and status.text in values:
                return key
        reject = xml_message.findtext('{http://www.sii.cl/XMLSchema}RESP_BODY/RECHAZADOS')
        if reject and int(reject) >= 1:
            return 'rejected'
        accepted = xml_message.findtext('{http://www.sii.cl/XMLSchema}RESP_BODY/ACEPTADOS')
        informed = xml_message.findtext('{http://www.sii.cl/XMLSchema}RESP_BODY/INFORMADOS')
        objected = xml_message.findtext('{http://www.sii.cl/XMLSchema}RESP_BODY/REPAROS')
        if accepted is not None and informed is not None and accepted == informed:
            return 'accepted'
        if objected and int(objected) >= 1:
            return 'objected'

        raise UnexpectedXMLResponse()

    def l10n_cl_verify_cesion_dte_status(self, send_dte_to_partner=True):
        digital_signature = self.company_id._get_digital_signature(user_id=self.env.user.id)
        response = self._get_send_status_cesion(
            self.company_id.l10n_cl_dte_service_provider,
            self.l10n_cl_sii_cesion_send_ident,
            self._l10n_cl_format_vat(self.company_id.vat),
            digital_signature,
            int(self.l10n_latam_document_type_id.code),
            int(self.l10n_latam_document_number))
        if not response:
            self.l10n_cl_dte_status_factoring = 'ask_for_status'
            digital_signature.last_token = False
            return None

        response_parsed = etree.fromstring(response.encode('utf-8'))
        status = response_parsed.findtext('{http://www.sii.cl/XMLSchema}RESP_HDR/{http://www.sii.cl/XMLSchema}ESTADO')
        if response_parsed.findtext('{http://www.sii.cl/XMLSchema}RESP_HDR/{http://www.sii.cl/XMLSchema}ESTADO') == '3':
            digital_signature.last_token = False
            _logger.error('Token is invalid.')
            return

        if status == '0':
            self.l10n_cl_dte_status_factoring = 'accepted'
        # try:
        #     self.l10n_cl_dte_status_factoring = self._analyze_sii_cesion_result(response_parsed)
        # except UnexpectedXMLResponse:
        #     # The assumption here is that the unexpected input is intermittent,
        #     # so we'll retry later. If the same input appears regularly, it should
        #     # be handled properly in _analyze_sii_result.
        #     _logger.error("Unexpected XML response:\n{}".format(response))
        #     return

        # if self.l10n_cl_dte_status in ['accepted', 'objected']:
        #     self.l10n_cl_dte_partner_status = 'not_sent'
        #     if send_dte_to_partner:
        #         self._l10n_cl_send_dte_to_partner()
        else:
            self.message_post(
                body=_('Asking for DTE status with response:') +
                     '<br /><li><b>ESTADO</b>: %s</li><li><b>ERR_CODE</b>: %s</li><li><b>NUM_ATENCION</b>: %s</li>' % (
                         response_parsed.findtext('{http://www.sii.cl/XMLSchema}RESP_HDR/ESTADO'),
                         response_parsed.findtext('{http://www.sii.cl/XMLSchema}RESP_HDR/ERR_CODE'),
                         response_parsed.findtext('{http://www.sii.cl/XMLSchema}RESP_HDR/NUM_ATENCION')))