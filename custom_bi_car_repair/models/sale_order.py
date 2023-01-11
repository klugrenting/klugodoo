# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.


import time
from datetime import datetime
from datetime import date, datetime
from odoo.exceptions import Warning, UserError
from odoo import models, fields, exceptions, api


class InhSaleOrder(models.Model):
    _inherit = 'sale.order'

    responsible_id = fields.Many2one('res.users', string='Responsable')
    type_sale = fields.Selection([('normal_sale_order', 'Presupuesto Estandar'), (
        'service_sale_order', 'Presupuesto Servicio')], string="Tipo de presupuesto", default="normal_sale_order")
    company_name = fields.Char(
        string='nombre compania', related="company_id.name")
    fleet = fields.Many2one('fleet.vehicle', string='Flota')
    brand = fields.Many2one('fleet.vehicle.model.brand', string='Marca')
    model = fields.Many2one('fleet.vehicle.model', string='Modelo')
    model_year = fields.Char(string='Año')
    license_plate = fields.Char(string='Patente')
    worker_order_count = fields.Integer(
        compute='_get_worker_order_count', string="worker order")
    description = fields.Char(string='Diagnostico')
    

    

    @api.onchange('fleet')
    def _onchange_fleet(self):
        for record in self:
            if record.fleet:
                
                record.brand = record.fleet.model_id.brand_id
                record.model = record.fleet.model_id
                record.license_plate = record.fleet.license_plate
                record.model_year = record.fleet.model_year

    @api.depends('type_sale')
    def _compute_type_sale(self):
        pricelist_ids = self.env['product.pricelist'].search(
            ['name', '=', 'Tarifa Pesos'], limit=1)
        for record in self:
            if record.type_sale == 'service_sale_order':
                record.pricelist_id = pricelist_ids.id

    def worker_order_button(self):
        self.ensure_one()

        return {
            'name': 'Sale order OT',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'maintenance.request',
            'domain': [('sale_order_id', '=', self.id)],
        }

    def _get_worker_order_count(self):
        for sale in self:
            worker_ids = self.env['maintenance.request'].search(
                [('sale_order_id', '=', sale.id)])
            sale.worker_order_count = len(worker_ids)

    def create_worker_order(self):
        maintenance_team = self.env['maintenance.team'].search(
            [('name', '=', 'Equipo Klug Servicio')])
        sale_obj = self.env['sale.order'].browse(self.ids[0])
        sale_obj.state = 'sale'
        vals = {
            'name': sale_obj.name,
            'description': sale_obj.description,
            'maintenance_team_id': maintenance_team.id,
            'partner_id': sale_obj.partner_id.id,
            'street': sale_obj.partner_id.street,
            'sale_order_id': sale_obj.id,
            'fleet': sale_obj.fleet.id,
            'brand': sale_obj.brand.id,
            'model': sale_obj.model.id,
            'year': sale_obj.model_year,
            'license_plate': sale_obj.license_plate,
            'user_id': sale_obj.responsible_id.id,


        }

        maintenance_id = self.env['maintenance.request'].create(vals)
        
        if sale_obj.order_line:
            for record in sale_obj.order_line:
            
                if record.product_id.detailed_type == 'service':
                    vals_services = {
                        'product_id': record.product_id.id,
                        'description': record.name,
                        'price': record.price_unit,
                        'quantity': record.product_uom_qty,
                    }
                    maintenance_id.write(
                    {'maintenance_line_services': [(0, 0, vals_services)]})
                if record.product_id.detailed_type == 'product':
                    vals_products = {
                        'product_id': record.product_id.id,
                        'description': record.name,
                        'price': record.price_unit,
                        'quantity': record.product_uom_qty,
                    }
                    maintenance_id.write(
                    {'maintenance_line_products': [(0, 0, vals_products)]})
                
        
        
        
        # maintenance_id.write(
        #     {'maintenance_line_services': [(0, 0, vals_services)]})
        # maintenance_id.write(
        #     {'maintenance_line_products': [(0, 0, vals_products)]})
        maintenance_id._onchange_maintenance_services()
        maintenance_id._onchange_maintenance_products()
        maintenance_id._onchange_total_neto()
        maintenance_id.consume_car_parts()
        return True
