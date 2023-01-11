# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

import time
import logging
from datetime import datetime
from datetime import date, datetime
from odoo.exceptions import Warning, UserError
from odoo import models, fields, exceptions, api, SUPERUSER_ID, _, tools
from uuid import uuid4

_logger = logging.getLogger(__name__)

class InhAccountMove(models.Model):
    _inherit = 'account.move'

    maintenance_id = fields.Many2one('maintenance.request', string='OT')


class InhMaintenance(models.Model):
    _inherit = ['maintenance.request']

    # portal 
    uuid = fields.Char('Account UUID', default=lambda self: str(uuid4()), copy=False, required=True)
    partner_id = fields.Many2one('res.partner', string='Cliente')
    street = fields.Char(string='Direccion')
    fleet = fields.Many2one('fleet.vehicle', string='Flota')
    brand = fields.Many2one('fleet.vehicle.model.brand', string='Marca')
    model = fields.Many2one('fleet.vehicle.model', string='Modelo')
    license_plate = fields.Char(string='Patente')
    year = fields.Char(string='Año')
    color = fields.Char(string='Color')
    sale_order_id = fields.Many2one('sale.order', string='Origen')
    failure = fields.Char(string='Falla')
    state_vehicule = fields.Char(string='Estado vehiculo')
    image_brand = fields.Binary(
        string="imagen marca", compute='_compute_image_vals')
    image_one = fields.Binary(string="imagen 1")
    image_two = fields.Binary(string="imagen 2")
    image_tree = fields.Binary(string="imagen 3")
    image_four = fields.Binary(string="imagen 4")
    image_five = fields.Binary(string="imagen 5")
    maintenance_line_products = fields.One2many(
        'maintenance.line.products', 'maintenance_product_id')
    maintenance_line_services = fields.One2many(
        'maintenance.line.services', 'maintenance_service_id')
    observations = fields.Text(string='Observaciones')
    odometer = fields.Integer(string='Odometro')
    account_count = fields.Integer(
        compute='_get_account_count', string="Factura")
    picking_count = fields.Integer(
        compute='_get_picking_count', string="Factura")
    
    total_price_products = fields.Float(string='Precio total')
    total_price_services = fields.Float(string='Precio total')
    total_neto = fields.Float(string='Subtotal')
    
    total_tax = fields.Float(string='Impuestos')
    total_tax_incluide = fields.Float(string='Total incluido')
    maintenance_count = fields.Integer(compute='_compute_maintenance_count')
    
    
    def _compute_maintenance_count(self):
        maintenance_data = self.env['maintenance.request'].read_group(domain=[('partner_id', 'in', self.ids), ('stage_id', '!=', False)],
                                                                     fields=['partner_id'],
                                                                     groupby=['partner_id'])
        mapped_data = dict([(m['partner_id'][0], m['partner_id_count']) for m in maintenance_data])
        for maintenances in self:
            maintenances.maintenance_count = mapped_data.get(maintenances.id, 0)

    
    
    def _init_column(self, column_name):
        # to avoid generating a single default uuid when installing the module,
        # we need to set the default row by row for this column
        if column_name == "uuid":
            _logger.debug("Table '%s': setting default value of new column %s to unique values for each row",
                          self._table, column_name)
            self.env.cr.execute("SELECT id FROM %s WHERE uuid IS NULL" % self._table)
            acc_ids = self.env.cr.dictfetchall()
            query_list = [{'id': acc_id['id'], 'uuid': str(uuid4())} for acc_id in acc_ids]
            query = 'UPDATE ' + self._table + ' SET uuid = %(uuid)s WHERE id = %(id)s;'
            self.env.cr._obj.executemany(query, query_list)

        
    
    def _compute_access_url(self):
        for record in self:
            record.access_url = '/my/contracts/{}'.format(record.id)

    def action_preview(self):
        """Invoked when 'Preview' button in contract form view is clicked."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'target': 'self',
            'url': self.get_portal_url(),
        }
    
    
    
    @api.onchange('user_id')
    def _onchange_user_id(self):
        if self.user_id:
            self.stage_id = 5



    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        if self.partner_id:
            self.street = self.partner_id.street
        
    
    @api.onchange('total_price_services', 'total_price_products')
    def _onchange_total_neto(self):
        for record in self:
            if record.total_price_products > 0 or record.total_price_services > 0:
                record.total_neto = record.total_price_services + record.total_price_products
                record.total_tax = record.total_neto * 0.19
                record.total_tax_incluide = record.total_neto + record.total_tax

    @api.onchange('fleet')
    def _onchange_fleet(self):
        for record in self:
            if record.fleet:
                record.brand = record.fleet.model_id.brand_id
                record.model = record.fleet.model_id
                record.license_plate = record.fleet.license_plate
                record.odometer = record.fleet.odometer
                record.year = record.fleet.model_year

    @api.onchange('maintenance_line_services')
    def _onchange_maintenance_services(self):
        total_price = 0
        subtotal_price_services = 0
        if self.maintenance_line_services:
            for record in self.maintenance_line_services:
                total_price = record.price * record.quantity
                record.total_subtotal_line_services = total_price
                subtotal_price_services += total_price 
                self.total_price_services = subtotal_price_services
        else:
            self.total_price_services = 0
            
    @api.onchange('maintenance_line_products')
    def _onchange_maintenance_products(self):
        total_price = 0
        subtotal_price_products = 0
        if self.maintenance_line_products:
            for record in self.maintenance_line_products:
                total_price = record.price * record.quantity
                record.total_subtotal_line_product = total_price
                subtotal_price_products += total_price 
                self.total_price_products = subtotal_price_products
        else:
            self.total_price_products = 0

    def account_move_button(self):
        self.ensure_one()

        return {
            'name': 'OT order invoice',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'domain': [('maintenance_id', '=', self.id)],
        }

    def _get_account_count(self):
        for account in self:
            account_ids = self.env['account.move'].search(
                [('maintenance_id', '=', account.id)])
            account.account_count = len(account_ids)

    @api.depends('image_brand')
    def _compute_image_vals(self):
        self.image_brand = self.brand.image_128

    def _get_picking_count(self):
        for picking in self:
            picking_ids = self.env['stock.picking'].search(
                [('origin', '=', self.name)])
            picking.picking_count = len(picking_ids)

    def picking_button(self):
        self.ensure_one()
        return {
            'name': 'Consume Parts Picking',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'stock.picking',
            'domain': [('origin', '=', self.name)],
        }

    def consume_car_parts(self):
        
        picking_type_id = self.env['stock.picking.type'].search([['code', '=', 'outgoing'], [
                                                                'warehouse_id.company_id', '=', self.company_id.id]], limit=1)

        picking = self.env['stock.picking'].create({
            'partner_id': self.partner_id.id,
            'picking_type_id': picking_type_id.id,
            'picking_type_code': 'outgoing',
            'location_id': picking_type_id.default_location_src_id.id,
            'location_dest_id': picking_type_id.default_location_dest_id.id,
            'origin': self.name,
        })
        for estitmate in self.maintenance_line_products:
            move = self.env['stock.move'].create({
                'picking_id': picking.id,
                'name': estitmate.product_id.name,
                'product_uom': estitmate.product_id.uom_id.id,
                'product_id': estitmate.product_id.id,
                'product_uom_qty': estitmate.quantity,
                'location_id': picking_type_id.default_location_src_id.id,
                'location_dest_id': picking_type_id.default_location_dest_id.id,
                'origin': self.name,
            })

    def create_account(self):
        # call picking function
        self.consume_car_parts()
        list_invoice = []
        res = {}
        values = {}
        values_product = {}
        maintenance_obj = self.env['maintenance.request'].browse(self.ids[0])
        car_repair_obj = self.env['car.repair']
        product_obj = self.env['product.product']
        maintenance_stage = self.env['maintenance.stage'].search([('name', '=', 'Facturado')])
        maintenance_obj.stage_id = maintenance_stage.id
        journal_id = self.env['account.journal'].search([('type', '=', 'sale'), (
            'name', '=', 'Facturas de cliente'), ('company_id', '=', self.company_id.id)])
        type_document = self.env['l10n_latam.document.type'].search(
            [('code', '=', 33)])
        currency = self.env['res.currency'].search([('name', '=', 'CLP')])
        taxes = self.env['account.tax'].search([('type_tax_use', '=', 'sale')])
        tax_ids = [tax.id for tax in taxes if tax.l10n_cl_sii_code ==
                   14 and tax.description == 'IVA 19% Venta']
        invoice = self.env['account.move'].create({
            'partner_id': maintenance_obj.partner_id.id,
            'move_type': 'out_invoice',
            'currency_id': currency.id,
            'state': 'draft',
            'invoice_date': datetime.now(),
            'journal_id': journal_id.id,
            'maintenance_id': maintenance_obj.id,
            'l10n_latam_document_type_id': type_document.id,


        })

        for services_line in maintenance_obj.maintenance_line_services:
            values = {
                'move_id': invoice.id,
                'name': 'Trabajo segun ' + maintenance_obj.name,
                'product_id': services_line.product_id.id,
                'account_id': journal_id.default_account_id.id,
                'quantity': services_line.quantity,
                'price_unit': services_line.price,
                'account_id': services_line.product_id.categ_id.property_account_income_categ_id.id,
                'tax_ids': services_line.product_id.taxes_id.ids,
            }

            list_invoice.append(values)
        for products_line in maintenance_obj.maintenance_line_products:
            values_product = {
                'move_id': invoice.id,
                'name': 'Trabajo segun ' + maintenance_obj.name,
                'product_id': products_line.product_id.id,
                'account_id': journal_id.default_account_id.id,
                'quantity': products_line.quantity,
                'price_unit': products_line.price,
                'account_id': products_line.product_id.categ_id.property_account_income_categ_id.id,
                'tax_ids': products_line.product_id.taxes_id.ids,
            }

            list_invoice.append(values_product)

        invoice.write(
            {'invoice_line_ids': [(0, 0, values) for values in list_invoice]})
        invoice._onchange_partner_id()
        invoice._onchange_invoice_line_ids()
        invoice._move_autocomplete_invoice_lines_values()


class InhMaintenanceLineProducts(models.Model):

    _name = 'maintenance.line.products'

    product_id = fields.Many2one('product.product', string='Productos')
    description = fields.Char(string='Descripción')
    price = fields.Float(string='Precio')
    quantity = fields.Float(string='Cantidad', default=1)
    maintenance_product_id = fields.Many2one(
        'maintenance.request', string='Presupuesto')
    total_subtotal_line_product = fields.Float(string='Subtotal Linea')
    


class InhMaintenanceLineServices(models.Model):

    _name = 'maintenance.line.services'

    product_id = fields.Many2one('product.product', string='Productos')
    description = fields.Char(string='Descripción')
    price = fields.Float(string='Precio')
    quantity = fields.Float(string='Cantidad')
    maintenance_service_id = fields.Many2one(
        'maintenance.request', string='Presupuesto')
    total_subtotal_line_services = fields.Float(string='Subtotal Linea')
