# © 2022 (Jamie Escalante <jescalante@blueminds.cl>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models


class AgreementDocument(models.Model):
    _name = "agreement.document"
    _description = 'Documentos'

    recital_ids = fields.One2many(
        "agreement.recital", "document_id", string="Documentos Extra", copy=True)
    sections_ids = fields.One2many(
        "agreement.section", "document_id", string="Sections", copy=True)
    clauses_ids = fields.One2many(
        "agreement.clause", "document_id", string="Clauses")
    appendix_ids = fields.One2many(
        "agreement.appendix", "document_id", string="Appendices", copy=True)
    agreement_id = fields.Many2one(
        "agreement", string="Agreement", ondelete="cascade")