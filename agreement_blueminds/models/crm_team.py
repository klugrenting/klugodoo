# -*- coding: utf-8 -*-

from odoo import api, models, fields,_
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError, UserError

from odoo.fields import Date

class Team(models.Model):
    _inherit = 'crm.team'

    def _compute_template(self):
        res = {}
        templates_all = self.search([])
        arrs = []
        today = datetime.now()
        domain = [('is_template', '=', True), ('expiration_date', '>=', today)]
        templates_ids = self.env['agreement'].sudo().search([
            ('is_template', '=', True),
            ('expiration_date', '>=', today),
            ('is_template', '=', True),
            ('team_id_domain', 'in', self.id)])
        exc_templates_ids = self.env['agreement'].sudo().search([
            ('is_template', '=', True),
            ('expiration_date', '>=', today),
            ('is_template', '=', True),
            ('exception_team_id_domain', 'in', self.id)])
        template_domain = []
        if templates_ids:
            for temp in templates_ids:
                template_domain.append(temp.id)
        if exc_templates_ids:
            for exc in exc_templates_ids:
                if exc.id not in template_domain:
                    template_domain.append(exc.id)
        self.template_domain = template_domain

    template_agreement_id = fields.Many2one('agreement', string='Template')
    exception_agreement_id = fields.Many2one('agreement', string='Template exception', domain=[('is_template', '=', True)])
    template_domain = fields.Many2many('agreement', 'template_team_rel', 'parent_id',
                                       'team_id', compute='_compute_template',
                                       string='Domain for templates')
