# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
# Jamie Escalante, (jescalante@blueminds.cl)

from odoo import api, fields, models, _


class ResCompany(models.Model):
    _inherit = 'res.company'

    api_tag = fields.Boolean(string='is_tag', readonly=False)
    api_odometer = fields.Boolean(string='is_odometer', readonly=False)
    odo_user = fields.Char(string='Usuario', readonly=False)
    odo_psswd = fields.Char(string='Contraseña', readonly=False)
    odo_token = fields.Char(string='Token', readonly=False)
    odo_url = fields.Char(string='URL', readonly=False, default="https://api.smartreport.cl/v2/odometro/")
    tag_user = fields.Char(string='Usuario', readonly=False)
    tag_psswd = fields.Char(string='Contraseña', readonly=False)
    tag_token = fields.Char(string='Token', readonly=False)
    tag_url = fields.Char(string='URL', readonly=False, default="https://api.smartreport.cl/v1/tag/")