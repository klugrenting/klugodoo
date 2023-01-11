# © 2022 (Jamie Escalante <jescalante@blueminds.cl>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


# Main Agreement Status Records Model
class AgreementStatus(models.Model):
    _name = "agreement.type"

    # General
    name = fields.Char(string="Title", required=True)
