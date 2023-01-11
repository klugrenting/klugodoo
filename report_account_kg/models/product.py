# -*- coding: utf-8 -*-

from odoo import api, models, fields


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    marca = fields.Char(string="Marca")
    modelo = fields.Char(string="Modelo")
    chasis = fields.Char(string="Chasis")
    estado = fields.Char(string="Estado")
    motor = fields.Char(string="Motor")
    kilometraje = fields.Integer(string="Kilometraje")
    cilindrada = fields.Char(string="Cilindrada")
    anio = fields.Char(string="Año")
    transmision = fields.Char(string="Transmisión")
    color_kg = fields.Char(string="Color")
    combustible = fields.Char(string="Combustible")
    tipo_vehiculo = fields.Char(string="Tipo Vehículo")
    patente = fields.Char(string="Patente")