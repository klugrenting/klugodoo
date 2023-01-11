# Copyright (C) 2022 - TODAY, Jescalante@blueminds.cl
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AgreementLine(models.Model):
    _name = "rentals.line"
    _description = "Agreement Rental Lines"

    name = fields.Char(
        string="Nombre",
        required=True)
    agreement_id = fields.Many2one(
        "agreement",
        string="Agreement",
        ondelete="cascade")
    state = fields.Selection([
        ('draft', 'Quotation'),
        ('sent', 'Quotation Sent'),
        ('sale', 'Sales Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled'),
    ], string='Estado', readonly=True, copy=False, index=True, tracking=3, default='draft')

