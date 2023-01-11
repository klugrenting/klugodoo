# © 2022 (Jamie Escalante <jescalante@blueminds.cl>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models, tools, fields, _




class Agreement(models.Model):
    _inherit = 'agreement.line'
    
    
    deducible = fields.Float('deducible')
    deducible_robo = fields.Float('deducible robo')

