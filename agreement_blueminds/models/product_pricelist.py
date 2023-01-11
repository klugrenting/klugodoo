# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools, _
from odoo.exceptions import UserError

class Pricelist(models.Model):
    _inherit = "product.pricelist"

    def name_get(self):
        return [(pricelist.id, '%s' % (pricelist.name)) for pricelist in self]

    vigente = fields.Selection([('V', 'Vigente'), ('NV', 'No Vigente')], string='Validity', default='V')
    pricelist_type = fields.Selection([('C', 'Contrato'),('E', 'Ecomerce')], string='Rate Type', default='C')

    @api.onchange("pricelist_type")
    def _onchange_pricelist_type(self):
        if self.pricelist_type:
            if self.pricelist_type == 'C':
                for line in self.item_ids:
                    line.pricelist_type = 'C'
            if self.pricelist_type == 'E':
                for line in self.item_ids:
                    line.pricelist_type = 'E'


class PricelistItem(models.Model):
    _inherit = "product.pricelist.item"

    payment_method_p = fields.Many2many('agreement.payment.method', 'method_pricelist_rel', 'method_id',
                                             'pricelist_id',
                                             string='Payment method', domain=[("id", "in", ['1','2','3','4'])])
    payment_period_p = fields.Many2many('agreement.payment.period', 'period_pricelist_rel', 'period_id',
                                             'pricelist_id',
                                             string='Payment Frequency', domain=[("id", "in", ['1','2','3','4','5','6'])])
    zone = fields.Many2many('zona.comercial', 'zona_pricelist_rell', 'zona_id',
                                             'pricelist_id', string='Shopping area', track_visibility='onchange')
    comuna_id = fields.Many2many('comuna.comercial', 'comuna_pricelist_rel', 'comuna_id',
                                             'pricelist_id', string='Commune', track_visibility='onchange')
    pricelist_type = fields.Selection(related='pricelist_id.pricelist_type', string='Rate Type')
    type_partner = fields.Many2many('agreement.type.partner', 'type_partner_rel', 'type_id',
                            'pricelist_id', string='Type of contract', track_visibility='onchange', help="Type of client (household, company, HORECA - INTERNAL, HORECA - SELF-BOTTLING)")
    currency_id_m = fields.Many2one("res.currency", string="currency")
    vigente = fields.Selection(related='pricelist_id.vigente', string='Validity')

    @api.onchange('date_start')
    def _onchange_date_start(self):
        if self.date_start and self.date_end:
            if self.date_start > self.date_end:
                raise UserError("The start date cannot be greater than the end date")

    @api.onchange('date_end')
    def _onchange_date_end(self):
        if self.date_start and self.date_end:
            if self.date_end < self.date_start:
                raise UserError("The end date cannot be less than the start date.")
