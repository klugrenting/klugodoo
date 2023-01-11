# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
# Jamie Escalante, (jescalante@blueminds.cl)


from odoo import fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    agreement_id = fields.Many2one(
        comodel_name='agreement', string='Agreement', ondelete='restrict',
        track_visibility='onchange', readonly=True, copy=False,
        states={'draft': [('readonly', False)]})

