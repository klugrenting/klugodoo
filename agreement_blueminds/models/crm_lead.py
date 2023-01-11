# -*- coding: utf-8 -*-

from odoo import api, models, fields,_
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError, UserError

from odoo.fields import Date

class Lead(models.Model):
    _inherit = 'crm.lead'

    # def _compute_template(self):
    #     today = datetime.now()
    #     domain = [('is_template', '=', True), ('expiration_date', '>=', today)]
    #     templates_ids = self.env['agreement'].sudo().search([
    #         ('is_template', '=', True),
    #         ('expiration_date', '>=', today),
    #         ('is_template', '=', True),
    #         ('team_id_domain', 'in', self.team_id.id)])
    #     exc_templates_ids = self.env['agreement'].sudo().search([
    #         ('is_template', '=', True),
    #         ('expiration_date', '>=', today),
    #         ('is_template', '=', True),
    #         ('exception_team_id_domain', 'in', self.team_id.id)])
    #     template_domain = []
    #     if templates_ids:
    #         for temp in templates_ids:
    #             template_domain.append(temp.id)
    #     if exc_templates_ids:
    #         for exc in exc_templates_ids:
    #             if exc.id not in template_domain:
    #                 template_domain.append(exc.id)
    #     self.template_domain = template_domain
    #     self.template_agreement_id = self.team_id.template_agreement_id.id
    #     self.payment_method_domain = self.team_id.template_agreement_id.payment_method_domain.ids
    #     self.type_partner_domain = self.team_id.template_agreement_id.type_partner_domain.ids

    # @api.model
    # def default_get(self, fields):
    #     result = super(Lead, self).default_get(fields)
    #     #team_id = result.get('team_id')
    #     if self.team_id:
    #         templates_ids = self.env['agreement'].sudo().search([
    #             ('is_template', '=', True),
    #             ('team_id_domain', 'in', self.team_id.id)])
    #         exc_templates_ids = self.env['agreement'].sudo().search([
    #             ('is_template', '=', True),
    #             ('exception_team_id_domain', 'in', self.team_id.id)])
    #         template_domain = []
    #         if templates_ids:
    #             for temp in templates_ids:
    #                 template_domain.append(temp.id)
    #         if exc_templates_ids:
    #             for exc in exc_templates_ids:
    #                 if exc.id not in template_domain:
    #                     template_domain.append(exc.id)
    #         result['template_domain'] = template_domain
    #         result['template_agreement_id'] = self.team_id.template_agreement_id.id
    #         result['payment_method_domain'] = self.team_id.template_agreement_id.payment_method_domain.ids
    #         result['type_partner_domain'] = self.team_id.template_agreement_id.type_partner_domain.ids
    #     return result


    def _compute_agreement_count(self):
        agreement_data = self.sudo().env['agreement'].read_group([('state', '!=', 'cancel'), ('crm_lead_id', 'in', self.ids)], ['crm_lead_id'], ['crm_lead_id'])
        mapped_data = dict([(q['crm_lead_id'][0], q['crm_lead_id_count']) for q in agreement_data])
        for agreement in self:
            agreement.agreement_count = mapped_data.get(agreement.id, 0)

    @api.depends('crm_line_ids.price')
    def _amount_line_all(self):
        """
        Compute the total amounts of the crm.
        """
        for lead in self:
            amount_total = 0.0
            for line in lead.crm_line_ids:
                amount_total += line.price
            lead.update({
                'planned_revenue': amount_total,
            })

    partner_id = fields.Many2one(domain="[('parent_id', '=', False)]")
    # type_contrib_partner = fields.Many2one(related='partner_id.type_contrib', string='Type of taxpayer', required=False)
    agreement_count = fields.Integer(compute='_compute_agreement_count')
    agreement_id = fields.Many2one('agreement', "Father Contract",
                                   help="Select a parent contract to generate an annex of that selected contract",
                                  required=False, domain="[('partner_id', '=', partner_id)]")
    crm_line_ids = fields.One2many('crm.line', 'crm_id', string='Services')
    # crm_line_serv_real = fields.One2many('crm.line', 'crm_id', string='Royal Services')
    planned_revenue = fields.Float(compute='_amount_line_all')
    # crm_captado_id = fields.Many2one(
    #     'res.partner',
    #     string='captured by')
    # crm_gestionado_id = fields.Many2one(
    #     'res.partner',
    #     string='Managed by')
    # canal_id = fields.Many2one(
    #     'crm.canal',
    #     string='Channel')
    # subcanal_id = fields.Many2one(
    #     'crm.subcanal',
    #     string='sub channel')
    # payment_method = fields.Many2one(
    #     "agreement.payment.method", required=False, domain="[('id', 'in', [1,2,3,4])]",
    #     string="Payment method")
    # type_partner = fields.Many2one(
    #     "agreement.type.partner", required=False,
    #     string="Type of contract", help="Type of client (household, company, HORECA - INTERNAL, HORECA - SELF-BOTTLING)")
    # template_agreement_id = fields.Many2one('agreement', string='Template')
    # check_exception = fields.Boolean(string='Exception Template', default=False)
    # exception = fields.Boolean(string='Check Exception Template', default=False)
    # valid_exception = fields.Boolean(string='Valid Exception Template', default=False)
    # template_domain = fields.Many2many('agreement', 'template_lead_rel', 'parent_id',
    #                                    'lead_id', compute='_compute_template',
    #                                    string='Domain for contract')
    # payment_method_domain = fields.Many2many('agreement.payment.method', 'method_lead_rel', 'method_id',
    #                                          'lead_id',
    #                                          string='Payment method')
    # type_partner_domain = fields.Many2many('agreement.type.partner', 'lead_type_partner_rel', 'type_id',
    #                                        'lead_id',
    #                                        string='Type of contract')


    # @api.onchange('team_id')
    # def onchange_team_id(self):
    #     res = {}
    #     template_domain = []
    #     if self.team_id:
    #         templates_ids = self.env['agreement'].sudo().search([
    #             ('is_template', '=', True),
    #             ('team_id_domain', 'in', self.team_id.id)])
    #         exc_templates_ids = self.env['agreement'].sudo().search([
    #             ('is_template', '=', True),
    #             ('exception_team_id_domain', 'in', self.team_id.id)])
    #         template_domain = []
    #         if templates_ids:
    #             for temp in templates_ids:
    #                 template_domain.append(temp.id)
    #         if exc_templates_ids:
    #             for exc in exc_templates_ids:
    #                 if exc.id not in template_domain:
    #                     template_domain.append(exc.id)
    #     self.template_domain = template_domain
    #     self.template_agreement_id = self.team_id.template_agreement_id.id

    # @api.onchange('template_agreement_id', 'payment_method', 'type_partner', 'agreement_id')
    # def onchange_template_agreement_id(self):
    #     res = {}
    #     template_domain = []
    #     payment_method_domain = []
    #     type_partner_domain = []
    #     if self.agreement_id:
    #         self.template_agreement_id = self.agreement_id.template_agreement_id.id
    #         self.payment_method = self.agreement_id.payment_method.id
    #         self.type_partner = self.agreement_id.type_partner.id
    #         self.template_domain = self.agreement_id.template_agreement_id.ids
    #         self.payment_method_domain = self.agreement_id.payment_method.ids
    #         self.type_partner_domain = self.agreement_id.type_partner.ids
    #         return res
    #     if self.template_agreement_id:
    #         self.payment_method_domain = self.template_agreement_id.payment_method_domain
    #         self.type_partner_domain = self.template_agreement_id.type_partner_domain
    #         if self.team_id.id in self.template_agreement_id.exception_team_id_domain.ids:
    #             self.check_exception = True
    #         else:
    #             self.check_exception = False
    #     if not self.template_agreement_id:
    #         if self.payment_method:
    #             templates_method = self.env['agreement'].sudo().search([
    #                 ('is_template', '=', True),
    #                 ('team_id_domain', 'in', self.team_id.id),
    #                 ('payment_method_domain', 'in', self.payment_method.id)])
    #             templates_method_exc = self.env['agreement'].sudo().search([
    #                 ('is_template', '=', True),
    #                 ('exception_team_id_domain', 'in', self.team_id.id),
    #                 ('payment_method_domain', 'in', self.payment_method.id)])
    #             if templates_method:
    #                 for temp in templates_method:
    #                     template_domain.append(temp.id)
    #             if templates_method_exc:
    #                 for exc in templates_method_exc:
    #                     if exc.id not in template_domain:
    #                         template_domain.append(exc.id)
    #             for temp1 in self.template_domain:
    #                 for tparner in temp1.type_partner_domain:
    #                     if tparner.id not in type_partner_domain:
    #                         type_partner_domain.append(tparner.id)
    #             self.template_domain = template_domain
    #             self.payment_method_domain = self.payment_method
    #             self.type_partner_domain = type_partner_domain
    #         if not self.payment_method:
    #             if self.type_partner:
    #                 templates_tpartner = self.env['agreement'].sudo().search([
    #                     ('is_template', '=', True),
    #                     ('team_id_domain', 'in', self.team_id.id),
    #                     ('type_partner_domain', 'in', self.type_partner.id)])
    #                 templates_tpartner_exc = self.env['agreement'].sudo().search([
    #                     ('is_template', '=', True),
    #                     ('exception_team_id_domain', 'in', self.team_id.id),
    #                     ('type_partner_domain', 'in', self.type_partner.id)])
    #                 if templates_tpartner:
    #                     for temp in templates_tpartner:
    #                         template_domain.append(temp.id)
    #                 if templates_tpartner_exc:
    #                     for exc2 in templates_tpartner_exc:
    #                         if exc2.id not in template_domain:
    #                             template_domain.append(exc2.id)
    #                 for temp2 in template_domain:
    #                     temp2 = self.env['agreement'].sudo().browse(temp2)
    #                     for method in temp2.payment_method_domain:
    #                         if method.id not in payment_method_domain:
    #                             payment_method_domain.append(method.id)
    #                 self.template_domain = template_domain
    #                 self.payment_method_domain = payment_method_domain
    #                 self.type_partner_domain = self.type_partner
    #             if not self.type_partner:
    #                 templates_ids = self.env['agreement'].sudo().search([
    #                     ('is_template', '=', True),
    #                     ('team_id_domain', 'in', self.team_id.id)])
    #                 exc_templates_ids = self.env['agreement'].sudo().search([
    #                     ('is_template', '=', True),
    #                     ('exception_team_id_domain', 'in', self.team_id.id)])
    #                 if templates_ids:
    #                     for temp in templates_ids:
    #                         template_domain.append(temp.id)
    #                 if exc_templates_ids:
    #                     for exc in exc_templates_ids:
    #                         if exc.id not in template_domain:
    #                             template_domain.append(exc.id)
    #                 for temp in template_domain:
    #                     temp3 = self.env['agreement'].sudo().browse(temp)
    #                     for method in temp3.payment_method_domain:
    #                         if method.id not in payment_method_domain:
    #                             payment_method_domain.append(method.id)
    #                     for tparner in temp3.type_partner_domain:
    #                         if tparner.id not in type_partner_domain:
    #                             type_partner_domain.append(tparner.id)
    #                 self.template_domain = template_domain
    #                 self.payment_method_domain = payment_method_domain
    #                 self.type_partner_domain = type_partner_domain

    def create_agreement(self):
        if not self.partner_id:
            raise UserError("Cannot create a contract without a Client. ")
        created = self.env['agreement'].create({
            'partner_id': self.partner_id.id,
            'description': self.description or 'nuevo',
            'name': 'Nuevo',
            'crm_lead_id': self.id,
            #'agreement_type_id': 1,
            'end_date': Date.to_string((datetime.now() + timedelta(days=365))),
            'start_date': Date.today(),
            'is_template': False,
            'team_id': self.team_id.id,
            'assigned_user_id': self.user_id.id,
            # 'template_agreement_id': self.template_agreement_id.id,
        })
        for deltals in self.crm_line_ids:
            contract_line = {
                'agreement_id': created.id,
                'product_id': deltals.product_id.id,
                'name': deltals.product_id.name,
                'uom_id': deltals.product_id.uom_id.id,
                'partner_contact_id': deltals.partner_contact_id.id,
                'partner_invoice_id': deltals.partner_invoice_id.id,
                'price': deltals.price,
            }
            line = self.env['agreement.line'].create(contract_line)
        # if self.template_agreement_id.extra_ids:
        #     for document in self.template_agreement_id.extra_ids:
        #         contract_document = {
        #             'agreement_id': created.id,
        #             'name': created.name,
        #             'firma': document.firma,
        #             'type_extra': document.type_extra.id,
        #             'required_sign': document.required_sign,
        #             'require_maihue': document.require_maihue,
        #             'content': document.content,
        #         }
        #         line_document = self.env['agreement.extra'].create(contract_document)
        return created

    def action_agreement(self):
        action = self.env.ref('agreement.agreement_form').read()[0]
        action['views'] = [(self.env.ref('agreement.agreement_form').id, 'form')]
        action['context'] = {
                             'name': self.name,
                             'code': self.name,
                            }
        return action

    def action_view_agreement(self):
        action = self.env.ref('agreement_blueminds.agreement_dashboard_agreement').read()[0]
        action['context'] = {
            'search_default_draft': 1,
            'search_default_partner_id': self.partner_id.id,
            'default_partner_id': self.partner_id.id,
            'default_opportunity_id': self.id
        }
        action['domain'] = [('crm_lead_id', '=', self.id), ('state', 'in', ['draft', 'sent'])]
        agreement = self.mapped('order_ids').filtered(lambda l: l.state in ('draft', 'sent'))
        if len(agreement) == 1:
            action['views'] = [(self.env.ref('agreement_blueminds.partner_agreement_form_view').id, 'form')]
            action['res_id'] = agreement.id
        return action

    # @api.constrains('agreement_id')
    # def _check_agreement(self):
    #     if self.agreement_id:
    #         if self.agreement_id.anexo == False:
    #             raise ValidationError(_('El contrato: %s No permite anexos' %
    #                                     (self.agreement_id.name)))

class CrmtLine(models.Model):
    _name = "crm.line"
    _description = "CRM Lines"

    product_id = fields.Many2one("product.product", string="Servicio")
    name = fields.Char(string="Description", required=True)
    crm_id = fields.Many2one("crm.lead", string="CRM", ondelete="cascade")
    partner_id = fields.Many2one(related="crm_id.partner_id", string="Partner", required=False, copy=True)
    qty = fields.Float(string="Cantidad", default="1")
    uom_id = fields.Many2one("uom.uom", string="Unidad de Medida", required=True)
    location = fields.Char('Ubicación')
    price = fields.Float('Precio')
    partner_contact_id = fields.Many2one("res.partner", string="Dirección", copy=True,
        domain="[('type', '=', 'delivery'), ('parent_id', '=', partner_id)]")
    partner_invoice_id = fields.Many2one("res.partner", string="Dirección Facturación", copy=True,
        domain="[('type', '=', 'invoice'), ('parent_id', '=', partner_id)]")

    @api.onchange("product_id")
    def _onchange_product_id(self):
        self.name = self.product_id.name
        self.uom_id = self.product_id.uom_id.id

class CrmLine(models.Model):
    _name = 'crm.rline'
    _description = "CRM Linea Real"

    product_id = fields.Many2one("product.product", string="Servicio real")
    name = fields.Char(string="Description", required=True)
    crm_id = fields.Many2one("crm.lead", string="CRM", ondelete="cascade", domain="[('agreement_count', '=', False)]")
    partner_id = fields.Many2one(related="crm_id.partner_id", string="Partner", required=False, copy=True)
    qty = fields.Float(string="Cantidad", default="1")
    uom_id = fields.Many2one("uom.uom", string="Unidad de Medida", required=True)
    location = fields.Char('Ubicación')
    price = fields.Float('Precio')
    partner_contact_id = fields.Many2one("res.partner", string="Dirección", copy=True, domain="[('parent_id', '=', False)]")
    partner_invoice_id = fields.Many2one("res.partner", string="Dirección Facturación", copy=True, domain="[('parent_id', '=', False)]")

    @api.onchange("product_id")
    def _onchange_product_id(self):
        self.name = self.product_id.name
        self.uom_id = self.product_id.uom_id.id