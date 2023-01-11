# -*- coding: utf-8 -*-
# Copyright (C) 2022 - TODAY, Jescalante@blueminds.cl
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class FleetVehicleOdometer(models.Model):
    _inherit = 'fleet.vehicle.odometer'

    date = fields.Datetime(default=fields.Date.context_today)
    tag_ids = fields.Many2many('fleet.vehicle.tag', 'fleet_vehicle_vehicle_odometer_tag_rel', 'odometer_tag_id', 'tag_id', 'Categoría',
                               copy=False)
    amount = fields.Float(string='Tarifa')
    concession = fields.Char(string='Concesión')
    description = fields.Char(string='Descripción/Vía')
    category = fields.Char(string='Categoría/Tipo Multa')