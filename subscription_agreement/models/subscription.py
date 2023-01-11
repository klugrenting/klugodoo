# © 2022 (Jamie Escalante <jescalante@blueminds.cl>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models, tools, fields, _
import base64
import logging
from io import BytesIO
from xlwt import Workbook, easyxf
from datetime import date
from dateutil.relativedelta import relativedelta
import calendar
import time
from datetime import timedelta, datetime
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class SaleSubscription(models.Model):
    _inherit = 'sale.subscription'
    
    
    
    
    deducible_maliciosos = fields.Integer('deducible malicioso')
    deducible_robo = fields.Integer('deducible robo')
    deducible_propios_terceros = fields.Integer('Danos propios y a Terceros')
    deducible_accesorios = fields.Integer('Robo accesorios')
    fecha_contrato = fields.Date('Fecha Contrato')
    maintenance = fields.Char(string="Frecuencia de mantenimiento")
    pago_garantia = fields.Boolean(default=False) 
    vehicle_id = fields.Many2one('fleet.vehicle', sting="Vehiculo", related='x_studio_many2one_field_aHUoE')
    date_expect_refund = fields.Date(string="Fecha esperada de devolucion")

    def set_close(self):
        today = fields.Date.from_string(fields.Date.context_today(self))
        search = self.env['sale.subscription.stage'].search
        for sub in self:
            stage = search([('category', '=', 'closed'), ('sequence', '>=', sub.stage_id.sequence)], limit=1)
            if not stage:
                stage = search([('category', '=', 'closed')], limit=1)
            values = {'stage_id': stage.id, 'to_renew': False}
            if sub.recurring_rule_boundary == 'unlimited' or not sub.date or today < sub.date:
                values['date_expect_refund'] = sub.date
                values['date'] = today
            sub.write(values)
        return True

            
                
