# -*- coding: utf-8 -*-
# Copyright (C) 2022 - TODAY, Jescalante@blueminds.cl
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.osv import expression
from odoo.addons.fleet.models.fleet_vehicle_model import FUEL_TYPES

class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    product_id = fields.Many2one(
        "product.product",
        string="Producto")
    marca = fields.Char(string="Marca")
    modelo = fields.Char(string="Modelo")
    chasis = fields.Char(string="Chasis")
    motor = fields.Char(string="Motor")
    cilindrada = fields.Char(string="Cilindrada")
    anio = fields.Char(string="Año")
    transmision = fields.Char(string="Transmisión")
    color_kg = fields.Char(string="Color")
    combustible = fields.Char(string="Combustible")
    tipo_vehiculo = fields.Char(string="Tipo Vehículo")
    patente = fields.Char(string="Patente")

    @api.onchange('product_id')
    def onchange_product_id(self):
        if self.product_id:
            self.marca = self.product_id.marca
            self.modelo = self.product_id.modelo
            self.chasis = self.product_id.chasis
            self.motor = self.product_id.motor
            self.cilindrada = self.product_id.cilindrada
            self.anio = self.product_id.anio
            self.transmision = self.product_id.transmision
            self.color_kg = self.product_id.color_kg
            self.combustible = self.product_id.combustible
            self.tipo_vehiculo = self.product_id.tipo_vehiculo
            self.patente = self.product_id.patente
            self.license_plate = self.product_id.patente