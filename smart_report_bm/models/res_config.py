# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
# Jamie Escalante, (jescalante@blueminds.cl)

from odoo import api, fields, models, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # company_id = fields.Many2one(
    #     'res.company', string='Company', related='event_id.company_id',
    #     store=True, readonly=True, states={'draft': [('readonly', False)]})
    api_tag = fields.Boolean(related='company_id.api_tag', string='is_tag', readonly=False)
    api_odometer = fields.Boolean(related='company_id.api_odometer', string='is_odometer', readonly=False)
    odo_user = fields.Char(related='company_id.odo_user', string='Usuario', readonly=False)
    odo_psswd = fields.Char(related='company_id.odo_psswd', string='Contraseña', readonly=False)
    odo_token = fields.Char(related='company_id.odo_token', string='Token', readonly=False)
    odo_url = fields.Char(related='company_id.odo_url', string='URL Odómetro', readonly=False, default="https://api.smartreport.cl/v2/odometro/")
    tag_user = fields.Char(related='company_id.tag_user', string='Usuario', readonly=False)
    tag_psswd = fields.Char(related='company_id.tag_psswd', string='Contraseña', readonly=False)
    tag_token = fields.Char(related='company_id.tag_token', string='Token', readonly=False)
    tag_url = fields.Char(related='company_id.tag_url', string='URL TAG', readonly=False, default="https://api.smartreport.cl/v1/tag/")

    def set_values(self):
        res = super(ResConfigSettings, self).set_values()
        params_obj = self.env['ir.config_parameter']

        params_obj.sudo().set_param('api_tag', self.api_tag)
        params_obj.sudo().set_param('api_odometer', self.api_odometer)
        params_obj.sudo().set_param('odo_user', self.odo_user)
        params_obj.sudo().set_param('odo_psswd', self.odo_psswd)
        params_obj.sudo().set_param('odo_token', self.odo_token)
        params_obj.sudo().set_param('odo_url', self.odo_url)
        params_obj.sudo().set_param('tag_user', self.tag_user)
        params_obj.sudo().set_param('tag_user', self.tag_user)
        params_obj.sudo().set_param('tag_psswd', self.tag_psswd)
        params_obj.sudo().set_param('tag_url', self.tag_url)

        return res
