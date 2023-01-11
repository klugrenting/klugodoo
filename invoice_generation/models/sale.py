# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
from functools import partial
from itertools import groupby
from datetime import date
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.misc import formatLang, get_lang
from odoo.osv import expression
from odoo.tools import float_is_zero, float_compare


class SaleOrder(models.Model):
    _inherit = "sale.order"

    scheduled_date = fields.Date('Fecha Pautada')
    mass_invoice = fields.Boolean('Factura Masiva')
    uf_rate = fields.Float('Tasa', digits=(16, 2)) #, default=lambda self: self._get_uf()
    invoice_id = fields.Many2one('account.move', string='Invoice')#, compute='_get_invoiced', readonly=True)
    queue_id = fields.Many2one('invoice.generation.queue', 'Cola')


    # def group_invoice_contract_annex(self, invoices):
    #     inv_grouped = []
    #     exist = False
    #     for inv in invoices:
    #         agreement = self.env['agreement'].search([('id', '=', inv['agreement_id'])])
    #         if inv_grouped:
    #             for ig in inv_grouped:
    #                 ig_agreement = self.env['agreement'].search([('id', '=', ig['agreement_id'])])
    #                 if not agreement.parent_agreement_id and not ig_agreement.parent_agreement_id:
    #                     exist = False
    #                 elif agreement.parent_agreement_id and not ig_agreement.parent_agreement_id:
    #                     if agreement.parent_agreement_id.id == ig_agreement.id:
    #                         for line in inv['invoice_line_ids']:
    #                             ig['invoice_line_ids'].append(line)
    #                         exist = True
    #                         break
    #                 elif not agreement.parent_agreement_id and ig_agreement.parent_agreement_id:
    #                     if agreement.id == ig_agreement.parent_agreement_id.id:
    #                         for line in inv['invoice_line_ids']:
    #                             ig['invoice_line_ids'].append(line)
    #                         exist = True
    #                         break
    #                 else:
    #                     exist = False
    #             if not exist:
    #                 inv_grouped.append(inv)
    #         else:
    #             inv_grouped.append(inv)
    #     return inv_grouped
    #
    # def group_line_invoices(self, lines):
    #     lines_grouped = []
    #     exist = False
    #     for line in lines:
    #         if lines_grouped:
    #             for lg in lines_grouped:
    #                 if line['product_id'] == lg['product_id'] and line['price_unit'] == lg['price_unit']:
    #                     quantity = float(float(lg['quantity']) + float(line['quantity']))
    #                     lg['quantity'] = quantity
    #                     lg['sale_line_ids'].append(line['sale_line_ids'][0])
    #                     exist = True
    #                     break
    #                 else:
    #                     exist = False
    #             if not exist:
    #                 lines_grouped.append(line)
    #
    #         else:
    #             lines_grouped.append(line)
    #     return lines_grouped
    #
    # def _create_invoices(self, grouped=False, final=False, date=None):
    #     group_line_invoices = ['product_id', 'price_unit']
    #     """
    #     Create the invoice associated to the SO.
    #     :param grouped: if True, invoices are grouped by SO id. If False, invoices are grouped by
    #                     (partner_invoice_id, currency)
    #     :param final: if True, refunds will be generated if necessary
    #     :returns: list of created invoices
    #     """
    #     if not self.env['account.move'].check_access_rights('create', False):
    #         try:
    #             self.check_access_rights('write')
    #             self.check_access_rule('write')
    #         except AccessError:
    #             return self.env['account.move']
    #
    #     # 1) Create invoices.
    #     invoice_vals_list = []
    #     invoice_item_sequence = 0 # Incremental sequencing to keep the lines order on the invoice.
    #     for order in self:
    #         order = order.with_company(order.company_id)
    #         current_section_vals = None
    #         down_payments = order.env['sale.order.line']
    #
    #         invoice_vals = order._prepare_invoice()
    #         invoiceable_lines = order._get_invoiceable_lines(final)
    #
    #         if not any(not line.display_type for line in invoiceable_lines):
    #             continue
    #
    #         invoice_line_vals = []
    #         down_payment_section_added = False
    #         for line in invoiceable_lines:
    #             if not down_payment_section_added and line.is_downpayment:
    #                 # Create a dedicated section for the down payments
    #                 # (put at the end of the invoiceable_lines)
    #                 invoice_line_vals.append(
    #                     (0, 0, order._prepare_down_payment_section_line(
    #                         sequence=invoice_item_sequence,
    #                     )),
    #                 )
    #                 down_payment_section_added = True
    #                 invoice_item_sequence += 1
    #             invoice_line_vals.append(
    #                 (0, 0, line._prepare_invoice_line(sequence=invoice_item_sequence,
    #                 )),
    #             )
    #             invoice_item_sequence += 1
    #
    #         invoice_vals['invoice_line_ids'] += invoice_line_vals
    #         invoice_vals_list.append(invoice_vals)
    #
    #     if not invoice_vals_list:
    #         raise self._nothing_to_invoice_error()
    #
    #     # 2) Manage 'grouped' parameter: group by (partner_id, currency_id).
    #     if not grouped:
    #         new_invoice_vals_list = []
    #         invoice_grouping_keys = self._get_invoice_grouping_keys()
    #         invoice_vals_list = sorted(invoice_vals_list, key=lambda x: [x.get(grouping_key) for grouping_key in invoice_grouping_keys])
    #         for grouping_keys, invoices in groupby(invoice_vals_list, key=lambda x: [x.get(grouping_key) for grouping_key in invoice_grouping_keys]):
    #             origins = set()
    #             payment_refs = set()
    #             refs = set()
    #             ref_invoice_vals = None
    #             for invoice_vals in invoices:
    #                 if not ref_invoice_vals:
    #                     ref_invoice_vals = invoice_vals
    #                 else:
    #                     ref_invoice_vals['invoice_line_ids'] += invoice_vals['invoice_line_ids']
    #                 origins.add(invoice_vals['invoice_origin'])
    #                 payment_refs.add(invoice_vals['payment_reference'])
    #                 refs.add(invoice_vals['ref'])
    #             ref_invoice_vals.update({
    #                 'ref': ', '.join(refs)[:2000],
    #                 'invoice_origin': ', '.join(origins),
    #                 'payment_reference': len(payment_refs) == 1 and payment_refs.pop() or False,
    #             })
    #             new_invoice_vals_list.append(ref_invoice_vals)
    #         invoice_vals_list = new_invoice_vals_list
    #
    #     # 3) Create invoices.
    #
    #     # As part of the invoice creation, we make sure the sequence of multiple SO do not interfere
    #     # in a single invoice. Example:
    #     # SO 1:
    #     # - Section A (sequence: 10)
    #     # - Product A (sequence: 11)
    #     # SO 2:
    #     # - Section B (sequence: 10)
    #     # - Product B (sequence: 11)
    #     #
    #     # If SO 1 & 2 are grouped in the same invoice, the result will be:
    #     # - Section A (sequence: 10)
    #     # - Section B (sequence: 10)
    #     # - Product A (sequence: 11)
    #     # - Product B (sequence: 11)
    #     #
    #     # Resequencing should be safe, however we resequence only if there are less invoices than
    #     # orders, meaning a grouping might have been done. This could also mean that only a part
    #     # of the selected SO are invoiceable, but resequencing in this case shouldn't be an issue.
    #     if len(invoice_vals_list) < len(self):
    #         SaleOrderLine = self.env['sale.order.line']
    #         for invoice in invoice_vals_list:
    #             sequence = 1
    #             for line in invoice['invoice_line_ids']:
    #                 line[2]['sequence'] = SaleOrderLine._get_invoice_line_sequence(new=sequence, old=line[2]['sequence'])
    #                 sequence += 1
    #     ###### Agrupar facturas si el contrato es un anexo #######
    #     if self.partner_id.fact_integral == 'contrato':
    #         invoice_vals_list = self.group_invoice_contract_annex(invoice_vals_list)
    #     ##### Agrupando lineas de facturas ######
    #     for inv in invoice_vals_list:
    #         new_invoice_line_list = []
    #         create_invoice_lines = []
    #         for line in inv['invoice_line_ids']:
    #             new_invoice_line_list.append(line[2])
    #         grouped_invoice_lines = self.group_line_invoices(new_invoice_line_list)
    #         for line in grouped_invoice_lines:
    #             create_invoice_lines.append((0, 0, line))
    #         inv['invoice_line_ids'] = create_invoice_lines
    #     # Manage the creation of invoices in sudo because a salesperson must be able to generate an invoice from a
    #     # sale order without "billing" access rights. However, he should not be able to create an invoice from scratch.
    #     moves = self.env['account.move'].sudo().with_context(default_move_type='out_invoice').create(invoice_vals_list)
    #
    #     # 4) Some moves might actually be refunds: convert them if the total amount is negative
    #     # We do this after the moves have been created since we need taxes, etc. to know if the total
    #     # is actually negative or not
    #     if final:
    #         moves.sudo().filtered(lambda m: m.amount_total < 0).action_switch_invoice_into_refund_credit_note()
    #     for move in moves:
    #         move.message_post_with_view('mail.message_origin_link',
    #             values={'self': move, 'origin': move.line_ids.mapped('sale_line_ids.order_id')},
    #             subtype_id=self.env.ref('mail.mt_note').id
    #         )
    #     return moves


    # def _create_invoices(self, grouped=False, final=False):
    #     group_line_invoices = ['product_id', 'price_unit']
    #     """
    #     Create the invoice associated to the SO.
    #     :param grouped: if True, invoices are grouped by SO id. If False, invoices are grouped by
    #                     (partner_invoice_id, currency)
    #     :param final: if True, refunds will be generated if necessary
    #     :returns: list of created invoices
    #     """
    #     if not self.env['account.move'].check_access_rights('create', False):
    #         try:
    #             self.check_access_rights('write')
    #             self.check_access_rule('write')
    #         except AccessError:
    #             return self.env['account.move']
    #
    #     precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
    #
    #     # 1) Create invoices.
    #     invoice_vals_list = []
    #     for order in self:
    #         pending_section = None
    #
    #         # Invoice values.
    #         invoice_vals = order._prepare_invoice()
    #
    #         # Invoice line values (keep only necessary sections).
    #         for line in order.order_line:
    #             if line.display_type == 'line_section':
    #                 pending_section = line
    #                 continue
    #             if line.display_type != 'line_note' and float_is_zero(line.qty_to_invoice, precision_digits=precision):
    #                 continue
    #             if line.qty_to_invoice > 0 or (line.qty_to_invoice < 0 and final) or line.display_type == 'line_note':
    #                 if pending_section:
    #                     invoice_vals['invoice_line_ids'].append((0, 0, pending_section._prepare_one_service_invoice_line()))
    #                     pending_section = None
    #                 invoice_vals['invoice_line_ids'].append((0, 0, line._prepare_one_service_invoice_line()))
    #
    #         if not invoice_vals['invoice_line_ids']:
    #             raise UserError(_(
    #                 'There is no invoiceable line. If a product has a Delivered quantities invoicing policy, please make sure that a quantity has been delivered.'))
    #
    #         invoice_vals_list.append(invoice_vals)
    #
    #     if not invoice_vals_list:
    #         raise UserError(_(
    #             'There is no invoiceable line. If a product has a Delivered quantities invoicing policy, please make sure that a quantity has been delivered.'))
    #
    #     # 2) Manage 'grouped' parameter: group by (partner_id, currency_id).
    #     if not grouped:
    #         new_invoice_vals_list = []
    #         invoice_grouping_keys = self._get_invoice_grouping_keys()
    #         for grouping_keys, invoices in groupby(invoice_vals_list, key=lambda x: [x.get(grouping_key) for grouping_key in invoice_grouping_keys]):
    #             origins = set()
    #             payment_refs = set()
    #             refs = set()
    #             ref_invoice_vals = None
    #             for invoice_vals in invoices:
    #                 if not ref_invoice_vals:
    #                     ref_invoice_vals = invoice_vals
    #                 else:
    #                     ref_invoice_vals['invoice_line_ids'] += invoice_vals['invoice_line_ids']
    #                 origins.add(invoice_vals['invoice_origin'])
    #                 payment_refs.add(invoice_vals['payment_reference'])
    #                 refs.add(invoice_vals['ref'])
    #             ref_invoice_vals.update({
    #                 'ref': ', '.join(refs)[:2000],
    #                 'invoice_origin': ', '.join(origins),
    #                 'payment_reference': len(payment_refs) == 1 and payment_refs.pop() or False,
    #             })
    #             new_invoice_vals_list.append(ref_invoice_vals)
    #         invoice_vals_list = new_invoice_vals_list
    #
    #     # 3) Create invoices.
    #
    #     # As part of the invoice creation, we make sure the sequence of multiple SO do not interfere
    #     # in a single invoice. Example:
    #     # SO 1:
    #     # - Section A (sequence: 10)
    #     # - Product A (sequence: 11)
    #     # SO 2:
    #     # - Section B (sequence: 10)
    #     # - Product B (sequence: 11)
    #     #
    #     # If SO 1 & 2 are grouped in the same invoice, the result will be:
    #     # - Section A (sequence: 10)
    #     # - Section B (sequence: 10)
    #     # - Product A (sequence: 11)
    #     # - Product B (sequence: 11)
    #     #
    #     # Resequencing should be safe, however we resequence only if there are less invoices than
    #     # orders, meaning a grouping might have been done. This could also mean that only a part
    #     # of the selected SO are invoiceable, but resequencing in this case shouldn't be an issue.
    #     if len(invoice_vals_list) < len(self):
    #         SaleOrderLine = self.env['sale.order.line']
    #         for invoice in invoice_vals_list:
    #             sequence = 1
    #             for line in invoice['invoice_line_ids']:
    #                 line[2]['sequence'] = SaleOrderLine._get_invoice_line_sequence(new=sequence,
    #                                                                                old=line[2]['sequence'])
    #                 sequence += 1
    #     ##### Agrupando lineas de facturas ######
    #     for inv in invoice_vals_list:
    #         new_invoice_line_list = []
    #         create_invoice_lines = []
    #         for line in inv['invoice_line_ids']:
    #             new_invoice_line_list.append(line[2])
    #         grouped_invoice_lines = self.group_line_invoices(new_invoice_line_list)
    #         for line in grouped_invoice_lines:
    #             create_invoice_lines.append((0, 0, line))
    #         inv['invoice_line_ids'] = create_invoice_lines
    #     # Manage the creation of invoices in sudo because a salesperson must be able to generate an invoice from a
    #     # sale order without "billing" access rights. However, he should not be able to create an invoice from scratch.
    #
    #         moves = self.env['account.move'].create(inv) # .sudo().with_context(default_type='out_invoice')
    #
    #         # 4) Some moves might actually be refunds: convert them if the total amount is negative
    #         # We do this after the moves have been created since we need taxes, etc. to know if the total
    #         # is actually negative or not
    #         if final:
    #             moves.sudo().filtered(lambda m: m.amount_total < 0).action_switch_invoice_into_refund_credit_note()
    #         for move in moves:
    #             move.message_post_with_view('mail.message_origin_link',
    #                                         values={'self': move, 'origin': move.line_ids.mapped('sale_line_ids.order_id')},
    #                                         subtype_id=self.env.ref('mail.mt_note').id
    #                                         )
    #     return moves

    def _get_uf(self):
        uf = self.env['res.currency'].search([('name', '=', 'UF')])
        rate = 1 / float(uf.rate)
        return rate

    def _prepare_invoice(self):
        today = date.today()
        res = super(SaleOrder, self)._prepare_invoice()
        if self.currency_id.name == 'UF':
            clp = self.env['res.currency'].search([('name', '=', 'CLP')])
            res['currency_id'] = clp.id
        res['agreement_id'] = self.agreement_id.id if self.agreement_id else False
        # res['payment_period'] = self.payment_period.id
        # res['payment_method'] = self.payment_method.id
        # res['method_payment_id'] = self.agreement_id.card_number.id if self.agreement_id else False
        # res['intermediary_id'] = self.agreement_id.card_number.type_subscription_new.id if self.agreement_id else False
        res['scheduled_date'] = self.scheduled_date
        res['invoice_date'] = self.scheduled_date
        res['mass_invoice'] = self.mass_invoice
        res['uf_rate'] = self.uf_rate
        # if self.reference_ids:
        #     res['l10n_cl_reference_ids'] = self.reference_ids
        # if self.reference_ids.date_init <= today and self.reference_ids.date_end >= today:
        #     raise UserError(_('La referencia esta vencida'))
        return res

    def _get_invoice_grouping_keys(self):
        res = super(SaleOrder, self)._get_invoice_grouping_keys()
        type_gen = self.env.context.get('type_gen')
        if type_gen:
            group_by = {
                'contrato': ['agreement_id', 'company_id', 'partner_id', 'payment_period', 'payment_method', 'agreement_currency_id'],
                'integral': ['company_id', 'partner_id', 'payment_period', 'payment_method', 'agreement_currency_id']}
            return group_by[type_gen]
        else:
            return res

    # @api.depends('order_line.invoice_lines')
    # def _get_invoiced(self):
    #     # The invoice_ids are obtained thanks to the invoice lines of the SO
    #     # lines, and we also search for possible refunds created directly from
    #     # existing invoices. This is necessary since such a refund is not
    #     # directly linked to the SO.
    #     for order in self:
    #         invoices = order.order_line.invoice_lines.move_id.filtered(lambda r: r.type in ('out_invoice', 'out_refund'))
    #         order.invoice_ids = invoices
    #         order.invoice_count = len(invoices)
    #         order.invoice_id = invoices[0] if invoices else False


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _prepare_invoice_line(self, **optional_values):
        res = super(SaleOrderLine, self)._prepare_invoice_line()
        # contract = self.order_id.agreement_id.name + ';'
        # date_range = 'desde el ' + datetime.strftime(self.order_id.agreement_id.start_date, '%d-%m-%Y') + ' hasta el ' + datetime.strftime(self.order_id.agreement_id.end_date, '%d-%m-%Y')
        # #center_cost = self.order_id.cost_center_id if self.order_id.cost_center_id else ''
        # name = contract.split('-')[0] + res['name'].upper() + ';\n' + center_cost + ' ' + date_range
        # res['name'] = name
        if self.order_id.agreement_currency_id.id != self.env.company.currency_id.id:
            res['price_unit'] = res['price_unit'] / (1 / self.order_id.uf_rate if self.order_id.uf_rate > 0 else 1)

        # if self.cost_center_id:
        #     res['cost_center_id'] = self.cost_center_id.id
        return res

    @api.depends('state', 'product_uom_qty', 'qty_delivered', 'qty_to_invoice', 'qty_invoiced')
    def _compute_invoice_status(self):
        """
        Compute the invoice status of a SO line. Possible statuses:
        - no: if the SO is not in status 'sale' or 'done', we consider that there is nothing to
          invoice. This is also hte default value if the conditions of no other status is met.
        - to invoice: we refer to the quantity to invoice of the line. Refer to method
          `_get_to_invoice_qty()` for more information on how this quantity is calculated.
        - upselling: this is possible only for a product invoiced on ordered quantities for which
          we delivered more than expected. The could arise if, for example, a project took more
          time than expected but we decided not to invoice the extra cost to the client. This
          occurs onyl in state 'sale', so that when a SO is set to done, the upselling opportunity
          is removed from the list.
        - invoiced: the quantity invoiced is larger or equal to the quantity ordered.
        """
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        for line in self:
            if line.state not in ('sale', 'done'):
                line.invoice_status = 'no'
            elif line.is_downpayment and line.untaxed_amount_to_invoice == 0:
                line.invoice_status = 'invoiced'
            elif float_compare(line.qty_invoiced, line.product_uom_qty, precision_digits=precision) < 0:
                line.invoice_status = 'to invoice'
            elif line.state == 'sale' and line.product_id.invoice_policy == 'order' and \
                    float_compare(line.qty_delivered, line.product_uom_qty, precision_digits=precision) == 1:
                line.invoice_status = 'upselling'
            elif float_compare(line.qty_invoiced, line.product_uom_qty, precision_digits=precision) >= 0:
                line.invoice_status = 'invoiced'
            else:
                line.invoice_status = 'no'

    # def _prepare_one_service_invoice_line(self):
    #     res = super(SaleOrderLine, self)._prepare_one_service_invoice_line()
    #     if self.currency_id.name == 'UF':
    #         # try:
    #         res['price_unit'] = res['price_unit'] / (1 / self.order_id.uf_rate if self.order_id.uf_rate > 0 else 1)
    #         # except ZeroDivisionError:
    #         #     res['price_unit'] = 0
    #     return res

    # def _prepare_one_service_invoice_line(self, **optional_values):
    #     """
    #     Prepare the dict of values to create the new invoice line for a sales order line.
    #     :param qty: float quantity to invoice
    #     :param optional_values: any parameter that should be added to the returned invoice line
    #     """
    #     self.ensure_one()
    #     res = {
    #         'display_type': self.display_type,
    #         'sequence': self.sequence,
    #         'name': self.name, # str(self.name) + ' De contrato: ' + str(self.order_id.agreement_id.name)
    #         'product_id': self.product_id.id,
    #         'product_uom_id': self.product_uom.id,
    #         'quantity': self.qty_to_invoice,
    #         'discount': self.discount,
    #         'price_unit': self.price_unit,
    #         'tax_ids': [(6, 0, self.tax_id.ids)],
    #         'analytic_account_id': self.order_id.analytic_account_id.id,
    #         'analytic_tag_ids': [(6, 0, self.analytic_tag_ids.ids)],
    #         'sale_line_ids': [(4, self.id)],
    #     }
    #     if optional_values:
    #         res.update(optional_values)
    #     if self.display_type:
    #         res['account_id'] = False
    #     return res

    # def _get_uf(self):
    #     uf = self.env['res.currency'].search([('name', '=', 'UF')])
    #     rate = 1 / float(uf.rate)
    #     return rate