from odoo import fields, api, models, _
import base64
import logging
from html import unescape
from lxml import etree
import json
from odoo.tools.float_utils import float_repr, float_round

_logger = logging.getLogger(__name__)

# RESP_SII_BOLETA = {
#     'EPR': 'Aceptado con Reparo'
# }

class AccountMove(models.Model):
    _inherit = 'account.move'

    l10n_cl_sii_send_ident = fields.Text(string='SII Send Identification(Track ID)', readonly=False, copy=False, tracking=True)

#     def _l10n_cl_create_dte(self):
#         if self.l10n_latam_document_type_id.code == '39':
#             folio = int(self.l10n_latam_document_number)
#             doc_id_number = 'F{}T{}'.format(folio, self.l10n_latam_document_type_id.code)
#             dte_barcode_xml = self._l10n_cl_get_dte_barcode_xml()
#             self.l10n_cl_sii_barcode = dte_barcode_xml['barcode']
#             dte = self.env.ref('l10n_cl_fixed.dte_template_boleta')._render({
#                 'move': self,
#                 'format_vat': self._l10n_cl_format_vat,
#                 'get_cl_current_strftime': self._get_cl_current_strftime,
#                 'format_length': self._format_length,
#                 'float_repr': float_repr,
#                 'doc_id': doc_id_number,
#                 'caf': self.l10n_latam_document_type_id._get_caf_file(self.company_id.id, int(self.l10n_latam_document_number)),
#                 'amounts': self._l10n_cl_get_amounts_boleta(),
#                 'withholdings': self._l10n_cl_get_withholdings(),
#                 'dte': dte_barcode_xml['ted'],
#             })
#             dte = unescape(dte.decode('utf-8')).replace(r'&', '&amp;')
#             digital_signature = self.company_id._get_digital_signature(user_id=self.env.user.id)
#             signed_dte = self._sign_full_xml(
#                 dte, digital_signature, doc_id_number, 'doc', self.l10n_latam_document_type_id._is_doc_type_voucher())
#             dte_attachment = self.env['ir.attachment'].create({
#                 'name': 'DTE_{}.xml'.format(self.name),
#                 'res_model': self._name,
#                 'res_id': self.id,
#                 'type': 'binary',
#                 'datas': base64.b64encode(signed_dte.encode('ISO-8859-1'))
#             })
#             self.l10n_cl_dte_file = dte_attachment.id
#         else:
#             return super(AccountMove, self)._l10n_cl_create_dte()
#
#     def _process_resp_boleta_status_send(self, resp):
#         if resp['estado'] == 'RSC':
#             return 'rejected'
#         else:
#             stats = resp['estadistica']
#             if stats:
#                 if stats[0]['aceptados'] == 1:
#                     return 'accepted'
#                 if stats[0]['rechazados'] == 1:
#                     return 'rejected'
#                 if stats[0]['reparos'] == 1:
#                     return 'objected'
#
#
#     def l10n_cl_verify_boleta_status(self, send_dte_to_partner=True):
#         digital_signature = self.company_id._get_digital_signature(user_id=self.env.user.id)
#         response = self._get_status_sended_boleta(
#             self.company_id.l10n_cl_dte_service_provider,
#             self._l10n_cl_format_vat(self.company_id.vat),
#             self.l10n_cl_sii_send_ident,
#             digital_signature)
#         if not response:
#             self.l10n_cl_dte_status = 'ask_for_status'
#             digital_signature.last_token = False
#             return None
#         if response.status_code == 200:
#             response_parsed = json.loads(response.content)
#             _logger.info(response_parsed)
#             self.l10n_cl_dte_status = self._process_resp_boleta_status_send(response_parsed)
#             if self.l10n_cl_dte_status in ['rejected', 'objected']:
#                 det_rep_rech = response_parsed['detalle_rep_rech'][0]
#                 error = det_rep_rech['error'][0]
#                 msg = 'Consultando status de la Boleta:'
#                 msg += '<br /><li><b>ESTADO</b>: %s</li><li><b>GLOSA</b>: %s</li><li><b>DESCRIPCION</b>: %s</li><li><b>DETALLE</b>: %s</li>' % (det_rep_rech['estado'], det_rep_rech['descripcion'], error['descripcion'], error['detalle'])
#                 self.message_post(body=msg)
#             # if self.l10n_cl_dte_status in ['accepted']:
#             #     msg = 'Consultando status de la Boleta:'
#             #     msg += '<br /><li><b>ESTADO</b>: %s</li>' % (response_parsed['estado'])
#
#     def l10n_cl_verify_boleta_info(self, send_dte_to_partner=True):
#         digital_signature = self.company_id._get_digital_signature(user_id=self.env.user.id)
#         response = self._get_info_boleta(
#             self,
#             self.company_id.l10n_cl_dte_service_provider,
#             self._l10n_cl_format_vat(self.company_id.vat),
#             self.l10n_cl_sii_send_ident,
#             digital_signature)
#         if not response:
#             self.l10n_cl_dte_status = 'ask_for_status'
#             digital_signature.last_token = False
#             return None
#         if response.status_code == 200:
#             response_parsed = json.loads(response.content)
#             self.l10n_cl_dte_status = self._process_resp_boleta_status_send(response_parsed)
#             if self.l10n_cl_dte_status in ['rejected', 'objected']:
#                 det_rep_rech = response_parsed['detalle_rep_rech'][0]
#                 error = det_rep_rech['error'][0]
#                 msg = 'Consultando status de la Boleta:'
#                 msg += '<br /><li><b>ESTADO</b>: %s</li><li><b>DESCRIPCION</b>: %s</li><li><b>DETALLE</b>: %s</li>' % (det_rep_rech['estado'], det_rep_rech['descripcion'], error['descripcion'])
#                 self.message_post(body=msg)
#
#     def l10n_cl_verify_sended_boleta_status(self):
#         digital_signature = self.company_id._get_digital_signature(user_id=self.env.user.id)
#
#
#     def l10n_cl_send_boleta_to_sii(self, retry_send=True):
#         """
#         Send the TICKET to the SII. It will be
#         """
#         digital_signature = self.company_id._get_digital_signature(user_id=self.env.user.id)
#         codigo = 'FAU'
#         # Verificamos si ya este documento fue enviado
#         sended = self._get_verify_sended_boleta(
#             self.company_id.l10n_cl_dte_service_provider,
#             self._l10n_cl_format_vat(self.company_id.vat),
#             self,
#             digital_signature)
#         # if sended.status_code == 200:
#         #     resp = json.loads(sended.text)
#         #     codigo = resp['codigo']
#         if codigo == 'FAU':
#             # Enviamos el documento si no se ha enviado al SII
#             response = self._send_xml_boleta_to_sii(
#                 self.company_id.l10n_cl_dte_service_provider,
#                 self.company_id.website,
#                 self.company_id.vat,
#                 self.l10n_cl_sii_send_file.name,
#                 base64.b64decode(self.l10n_cl_sii_send_file.datas),
#                 digital_signature
#             )
#             if not response:
#                 return None
#             if response.status_code == 200:
#                 response_parsed = json.loads(response.text)
#                 _logger.info("========================Respuesta de envio========================")
#                 _logger.info(response.text)
#                 self.l10n_cl_sii_send_ident = response_parsed['trackid']
#                 self.l10n_cl_dte_status = 'ask_for_status'
#                 _logger.info('XML enviado con exito al SII con el numero de Identificacion: %s' % response_parsed['trackid'])
#                 self.message_post(body='XML enviado con exito al SII con el numero de Identificacion: %s' % response_parsed['trackid'])
#             if response.status_code == 405:
#                 ticket_exist = response.decode('utf-8')
#                 message = ticket_exist[-11].split('\n')
#                 _logger.warning(message)
#                 self.message_post(body=message)
#                 self.l10n_cl_dte_status = 'ask_for_status'
#
#     def _l10n_cl_get_amounts_boleta(self):
#         """
#         This method is used to calculate the amount and taxes required in the Chilean localization electronic documents.
#         """
#         self.ensure_one()
#         vat_taxes = self.line_ids.filtered(lambda x: x.tax_line_id.l10n_cl_sii_code == 14)
#         lines_with_taxes = self.invoice_line_ids.filtered(lambda x: x.tax_ids)
#         lines_without_taxes = self.invoice_line_ids.filtered(lambda x: not x.tax_ids)
#         values = {
#             'vat_amount': self.currency_id.round(sum(vat_taxes.mapped('price_subtotal'))),
#             # Sum of the subtotal amount affected by tax
#             'subtotal_amount_taxable': sum(lines_with_taxes.mapped('price_subtotal')) if (
#                     lines_with_taxes and self.l10n_latam_document_type_id._is_doc_type_voucher()) else False,
#             # Sum of the subtotal amount not affected by tax
#             'subtotal_amount_exempt': sum(lines_without_taxes.mapped('price_subtotal')) if lines_without_taxes else False,
#             'vat_percent': (
#                 '%.2f' % (vat_taxes[0].tax_line_id.mapped('amount')[0])
#                 if vat_taxes and not self.l10n_latam_document_type_id._is_doc_type_voucher() and
#                    not self.l10n_latam_document_type_id._is_doc_type_exempt() else False
#             ),
#             'total_amount': self.currency_id.round(self.amount_total),
#         }
#         # Calculate the fields needed if the invoice has a different currency than company currency
#         if self.currency_id != self.company_id.currency_id and self.l10n_latam_document_type_id._is_doc_type_export():
#             rate = (self.currency_id + self.company_id.currency_id)._get_rates(self.company_id, self.date).get(
#                 self.currency_id.id) or 1
#             values['second_currency'] = {'rate': rate}
#
#             values['second_currency'].update({
#                 'subtotal_amount_taxable': sum(lines_with_taxes.mapped('price_subtotal')) / rate if lines_with_taxes else False,
#                 'subtotal_amount_exempt': sum(lines_without_taxes.mapped('price_subtotal')) / rate if lines_without_taxes else False,
#                 'vat_amount': sum(lines_with_taxes.mapped('price_subtotal')) / rate if lines_with_taxes else False,
#                 'total_amount': self.amount_total / rate
#             })
#         return values
#
#     def _l10n_cl_ask_dte_status(self):
#         for move in self.search([('l10n_cl_dte_status', '=', 'ask_for_status')]):
#             if move.l10n_latam_document_type_id_code == '39':
#                 move.l10n_cl_verify_boleta_status(send_dte_to_partner=False)
#                 self.env.cr.commit()
#             else:
#                 move.l10n_cl_verify_dte_status(send_dte_to_partner=False)
#                 self.env.cr.commit()
#
#     def _l10n_cl_send_dte_to_partner_multi(self):
#         for move in self.search([('l10n_cl_dte_status', '=', 'accepted'),
#                                  ('l10n_cl_dte_partner_status', '=', 'not_sent'),
#                                  ('partner_id.country_id.code', '=', "CL")]):
#             if move.l10n_latam_document_type_id_code != '39':
#                 _logger.debug('Sending %s DTE to partner' % move.name)
#                 if move.partner_id._l10n_cl_is_foreign():
#                     # review this option: if in the email will the pdf be included, the email should be sent
#                     # to foreign partners also
#                     continue
#                 move._l10n_cl_send_dte_to_partner()
#                 self.env.cr.commit()
#
#     def _l10n_cl_ask_claim_status(self):
#         for move in self.search([('l10n_cl_dte_acceptation_status', 'in', ['accepted', 'claimed']),
#                                  ('move_type', 'in', ['out_invoice', 'out_refund']),
#                                  ('l10n_cl_claim', '=', False)]):
#             if move.l10n_latam_document_type_id_code != '39':
#                 if move.company_id.l10n_cl_dte_service_provider == 'SIITEST':
#                     continue
#                 move.l10n_cl_verify_claim_status()
#                 self.env.cr.commit()
#
#     def cron_send_dte_to_sii(self):
#         for record in self.search([('l10n_cl_dte_status', '=', 'not_sent')]):
#             if record.l10n_latam_document_type_id_code == '39':
#                 record.with_context(cron_skip_connection_errs=True).l10n_cl_send_boleta_to_sii()
#                 self.env.cr.commit()
#             else:
#                 record.with_context(cron_skip_connection_errs=True).l10n_cl_send_dte_to_sii()
#                 self.env.cr.commit()
#
# class AccountMoveLine(models.Model):
#     _inherit = 'account.move.line'
#
#     def _l10n_cl_get_line_amounts_boletas(self):
#         """
#         This method is used to calculate the amount and taxes of the lines required in the Chilean localization
#         electronic documents.
#         """
#         values = {
#             'price_item': float(self.price_total / self.quantity) if self.move_id.l10n_latam_document_type_id._is_doc_type_voucher() else self.price_unit,
#             'total_discount': '{:.0f}'.format(self.price_unit * self.quantity * self.discount / 100.0),
#         }
#         if self.move_id.currency_id != self.move_id.company_id.currency_id:
#             rate = (self.move_id.currency_id + self.move_id.company_id.currency_id)._get_rates(
#                 self.move_id.company_id, self.move_id.date).get(self.move_id.currency_id.id) or 1
#             second_currency_values = {
#                 'price': self.price_unit if not self.move_id.l10n_latam_document_type_id._is_doc_type_export(
#                     ) else '{:.4f}'.format(self.price_unit / rate),
#                 'conversion_rate': '{:.4f}'.format((self.currency_id + self.company_id.currency_id)._get_rates(
#                     self.company_id, self.move_id.date).get(
#                     self.currency_id.id)) if self.move_id.l10n_latam_document_type_id._is_doc_type_export(
#                         ) else False,
#                 'total_amount': '{:.4f}'.format(
#                     self.price_subtotal / rate) if self.move_id.l10n_latam_document_type_id._is_doc_type_export(
#                         ) else False,
#             }
#             values.update({'second_currency': second_currency_values})
#         return values

    