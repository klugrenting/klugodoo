# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import time

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta


class CreateTest(models.TransientModel):
    _name = "create.test"
    _description = "Creacion de instalacion"

    type = fields.Selection([
        ('prueba', 'Instalacion de Prueba'),
        ('definitiva', 'Instalacion Definitiva'),
        ('inmediata', 'Instalacion Inmediata')
        ], string='Tipo de Instalacion', required=True,
        help="Seleccione si la instacion es de prueba o definitiva).")
    date_test = fields.Date(string='Fecha', required=True, default=datetime.now())
    notes = fields.Text('Notas')
    #user_id = fields.Many2one('res.users', string='Responsible', required=False, default=lambda self: self.env.user)

    def create_test(self):
        line_id = self._context.get('active_id', False)
        line = self.env['agreement.line'].browse(line_id)
        ## /// new
        # ticket_man = self.env['helpdesk.ticket'].create({
        #     'name': 'Instalación ' + line.product_id.name,
        #     'partner_id': line.agreement_id.partner_id.id,
        #     #'assign_date': self.date_test,
        #     'fecha_registro_ticket': self.date_test,
        #     'agreement_id': line.agreement_id.id,
        #     'ticket_type_id': 1,
        #     'agreement_line_ids': line.id,
        #     'partner_email': line.agreement_id.partner_id.email,
        #     # 'user_id': line.mantenedor or False,
        # })
        # order_lineM = self.env['project.task'].create({
        #     'name': 'Instalación ' + line.product_id.name,
        #     'partner_id': line.agreement_id.partner_id.id,
        #     'helpdesk_ticket_id': ticket_man.id,
        #     'stage_id': 4,
        #     'fsm_done': False,
        #     'project_id': 2,
        # })
        # for x in line.product_id.product_related_ids:
        #     order_lineM_l = self.env['project.task.product'].create({
        #         'product_id': x.product_id.id,
        #         'description': x.name,
        #         'planned_qty': x.qty,
        #         'product_uom': x.product_id.uom_id.id,
        #         'time_spent': x.time_spent,
        #         'task_id': order_lineM.id,
        #     })
        fecha_cobro = self.date_test + relativedelta(days=int(line.test_day.code))
        line.write({'state': 'pen', 'start_date': self.date_test, 'fecha_cobro': fecha_cobro})
        line.agreement_id.write({'stage_id': 2})
        return True