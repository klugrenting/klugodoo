# -*- coding: utf-8 -*-
# Copyright (C) 2022 - TODAY, Jescalante@blueminds.cl
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class FleetVehicleIncidencia(models.Model):
    _name = 'fleet.vehicle.incidencia'


    name = fields.Char(string='Proveedor')
    date = fields.Date(string='Fecha')
    mensaje = fields.Char(string='Mensaje')
    mensaje_consul = fields.Char(string='Mensaje Consulta')
    vehicle_id = fields.Many2one('fleet.vehicle', 'Vehicle', required=True)