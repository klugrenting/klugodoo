# -*- coding: utf-8 -*-
# Copyright (C) 2022 - TODAY, Jescalante@blueminds.cl
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class SaleOrderDetail(models.Model):
    _name = 'sale.order.detail'

    name = fields.Many2one(
        "product.product",
        string="Vehiculo", track_visibility='onchange',
    )
    code = fields.Char(string='Patente')
    km_anterior = fields.Float(string='Km Recorrido mes anterior')
    km_acum = fields.Float(string='Km Acumulado')
    km_mes = fields.Float(string='Km Promedio Mes')
    mes_contract = fields.Integer(string='Mes Contrato')
    contract = fields.Integer(string='Contrato')
    co2_e = fields.Integer(string='CO2 Emitido (Kg)')
    co2_a = fields.Integer(string='Co2 Acumulado (Kg)')
    order_id = fields.Many2one('sale.order', 'orden', required=True)


class SaleOrderDetaill(models.Model):
    _name = 'sale.order.detaill'

    name = fields.Many2one(
        "product.product",
        string="Vehiculo", track_visibility='onchange',
    )
    date = fields.Date("Fecha")
    category = fields.Char(string='Categoría')
    concesion = fields.Char(string='Concesión')
    description = fields.Char(string='Descripción')
    km = fields.Float(string='KM')
    tarifa = fields.Float(string='Tarifa')
    order_id = fields.Many2one('sale.order', 'orden', required=True)