# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
import logging

_logger = logging.getLogger(__name__)

class AccountMove(models.Model):
    _inherit = "account.move"

    scheduled_date = fields.Date('Fecha Pautada')
    mass_invoice = fields.Boolean('Factura Masiva')
    pre_valid = fields.Boolean('Preliquidacion validada')
    pre_liquid = fields.Boolean('Preliquidacion')
    uf_rate = fields.Float('Tasa UF', digits=(16, 2), default=lambda self: self._get_uf())
    order_ids = fields.Many2many("sale.order", string='Orders', compute="_get_orders", readonly=True, copy=False)
    order_count = fields.Integer(string='Sale Order Count', compute='_get_orders')
    queue_id = fields.Many2one('invoice.generation.queue', 'Cola de Factura')

    def _get_uf(self):
        uf = self.env['res.currency'].search([('name', '=', 'UF')])
        rate = 1 / float(uf.rate)
        return rate

    def cron_invoice_public(self):
        # search for invoices of the day to be published
        _logger.info("Cron de publicacion de facturas")
        today_date = fields.Datetime.now()
        invoices = self.env['account.move'].search([('scheduled_date', '=', today_date),
                                                    ('move_type', '=', 'out_invoice'),
                                                    ('mass_invoice', '=', True),
                                                    ('pre_valid', '=', False)])
        if invoices:
            for inv in invoices:
                inv.action_post()
        return True

    #@api.depends('state')
    def _get_orders(self):
        SaleOrder = self.env['sale.order']
        for inv in self:
            sale_ids = SaleOrder.search([('state', '=', 'sale')]).filtered(lambda s: inv.id in s.invoice_ids.ids)
            inv.order_ids = sale_ids
            inv.order_count = len(sale_ids)

    def action_view_order(self):
        orders = self.mapped('order_ids')
        action = self.env.ref('sale_renting.rental_order_today_return_action').read()[0]
        action['domain'] = [('id', 'in', orders.ids)]
        action['context'] = False
        form_view = [(self.env.ref('sale_renting.rental_order_view_tree').id, 'tree')]
        action['views'] = form_view
        return action
