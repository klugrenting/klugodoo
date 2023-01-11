# Copyright (C) 2022 - TODAY, Jescalante@blueminds.cl
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)..

from odoo import fields, models, _, api
from odoo.exceptions import UserError


class SiiReference(models.Model):
    _inherit = "l10n_cl.account.invoice.reference"

    agreement_id = fields.Many2one('agreement')
    date_init = fields.Date(string="Fecha Inicio")
    date_end = fields.Date(string="Fecha Fin")
    sale_id = fields.Many2many('sale.order', 'sale_reference_rel', 'sale_id',
                               'reference_id',
                               string='Sale reference')

    @api.onchange('date_init')
    def _onchange_date_init(self):
        if self.date_init and self.date_end:
            if self.date_init > self.date_end:
                raise UserError("La fecha de inicio no puede ser mayor a la fecha fin")

    @api.onchange('date_end')
    def _onchange_date_end(self):
        if self.date_init and self.date_end:
            if self.date_end < self.date_init:
                raise UserError("La fecha fin no puede ser menor a la fecha de inicio")