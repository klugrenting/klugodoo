# © 2022 (Jamie Escalante <jescalante@blueminds.cl>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class InvoiceLine(models.Model):
    _name = "invoice.line"
    _description = "Agreement Invoice Lines"

    name = fields.Char(
        string="Numero",
        required=True)
    date = fields.Date(string='Date',
                       default=fields.Date.context_today)
    agreement_id = fields.Many2one(
        "agreement",
        string="Agreement",
        ondelete="cascade")
    agreement_line_ids = fields.Many2one('agreement.line', track_visibility="onchange", string="Linea de Contrato",
                                         ondelete="cascade")
    state = fields.Selection(selection=[
        ('draft', 'Draft'),
        ('posted', 'Posted'),
        ('cancel', 'Cancelled')
    ], string='Estado', required=True, readonly=True, copy=False, tracking=True,
        default='draft')
    invoice_payment_state = fields.Selection(selection=[
        ('not_paid', 'Not Paid'),
        ('in_payment', 'In Payment'),
        ('paid', 'Paid')],
        string='Payment', store=True, readonly=True, copy=False, tracking=True)