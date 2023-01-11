# -*- coding: utf-8 -*-

from odoo import api, fields, models
from datetime import date, datetime, timedelta
from odoo.exceptions import UserError, ValidationError
from logging import getLogger

_logger = getLogger(__name__)


class InvoiceGen(models.TransientModel):
    _name = 'invoice.gen'
    _description = u'Generación de Facturas'

    def default_date_scheduled(self):
        date_scheduled = date.today() + timedelta(days=1)
        return date_scheduled

    def default_currency_rates(self):
        currency = self.env['res.currency'].search([('active', '=', True)]).ids
        return currency

    date_from = fields.Date('Fecha desde')
    date_to = fields.Date('Fecha hasta')
    type_gen = fields.Selection(selection=[
        ('integral', 'Integral Cliente'),
        ('contrato', 'Separada por Contrato')], string='Tipo de Generación', required=False)
    partner_id = fields.Many2one('res.partner', 'Cliente', domain=[])
    uf_rate = fields.Float('Tasa UF', digits=(16, 2), default=lambda self: self._get_uf())
    currency_rate_ids = fields.One2many('invoice.gen.currency', 'invoice_gen_id', string='Tasas')
    scheduled_date = fields.Date('Fecha Pautada', default=default_date_scheduled)
    not_date = fields.Boolean()

    def _get_uf(self):
        uf = self.env['res.currency'].search([('name', '=', 'UF')])
        rate_date = uf.rate_ids.filtered(lambda s: s.name == self.scheduled_date)
        return rate_date.inverse_company_rate

    @api.onchange('scheduled_date')
    def onchange_scheduled_date(self):
        if self.scheduled_date:
            currencies = self.env['res.currency'].search([('active', '=', True), ('name', '!=', self.env.company.currency_id.name)])
            if currencies:
                if not self.currency_rate_ids:
                    for currency in currencies:
                        vals = {
                            'invoice_gen_id': self.id,
                            'currency_id': currency.id,
                            'rate': currency.rate_ids.filtered(lambda s: s.name == self.scheduled_date).inverse_company_rate
                        }
                        self.env['invoice.gen.currency'].create(vals)
                else:
                    for curr_rate in self.currency_rate_ids:
                        curr_rate.rate = curr_rate.currency_id.rate_ids.filtered(lambda s: s.name == self.scheduled_date).inverse_company_rate
            if self.scheduled_date <= date.today():
                self.not_date = True
            else:
                self.not_date = False
                self.uf_rate = self._get_uf()

    def generate_invoices(self):
        currencies = []
        selected_currencies = self.currency_rate_ids.mapped('currency_id')
        for currency in selected_currencies:
            currencies.append(currency.id)
        currencies.append(self.env.company.currency_id.id)
        if self.not_date:
            raise ValidationError('La fecha pautada debe ser estrictamente mayor a la fecha de hoy')
        elif self.currency_rate_ids.filtered(lambda r: r.rate == 0.0):
            raise ValidationError('Las tasas no pueden ser cero (0)')
        else:
            s_default = [
                ('state', '=', 'sale'),
                ('invoice_status', '=', 'to invoice'),
                ('agreement_currency_id', 'in', currencies)
            ]
            if self.partner_id:
                s_default.append(('partner_id', '=', self.partner_id.id))
            order_ids = self.env['sale.order'].search(s_default, order='partner_id').filtered(lambda s: s.fecha_fact_prog >= self.date_from and s.fecha_fact_prog <= self.date_to)
            type_gen = ['integral', 'contrato']
            queue_ids = []
            InvoiceGenQueueCurrency = self.env['invoice.generation.queue.currency']
            for tg in type_gen:
                try:
                    orders = order_ids.filtered(lambda s: s.partner_id.fact_integral == tg)
                    for order in orders:
                        rate = self.currency_rate_ids.filtered(lambda r: r.currency_id.id == order.agreement_currency_id.id).rate
                        vals = {
                            'scheduled_date': self.scheduled_date,
                            'mass_invoice': True,
                            'uf_rate': rate
                        }
                        order.write(vals)
                    if orders:
                        vals_queue = {
                            'name': 'Cola de creacion de facturas desde %s hasta %s' % (self.date_from, self.date_to),
                            'date': date.today(),
                            'type_gen': tg,
                            'rental_ids': orders.ids,
                        }
                        queue_id = self.env['invoice.generation.queue'].create(vals_queue)
                        for rate in self.currency_rate_ids:
                            vals_rate = {
                                'queue_id': queue_id.id,
                                'currency_id': rate.currency_id.id,
                                'rate': rate.rate
                            }
                            InvoiceGenQueueCurrency.create(vals_rate)
                        queue_ids.append(queue_id.id)
                except:
                    raise ValidationError('No se encontraron registros coincidentes')
            if queue_ids:
                action = self.env["ir.actions.actions"]._for_xml_id("invoice_generation.invoice_generation_queue_action")
                if len(queue_ids) > 1:
                    action['domain'] = [('id', 'in', queue_ids)]
                elif len(queue_ids) == 1:
                    form_view = [(self.env.ref('invoice_generation.invoice_generation_queue_view_form').id, 'form')]
                    if 'views' in action:
                        action['views'] = form_view + [(state, view) for state, view in action['views'] if view != 'form']
                    else:
                        action['views'] = form_view
                    action['res_id'] = queue_ids[0]
                else:
                    action = {'type': 'ir.actions.act_window_close'}
                return action

class InvoiceGen(models.TransientModel):
    _name = 'invoice.gen.currency'
    _description = u'Generacion Facturas Tasas'

    invoice_gen_id = fields.Many2one('invoice.gen')
    currency_id = fields.Many2one('res.currency', string='Moneda')
    date = fields.Date(related='invoice_gen_id.scheduled_date', store=True)
    rate = fields.Float(string='Tasa')

    @api.onchange('date')
    def onchange_date_get_rate(self):
        if self.date:
            rate_date = self.currency_id.rate_ids.filtered(lambda s: s.name == self.date)
            self.rate = rate_date.inverse_company_rate