# © 2022 (Jamie Escalante <jescalante@blueminds.cl>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models, tools, fields, _


class InheritProduct(models.Model):
    _inherit = 'product.product'

    traccion_vehicle = fields.Selection([('4x4', '4x4'),('4x2', '4x2'),('AWD', 'AWD')])
    accesories_vehicle = fields.Many2many('accesories.tags', string='Accesorios de Vehiculo', store=True)


 
