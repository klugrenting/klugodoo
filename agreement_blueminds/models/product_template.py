# Copyright (C) 2022 - TODAY, Jescalante@blueminds.cl
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, tools, _


class Product(models.Model):
    _inherit = "product.template"

    agreements_ids = fields.Many2many(
        "agreement",
        string="Agreements")

    #product_version_id = fields.Many2one('product.version', string='Version')
    # product_related_ids = fields.One2many('product.related', 'product_parent_id', string='Related products',
    #                                       copy=True, auto_join=True)
    name_key = fields.Char(string='Name on Invoice', required=True)
    # means_ids = fields.Many2many('means', string="Resources")
    # capabilities_ids = fields.Many2many('capabilities', string="Capabilities")
    is_principal = fields.Boolean(string="It is main service", default=False)
    fleet_vehicle = fields.Many2one('fleet.vehicle', string='Vehiculo Flota')
    fleet = fields.Boolean(string="Es Flota", default=False)

    @api.model_create_multi
    def create(self, vals_list):
        if 'product_version_id' in vals_list:
            version = self.env['product.version'].browse(vals_list['product_version_id'])
            vals_list['name'] = str(vals_list['name']) + ' ' + str(version.name)
        return super(Product, self).create(vals_list)

class ProductVersion(models.Model):
    _name = 'product.version'

    name = fields.Char(string='Version', required=True)

class ProductRelated(models.Model):
    _name = 'product.related'

    product_id = fields.Many2one(
        "product.product",
        string="Product")
    product_parent_id = fields.Many2one('product.template', string='Product Reference', required=True, ondelete='cascade', index=True,
                               copy=False)
    name = fields.Char(
        string="Description",
        required=True)
    qty = fields.Float(string="Quantity", default=1)
    uom_id = fields.Many2one(
        "uom.uom",
        string="Unit of measurement",
        required=True)
    is_principal = fields.Boolean(string="It is main service", default=False)
    time_spent = fields.Float('Time/Hours', precision_digits=2)

    # @api.onchange("product_id")
    # def _onchange_product_id(self):
    #     self.name = self.product_id.name
    #     self.uom_id = self.product_id.uom_id.id
