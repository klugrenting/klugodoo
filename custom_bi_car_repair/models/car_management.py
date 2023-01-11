# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

import time
from datetime import datetime
from datetime import date, datetime
from odoo.exceptions import Warning, UserError
from odoo import models, fields, exceptions, api, SUPERUSER_ID, _


class InhAccountMove(models.Model):
    _inherit = 'account.move'

    diagnose_id = fields.Many2one('car.diagnosys', string='Car Diagnosis')


class InhCarDiagnosys(models.Model):
    _inherit = 'car.diagnosys'

    timesheet_ids = fields.One2many('account.analytic.line','car_repair_timesheet_id',string="Timesheet")
    license_plate = fields.Char(string='License Plate')
    fleet = fields.Many2one('fleet.vehicle',string='Flota')
    brand = fields.Many2one('fleet.vehicle.model.brand', string='Marca')
    model = fields.Many2one('fleet.vehicle.model', string='Modelo')
    sale_order_id = fields.Many2one('sale.order')
    account_move_id = fields.Many2one('account.move')
    account_count = fields.Float(
        compute='_get_account_count', string="Quotation")

    def account_move_button(self):
        self.ensure_one()

        return {
            'name': 'Diagnosis invoice',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'domain': [('diagnose_id', '=', self.id)],
        }

    def _get_account_count(self):
        for account in self:
            account_ids = self.env['account.move'].search(
                [('diagnose_id', '=', account.id)])
            account.account_count = len(account_ids)

    def create_account(self):
        res = {}
        values = {}
        diagnose_obj = self.env['car.diagnosys'].browse(self.ids[0])
        car_repair_obj = self.env['car.repair']
        product_obj = self.env['product.product']

        journal_id = self.env['account.journal'].search([('type', '=', 'sale'),('name', '=', 'Facturas de cliente'),('company_id', '=', 1)])
        type_document = self.env['l10n_latam.document.type'].search([('code', '=', 33)])
        currency = self.env['res.currency'].search([('name', '=', 'CLP')])
        taxes = self.env['account.tax'].search([('type_tax_use', '=', 'sale')])
        tax_ids = [tax.id for tax in taxes if tax.l10n_cl_sii_code == 14 and tax.description == 'IVA 19% Venta']
        invoice = self.env['account.move'].create({
                                        'partner_id': diagnose_obj.partner_id.id,
                                        'move_type': 'out_invoice',
                                        'currency_id': currency.id,
                                        'state': 'draft',
                                        'invoice_date': datetime.now(),
                                        'journal_id': journal_id.id,
                                        'diagnose_id': diagnose_obj.id,
                                        'l10n_latam_document_type_id': type_document.id,


                            })

        for car_line in diagnose_obj.car_repair_estimation_ids:
            values['move_id'] = invoice.id
            values['name'] = car_line.notes,
            values['product_id'] = car_line.product_id.id
            values['account_id'] = journal_id.default_account_id.id
            values['quantity'] = car_line.quantity
            values['price_unit'] = car_line.price
            values['account_id'] = car_line.product_id.categ_id.property_account_income_categ_id.id,
            values['tax_ids'] = car_line.product_id.taxes_id.ids


        invoice.write({'invoice_line_ids': [(0, 0, values)]})
        invoice._onchange_partner_id()
        invoice._onchange_invoice_line_ids()
        invoice._move_autocomplete_invoice_lines_values()

        return res
        
