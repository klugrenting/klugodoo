# © 2022 (Jamie Escalante <jescalante@blueminds.cl>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AgreementType(models.Model):
    _name = "agreement.type"
    _description = "Agreement Types"

    name = fields.Char(string="Name", required=True)
    active = fields.Boolean(default=True)
    domain = fields.Selection(
        '_domain_selection', string='Domain', default='sale')
    agreement_subtypes_ids = fields.One2many(
        "agreement.subtype",
        "agreement_type_id",
        string="Subtypes"
    )

    @api.model
    def _domain_selection(self):
        return self.env['agreement']._domain_selection()
