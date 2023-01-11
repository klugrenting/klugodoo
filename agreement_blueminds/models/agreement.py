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


class Agreement(models.Model):
    _name = 'agreement'
    _description = 'Agreement'
    _inherit = ["mail.thread", "mail.activity.mixin", "mail.render.mixin"]
    _AGREEMENT_FIELDS = ['content', 'dynamic_content']

    def _get_default_parties(self):
        deftext = """
        <h3>Company Information</h3>
        <p>
        ${object.company_id.partner_id.name or ''}.<br>
        ${object.company_id.partner_id.street or ''} <br>
        ${object.company_id.partner_id.state_id.code or ''}
        ${object.company_id.partner_id.zip or ''}
        ${object.company_id.partner_id.city or ''}<br>
        ${object.company_id.partner_id.country_id.name or ''}.<br><br>
        Represented by <b>${object.company_contact_id.name or ''}.</b>
        </p>
        <p></p>
        <h3>Partner Information</h3>
        <p>
        ${object.partner_id.name or ''}.<br>
        ${object.partner_id.street or ''} <br>
        ${object.partner_id.state_id.code or ''}
        ${object.partner_id.zip or ''} ${object.partner_id.city or ''}<br>
        ${object.partner_id.country_id.name or ''}.<br><br>
        Represented by <b>${object.partner_contact_id.name or ''}.</b>
        </p>
        """
        return deftext

    # @api.model
    # def name_get(self):
    #     result = []
    #     for record in self:
    #         if record.anexo == False:
    #             name = '%s - %s' % (record.name, 'No permite anexos')
    #         else:
    #             name = record.name
    #         result.append((record.id, name))
    #     return result

    # Used for Kanban grouped_by view
    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        stage_ids = self.env["agreement.stage"].search(
            [('stage_type', '=', 'agreement')])
        return stage_ids

    @api.depends('content')
    def _compute_dynamic_content(self):
        for record in self:
            if record.content:
                copy_depends_values = {'lang': 'es_CL'}
                context = record._context.get('lang')
                agreement_id = record.with_context(lang=context)
                try:
                    mail_values = agreement_id.with_context(template_preview_lang=context).generate_email(
                        [record.id], record._AGREEMENT_FIELDS)
                    mail_values = mail_values[record.id]
                    record._set_mail_attributes(values=mail_values)
                except UserError as user_error:
                    _logger.info(user_error.args[0])
                    record._set_mail_attributes()
                finally:
                    for key, value in copy_depends_values.items():
                        record[key] = value
            else:
                record.dynamic_content = ''

    def _set_mail_attributes(self, values=None):
        field_value = values.get('content', False) if values else self['content']
        self['dynamic_content'] = field_value

    def generate_email(self, res_ids, fields):
        """Generates an email from the template for given the given model based on
        records given by res_ids.

        :param res_id: id of the record to use for rendering the template (model
                       is taken from template definition)
        :returns: a dict containing all relevant fields for creating a new
                  mail.mail entry, with one extra key ``attachments``, in the
                  format [(report_name, data)] where data is base64 encoded.
        """
        self.ensure_one()
        multi_mode = True
        if isinstance(res_ids, int):
            res_ids = [res_ids]
            multi_mode = False

        results = dict()
        for lang, (template, template_res_ids) in self.lassify_per_lang(res_ids).items():
            template.render_model = 'agreement'
            for field in fields:
                generated_field_values = template._render_field(
                    field, template_res_ids,
                    options={'render_safe': False},
                    post_process=True
                )
                for res_id, field_value in generated_field_values.items():
                    results.setdefault(res_id, dict())[field] = field_value
            # update values for all res_ids
            for res_id in template_res_ids:
                values = results[res_id]
                if values.get('content'):
                    values['dynamic_content'] = tools.html_sanitize(values['content'])

        return multi_mode and results or results[res_ids[0]]

    def lassify_per_lang(self, res_ids, engine='inline_template'):
        """ Given some record ids, return for computed each lang a contextualized
        template and its subset of res_ids.

        :param list res_ids: list of ids of records (all belonging to same model
          defined by self.render_model)
        :param string engine: inline_template, qweb, or qweb_view;

        :return dict: {lang: (template with lang=lang_code if specific lang computed
          or template, res_ids targeted by that language}
        """
        self.ensure_one()

        if self.env.context.get('template_preview_lang'):
            lang_to_res_ids = {self.env.context['template_preview_lang']: res_ids}
        else:
            lang_to_res_ids = {}
            for res_id, lang in self._render_lang(res_ids, engine=engine).items():
                lang_to_res_ids.setdefault(lang, []).append(res_id)

        return dict(
            (lang, (self.with_context(lang=lang) if lang else self, lang_res_ids))
            for lang, lang_res_ids in lang_to_res_ids.items()
        )

    # compute the dynamic content for mako expression
    def _compute_dynamic_description(self):
        MailTemplates = self.env["mail.template"]
        for agreement in self:
            lang = agreement.partner_id.lang or "en_US"
            description = MailTemplates.with_context(lang=lang)._render_template(
                agreement.description, "agreement", agreement.id
            )
            agreement.dynamic_description = description

    def _compute_dynamic_parties(self):
        MailTemplates = self.env["mail.template"]
        for agreement in self:
            lang = agreement.partner_id.lang or "en_US"
            parties = MailTemplates.with_context(
                lang=lang
            )._render_template(
                agreement.parties, "agreement", agreement.id
            )
            agreement.dynamic_parties = parties

    def _compute_dynamic_special_terms(self):
        MailTemplates = self.env["mail.template"]
        for agreement in self:
            lang = agreement.partner_id.lang or "en_US"
            special_terms = MailTemplates.with_context(lang=lang)._render_template(
                agreement.special_terms, "agreement", agreement.id
            )
            agreement.dynamic_special_terms = special_terms

    def _compute_invoice_count(self):
        base_domain = [
            ('agreement_id', 'in', self.ids),
            ('state', 'not in', ('draft', 'cancel'))]
        aio = self.env['account.move']
        out_rg_res = aio.read_group(
            base_domain + [('type', 'in', ('out_invoice', 'out_refund'))],
            ['agreement_id'], ['agreement_id'])
        out_data = dict(
            [(x['agreement_id'][0], x['agreement_id_count']) for x in out_rg_res])
        in_rg_res = aio.read_group(
            base_domain + [('type', 'in', ('in_invoice', 'in_refund'))],
            ['agreement_id'], ['agreement_id'])
        in_data = dict(
            [(x['agreement_id'][0], x['agreement_id_count']) for x in in_rg_res])
        for agreement in self:
            agreement.out_invoice_count = out_data.get(agreement.id, 0)
            agreement.in_invoice_count = in_data.get(agreement.id, 0)

    def _compute_sale_count(self):
        rg_res = self.env['sale.order'].read_group(
            [
                ('agreement_id', 'in', self.ids),
                ('state', 'not in', ('draft', 'sent', 'cancel')),
            ],
            ['agreement_id'], ['agreement_id'])
        mapped_data = dict(
            [(x['agreement_id'][0], x['agreement_id_count']) for x in rg_res])
        for agreement in self:
            agreement.sale_count = mapped_data.get(agreement.id, 0)

    code = fields.Char(
        string="Reference",
        required=True,
        default=lambda self: _("New"),
        track_visibility="onchange",
        copy=False,
        help="ID used for internal contract tracking.")
    name = fields.Char(string='Name', required=False, track_visibility='onchange')
    partner_id = fields.Many2one(
        'res.partner', string='Partner', ondelete='restrict',
        domain=[('parent_id', '=', False)], track_visibility='onchange')
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env['res.company']._company_default_get())
    is_template = fields.Boolean(
        string="Is a Template?",
        default=False,
        copy=False,
        help="Set if the agreement is a template. "
        "Template agreements don't require a partner."
    )
    agreement_type_id = fields.Many2one(
        'agreement.type',
        string="Document Type",
        help="Select the type of document",
    )
    domain = fields.Selection(
        '_domain_selection', string='Domain', default='sale',
        track_visibility='onchange')
    active = fields.Boolean(
        string="Active",
        default=True,
        help="If unchecked, it will allow you to hide the agreement without "
             "removing it.")
    signature_date = fields.Date(track_visibility='onchange')
    start_date = fields.Date(
        string="Start Date", default=fields.Date.context_today,
        track_visibility="onchange",
        help="When the agreement starts.")
    end_date = fields.Date(
        string="End Date", default=time.strftime('9999-01-01'),
        track_visibility="onchange",
        help="When the agreement ends.")
    version = fields.Integer(
        string="Version",
        default=1,
        copy=False,
        help="The versions are used to keep track of document history and "
             "previous versions can be referenced.")
    revision = fields.Integer(
        string="Revision",
        default=0,
        copy=False,
        help="The revision will increase with every save event.")
    num_dias = fields.Integer(
        string="Days without charge",
        default=0,
        copy=False)
    anexo = fields.Boolean(string='May have attachments', default=True,
                           help="Check if you do not want this contract to have annexes.")
    readonly_anexo = fields.Boolean(string='No Edit', default=False)
    description = fields.Text(
        string="Internal Notes",
        track_visibility="onchange",
        help="Description of the agreement")
    dynamic_description = fields.Text(
        compute="_compute_dynamic_description",
        string="Dynamic Description",
        help="Compute dynamic description")
    # template_agreement_id = fields.Many2one(
    #     "agreement", store=True,
    #     string="Template") # domain="[('fecha_termino_date', '>=', hoy_date), ('type_contrib', '=', type_contrib_partner), ('is_template', '=', 'True'), ('payment_method_domain', '=', payment_method), ('type_partner_domain', '=', type_partner)]",
    late_fine = fields.Float("Fine per day late")
    color = fields.Integer(string="Color")
    company_signed_date = fields.Date(
        string="Signed on",
        track_visibility="onchange",
        help="Date the contract was signed by Company.")
    partner_signed_date = fields.Date(
        string="Signed on (Partner)",
        track_visibility="onchange",
        help="Date the contract was signed by the Partner.")
    term = fields.Integer(
        string="Term (Months)",
        track_visibility="onchange",
        help="Number of months this agreement/contract is in effect with the "
             "partner.")
    expiration_notice = fields.Integer(
        string="Exp. Notice (Days)",
        track_visibility="onchange",
        help="Number of Days before expiration to be notified.")
    change_notice = fields.Integer(
        string="Change Notice (Days)",
        track_visibility="onchange",
        help="Number of Days to be notified before changes.")
    special_terms = fields.Text(
        string="Special Terms",
        track_visibility="onchange",
        help="Any terms that you have agreed to and want to track on the "
             "agreement/contract.")
    dynamic_special_terms = fields.Text(
        compute="_compute_dynamic_special_terms",
        string="Dynamic Special Terms",
        help="Compute dynamic special terms")
    increase_type_id = fields.Many2one(
        "agreement.increasetype",
        string="Increase Type",
        track_visibility="onchange",
        help="The amount that certain rates may increase.")
    termination_requested = fields.Date(
        string="Termination Requested Date",
        track_visibility="onchange",
        help="Date that a request for termination was received.")
    termination_date = fields.Date(
        string="Termination Date",
        track_visibility="onchange",
        help="Date that the contract was terminated.")
    reviewed_date = fields.Date(
        string="Reviewed Date", track_visibility="onchange")
    reviewed_user_id = fields.Many2one(
        "res.users", string="Reviewed By", track_visibility="onchange")
    approved_date = fields.Date(
        string="Approved Date", track_visibility="onchange")
    approved_user_id = fields.Many2one(
        "res.users", string="Approved By", track_visibility="onchange")
    currency_id = fields.Many2one("res.currency", string="Currency")
    partner_contact_id = fields.Many2one(
        "res.partner",
        string="Partner Contact",
        copy=True,
        domain="[('type', '=', 'delivery')]",
        help="The primary partner contact (If Applicable).")
    partner_contact_phone = fields.Char(
        related="partner_contact_id.phone", string="Partner Phone")
    partner_contact_email = fields.Char(
        related="partner_contact_id.email", string="Partner Email")
    company_contact_id = fields.Many2one(
        "res.partner",
        string="Company Contact",
        copy=True,
        help="The primary contact in the company.")
    company_contact_phone = fields.Char(
        related="company_contact_id.phone", string="Phone")
    company_contact_email = fields.Char(
        related="company_contact_id.email", string="Email")
    use_parties_content = fields.Boolean(
        string="Use parties content",
        help="Use custom content for parties")
    company_partner_id = fields.Many2one(
        related="company_id.partner_id", string="Company's Partner")
    repres_legal1 = fields.Many2one(
        "res.users", string="Primer Representante Legal", track_visibility="onchange")
    repres_legal2 = fields.Many2one(
        "res.users", string="Segundo Representante Legal", track_visibility="onchange")
    repres_legal3 = fields.Many2one(
        "res.users", string="Tercer Representante Legal", track_visibility="onchange")
    ceder = fields.Boolean(string='Assign/Transfer contract', default=False,
                           help="Check if you do not want this contract to have the possibility of assigning/transferring the contract (contract version).")
    req_firma = fields.Boolean(string='¿Requires Signature?', default=True,
                               help="Check if you want this contract to require a signature or not and if it is external or from Maihue")
    template_child = fields.Boolean(string='Annex Template', default=False,
                                    help="Check if this template is contract or annex")
    expiration_date = fields.Date(
        string="Expiration date", track_visibility="onchange", help="Date on which the template expires",
        default='9999-12-31')
    # payment_period = fields.Many2one(
    #     "agreement.payment.period", required=False, #domain="[('id', 'in', payment_period_domain)]",
    #     string="Payment Periodicity")
    # payment_method = fields.Many2one(
    #     "agreement.payment.method", required=False, #domain="[('id', 'in', payment_method_domain)]",
    #     string="Payment method")
    payment_term_id = fields.Many2one('account.payment.term', string='Payment deadline')
    modelo_id = fields.Many2one('agreement.modelos', string='Modelo Contrato')
    # payment_method_domain = fields.Many2many('agreement.payment.method', 'method_agreement_rel', 'method_id',
    #                                          'agreement_id',
    #                                          string='Payment method')
    # payment_period_domain = fields.Many2many('agreement.payment.period', 'period_agreement_rel', 'period_id',
    #                                          'agreement_id',
    #                                          string='Payment Periodicity')
    # payment_deadline_domain = fields.Many2many('account.payment.term', 'deadline_agreement_rel', 'deadline_id',
    #                                            'agreement_id',
    #                                            string='Payment deadline')
    team_id_domain = fields.Many2many('crm.team', 'team_agreement_rel', 'team_id',
                                      'agreement_id',
                                      string='Sales team')
    # exception_team_id_domain = fields.Many2many('crm.team', 'team_exc_agreement_rel', 'team_id',
    #                                   'agreement_id',
    #                                   string='Exception Sales team')
    initemplate_date = fields.Date(
        string="Template start date", track_visibility="onchange")
    # type_partner = fields.Many2one(
    #     "agreement.type.partner", required=False,
    #     string="Type of contract", help="type of client (house, company, HORECA - INTERNAL, HORECA - SELF-BOTTLING)")
    parent_template_id = fields.Many2one(
        "agreement",
        string="Father Template",
        help="Father Template"
    )
    req_orden = fields.Boolean(string='Allows purchase order or prior contract order?', default=False,
                               help="Check if you want this contract to require a purchase order or prior contract order")
    fecha_termino_date = fields.Date(
        string="End date", track_visibility="onchange")
    fecha_cobro = fields.Date(
        string="Collection Date", track_visibility="onchange", invisible=True)
    fecha_activacion = fields.Date(
        string="Fecha de Firma", track_visibility="onchange")
    test_day_domain = fields.Many2many('agreement.test.day', 'test_day_rel', 'test_day_id',
                                       'agreement_id', invisible=True,
                                       string='Days without charge')
    product_domain = fields.Many2many('product.product', 'product_domain_rel', 'product_id', 'agreement_id',
                                      string='Services')
    zona_domain = fields.Many2many('zona.comercial', 'agreement_zona_domain', 'zona_id',
                                   'agreement_id',
                                   string='Shopping area',
                                   track_visibility='onchange')
    test_day = fields.Many2one(
        "agreement.test.day", required=False,
        string="Days without charge")
    revisado_check = fields.Boolean(string='Revisado', default=False)
    fecha_repres1 = fields.Date(
        string="Fecha Firma R1", track_visibility="onchange")
    fecha_repres2 = fields.Date(
        string="Fecha Firma R2", track_visibility="onchange")
    fecha_repres3 = fields.Date(
        string="Fecha Firma R3", track_visibility="onchange")
    fecha_envio1 = fields.Date(
        string="Fecha Envio R1", track_visibility="onchange")
    fecha_envio2 = fields.Date(
        string="Fecha Envio R2", track_visibility="onchange")
    fecha_envio3 = fields.Date(
        string="Fecha Envio R3", track_visibility="onchange")
    type_contrib_partner = fields.Many2one(
        "agreement.type.contrib", string='Type of taxpayer', required=False, related='partner_id.type_contrib')
    type_contrib = fields.Many2one(
        "agreement.type.contrib", required=False,
        string="Type of taxpayer", domain=[("code", "not in", ['ig', 'na', 'igp'])])
    # type_contrib_domain = fields.Many2many('agreement.type.contrib', 'agreement_type_contrib_rel', 'tupe_domain_id',
    #                                        'agreement_id',
    #                                        string='Type of taxpayer')
    pricelist_id = fields.Many2one('product.pricelist', 'Rate', readonly=False)
    agreement_discount = fields.Many2one(
        "agreement.discount", required=False,
        string="Discount")
    # partner_domain = fields.Many2many('res.partner', 'partner_agreement_rel', 'partner_id', 'agreement_id',
    #                                   string='Clients')
    # type_partner_domain = fields.Many2many('agreement.type.partner', 'agreement_type_partner_rel', 'type_id',
    #                                        'agreement_id',
    #                                        string='Type of contract')
    # pricelist_id_domain = fields.Many2many('product.pricelist', 'agreement_pricelist_rel', 'pricelist_id',
    #                                        'agreement_id',
    #                                        string='Rate')
    signed_document_ids = fields.One2many(
        "agreement.signed.extra", "agreement_id", string="Extra Files", copy=True)
    tax_id = fields.Many2one('account.tax', string='Taxes',
                             domain=[('type_tax_use', '=', 'sale'), ('active', '=', True)], default=1)
    # tax_id_domain = fields.Many2many('account.tax', 'agreement_taxes_rel', 'taxes_id',
    #                                        'agreement_id',
    #                                        string='Impuestos')
    gestor_id = fields.Many2one('res.users', string='Managed by')
    team_id = fields.Many2one('crm.team', 'Sales team', readonly=False)
    pre_liquid = fields.Boolean('Pre-settlement')
    incidencia = fields.Boolean('Contractual Incidence', default=False)
    prueba_aprob = fields.Boolean('Proof without Signature', default=False)
    perm_act = fields.Boolean('Allows partial activation', default=False)
    hoy_date = fields.Date(
        string="today", default=fields.Date.context_today)
    parties = fields.Html(
        string="Parties",
        track_visibility="onchange",
        default=_get_default_parties,
        help="Parties of the agreement")
    dynamic_parties = fields.Html(
        compute="_compute_dynamic_parties",
        string="Dynamic Parties",
        help="Compute dynamic parties")
    agreement_subtype_id = fields.Many2one(
        "agreement.subtype",
        string="Agreement Sub-type",
        track_visibility="onchange",
        help="Select the sub-type of this agreement. Sub-Types are related to "
             "agreement types.")
    product_ids = fields.Many2many(
        "product.template", string="Products & Services")
    assigned_user_id = fields.Many2one(
        "res.users",
        string="Assigned To",
        track_visibility="onchange",
        help="Select the user who manages this agreement.")
    company_signed_user_id = fields.Many2one(
        "res.users",
        string="Signed By",
        track_visibility="onchange",
        help="The user at our company who authorized/signed the agreement or "
             "contract.")
    partner_signed_user_id = fields.Many2one(
        "res.partner",
        string="Firmante R1",
        track_visibility="onchange",
        help="Contact on the account that signed the agreement/contract.")
    parent_agreement_id = fields.Many2one(
        "agreement",
        string="Parent Agreement",
        help="Link this agreement to a parent agreement. For example if this "
             "agreement is an amendment to another agreement. This list will "
             "only show other agreements related to the same account.")
    renewal_type_id = fields.Many2one(
        "agreement.renewaltype",
        string="Renewal Type",
        track_visibility="onchange",
        help="Describes what happens after the contract expires.")
    recital_ids = fields.One2many(
        "agreement.recital", "agreement_id", string="Recitals", copy=True)
    sections_ids = fields.One2many(
        "agreement.section", "agreement_id", string="Sections", copy=True)
    clauses_ids = fields.One2many(
        "agreement.clause", "agreement_id", string="Clauses")
    appendix_ids = fields.One2many(
        "agreement.appendix", "agreement_id", string="Appendices", copy=True)
    previous_version_agreements_ids = fields.One2many(
        "agreement",
        "parent_agreement_id",
        string="Previous Versions",
        copy=False,
        domain=[("active", "=", False)])
    child_agreements_ids = fields.One2many(
        "agreement",
        "parent_agreement_id",
        string="Child Agreements",
        copy=False,
        domain=[("active", "=", True)])
    line_ids = fields.One2many(
        "agreement.line",
        "agreement_id",
        string="Contract Lines",
        copy=False)
    state = fields.Selection(
        [("draft", "Draft"), ("active", "Active"), ("inactive", "Inactive")],
        default="draft",
        track_visibility="always")
    notification_address_id = fields.Many2one(
        "res.partner",
        string="Notification Address",
        help="The address to send notificaitons to, if different from "
             "customer address.(Address Type = Other)")
    signed_contract_filename = fields.Char(string="Filename")
    signed_contract = fields.Binary(
        string="Signed Document", track_visibility="always")

    # Dynamic field editor
    field_domain = fields.Char(string='Field Expression',
                               default='[["active", "=", True]]')
    default_value = fields.Char(
        string="Default Value",
        help="Optional value to use if the target field is empty.")
    copyvalue = fields.Char(
        string="Placeholder Expression",
        help="""Final placeholder expression, to be copy-pasted in the desired
             template field.""")
    document_ids = fields.One2many(
        "agreement.document", "agreement_id", string="Documentos Extra", copy=True)
    # rentals_ids = fields.One2many(
    #     "rentals.line",
    #     "agreement_id",
    #     string="Rentals Orders",
    #     copy=False)
    invoicing_ids = fields.One2many(
        "invoice.line",
        "agreement_id",
        string="Invoices",
        copy=False)
    # document
    title = fields.Char(
        string="Title",
        help="The title is displayed on the PDF." "The name is not.")
    content = fields.Html(string="Content", render_engine='qweb', translate=True, sanitize=False)
    dynamic_content = fields.Html(
        compute='_compute_dynamic_content',
        string="Dynamic Content",
        sanitize=False,
        help="compute dynamic Content")
    company_signed_user_dos_id = fields.Many2one(
        "res.users",
        string="Firmante R2",
        track_visibility="onchange",
        help="Segundo Usuario que autorizo/firmo el acuerdo o contrato")
    company_signed_user_tres_id = fields.Many2one(
        "res.users",
        string="Firmante R3",
        track_visibility="onchange",
        help="Tercera Usuario que autorizo/firmo el acuerdo o contrato")
    extra_ids = fields.One2many(
        "agreement.extra", "agreement_id", string="Documentos Oficiales", copy=True)
    referidor_id = fields.Many2one('res.partner', string='referrer', domain=[("parent_id", "=", False)])
    partner_invoice_id = fields.Many2one(
        "res.partner",
        string="Representante Legal",
        copy=True,
        track_visibility='onchange',
        domain="[('parent_id', '=', partner_id)]")
    vat_invoice_partner = fields.Char(related='partner_invoice_id.vat')
    state_firm1 = fields.Selection(selection=[
        ('M', 'Firmado'),
        ('T', 'Pend. Firma'),
        ('S', 'Firma en Revisión')], string='Estado Firma R1')
    periodicidad = fields.Selection(selection=[
        ('M', 'Mensual'),
        ('S', 'Semanal'),
        ('D', 'Diario')], default_value='M', string='Periodicidad de Pago')
    state_firm2 = fields.Selection(selection=[
        ('M', 'Firmado'),
        ('T', 'Pend. Firma'),
        ('S', 'Firma en Revisión')], string='Estado Firma R2')
    state_firm3 = fields.Selection(selection=[
        ('M', 'Firmado'),
        ('T', 'Pend. Firma'),
        ('S', 'Firma en Revisión')], string='Estado Firma R3')
    state_firm4 = fields.Selection(selection=[
        ('M', 'Firmado'),
        ('T', 'Pend. Firma'),
        ('S', 'Firma en Revisión')], string='Estado Firma')
    agreement_penalty1 = fields.Many2one(
        "agreement.penalty", required=False,
        string="Servicio adicional 1", readonly=False)
    agreement_penalty2 = fields.Many2one(
        "agreement.penalty", required=False,
        string="Servicio adicional 2", readonly=False)
    agreement_penalty3 = fields.Many2one(
        "agreement.penalty", required=False,
        string="Servicio adicional 3", readonly=False)
    agreement_penalty4 = fields.Many2one(
        "agreement.penalty", required=False,
        string="Servicio adicional 4", readonly=False)
    agreement_penalty5 = fields.Many2one(
        "agreement.penalty", required=False,
        string="Servicio adicional 5", readonly=False)
    charge_extra_ids = fields.One2many(
        "agreement.extra.charges", "agreement_id", string="Extra Charges", copy=True)
    total_service = fields.Float('Total', store=True, compute='_compute_total_lines_contract')
    product_instalation = fields.Many2one(
        "product.product", readonly=True, track_visibility='onchange', string="Product Installation")
    # template_domain = fields.Many2many('agreement', 'template_agreement_rel', 'parent_id',
    #                                          'agreement_id', compute='_compute_template_agreement_id',
    #                                          string='Domain for contract')
    stage_id = fields.Many2one(
        "agreement.stage",
        string="Stage", default=1,
        group_expand="_read_group_stage_ids",
        help="Select the current stage of the agreement.",
        track_visibility="onchange",
        index=True)
    invoice_ids = fields.One2many(
        'account.move', 'agreement_id', string='Invoices', readonly=True)
    out_invoice_count = fields.Integer(
        compute='_compute_invoice_count', string='# of Customer Invoices')
    in_invoice_count = fields.Integer(
        compute='_compute_invoice_count', string='# of Vendor Bills')
    sale_id = fields.Many2one('sale.order', string='Sales Order')
    analytic_account_id = fields.Many2one(
        'account.analytic.account',
        'Analytic Account',
        copy=False)
    crm_lead_id = fields.Many2one('crm.lead', "CRM Oportunity", help="Crm for which we are creating a contract",
                                  required=False)
    # sale_ids = fields.One2many(
    #     'sale.order', 'agreement_id', string='Sale Orders', readonly=True)
    # sale_count = fields.Integer(
    #     compute='_compute_sale_count', string='# of Sale Orders')
    canal_id = fields.Many2one(
        'crm.canal',
        string='Channel')
    subcanal_id = fields.Many2one(
        'crm.subcanal',
        string='Sub Channel')
    reference_ids = fields.One2many(
        "l10n_cl.account.invoice.reference", "agreement_id")
    agreement_l10ncl = fields.Many2one(
        "agreement.l10ncl", required=False,
        string="Master Required Documents")
    l10ncl_domain = fields.Many2many('agreement.l10ncl', 'l10ncl_rel', 'l10ncl_id',
                                     'agreement_id',
                                     string='Required Documents')
    state_ajust = fields.Selection(selection=[
        ('P', 'Pendiente Realizar'),
        ('R', 'Realizado'),
        ('C', 'Cancelado')], string='Status Setting')
    date_ajuste = fields.Date(
        string="Date Adjustment of Conditions",
        track_visibility="onchange",
        help="Date Adjustment of Conditions")
    inicio_fecha_alquiler = fields.Date("De")
    fin_fecha_alquiler = fields.Date("Hasta")
    # check_exception = fields.Boolean(related='crm_lead_id.check_exception')
    # exception = fields.Boolean(related='crm_lead_id.exception')
    # canal_id = fields.Many2one(
    #     'crm.canal',
    #     string='Canal')
    # subcanal_id = fields.Many2one(
    #     'crm.subcanal',
    #     string='Sub Canal')
    # job_id = fields.Many2one('hr.job', 'Job that Approves Exception')

    @api.model
    def create(self, vals):
        tiene_seq = False
        if 'start_date' in self.env.context:
            vals['journal_id'] = self.env.context.get('journal_id')
        if 'stage_id' in vals:
            if vals['stage_id'] == 7:
                self.write({'fecha_activacion': datetime.now().date(), 'approved_user_id': self._uid, 'approved_date': datetime.now().date()})
                #maintenance = self.agree_maintenance()
            if vals['stage_id'] == 9 or vals['stage_id'] == 12:
                cancelled = self.agree_cancelled()
        if not vals.get('stage_id'):
            vals["stage_id"] = self.env['agreement.stage'].search([
            ('name', '=', 'BORRADOR'),
        ]).id
            #self.env.ref("agreement_stage_new").id
        if vals.get('is_template'):
            vals['name'] = vals['name']
            tiene_seq = True
        # if not vals.get('is_template'):
        #     if 'parent_agreement_id' in vals:
        #         if vals['parent_agreement_id']:
        #             agreement = self.env['agreement'].search([('id', '=', vals['parent_agreement_id'])])
        #             numa = agreement.name.split("-")
        #             vals['name'] = str(numa[0]) + '-1'
        #             no_existe_a = False
        #             while (no_existe_a == False):
        #                 existe_a = self.env['agreement'].search([('name', '=', vals['name'])])
        #                 if existe_a:
        #                     num = vals['name'].split("-")
        #                     prox = int(num[-1]) + 1
        #                     vals['name'] = str(agreement.name) + '-' + str(prox)
        #                 if not existe_a:
        #                     no_existe_a = True
        #             tiene_seq = True
        if not tiene_seq:
            seq = str(self.env['ir.sequence'].next_by_code('agreement_seq'))
            vals['name'] = str(seq) + '-0'
            no_existe = False
            while (no_existe == False):
                existe = self.env['agreement'].search([('name', '=', vals['name'])])
                if existe:
                    num = vals['name'].split("-")
                    prox = int(num[-1]) + 1
                    vals['name'] = str(seq) + '-' + str(prox)
                if not existe:
                    no_existe = True
            partner = self.env['res.partner'].browse(vals['partner_id'])
            vals['name'] = str(vals['name']) + '/' + str(partner.name)

        return super(Agreement, self).create(vals)

    def write(self, vals):
        if 'partner_id' in vals:
            if self.crm_lead_id:
                crm = self.env['crm.lead'].search([('id', '=', self.crm_lead_id.id)])
                crm.write({'partner_id': vals.get('partner_id')})
        # if 'payment_method' in vals:
        #     rentals = self.env['sale.order'].search([('agreement_id', '=', self.id), ('state', '=', 'draft')])
        #     if rentals:
        #         for rental in rentals:
        #             rental.write({'payment_method': vals['payment_method']})
        # if not self.is_template:
        #     if self.template_agreement_id:
        #         template_agreement = self.env['agreement'].browse(self.template_agreement_id.id)
                # if template_agreement.extra_ids:
                #     new = template_agreement.extra_ids.copy()
                #     new.write({'agreement_id': vals['template_agreement_id']})
        res = super(Agreement, self).write(vals)
        if self.reference_ids:
            for ref in self.reference_ids:
                if ref.active_s == True:
                    orders = self.env['sale.order'].search(
                        [('agreement_id', '=', self.id), ('state', '=', 'draft'),
                         ('inicio_fecha_alquiler', '<=', ref.date_init)])
                    for orden in orders:
                        orden.write({'reference_oc': ref.id})
                    if not orders:
                        orders = self.env['sale.order'].search(
                            [('agreement_id', '=', self.id), ('state', '=', 'draft')])
                        for orden in orders:
                            orden.write({'reference_oc': False})
        if not self.reference_ids:
            orders = self.env['sale.order'].search(
                [('agreement_id', '=', self.id), ('state', '=', 'draft')])
            orders.write({'reference_oc': False})
        return res

    def pre_prueba(self):
        # if self.check_exception == True:
        #     if self.exception == True:
                self.write({'stage_id': 2})
        #     else:
        #         raise UserError(_(
        #             'Disculpe, No se puede iniciar el contrato, \n \n  Porque no ha sido aprobado para el uso de excepción de plantilla'))
        # else:
        #     self.write({'stage_id': 2})

    def borrador(self):
        stage = self.env['agreement.stage'].search([
            ('name', '=', 'BORRADOR'),
        ])
        self.write({'stage_id': stage.id})
        for line in self.line_ids:
            line.write({'state': 'draft'})

    def pend_firma(self):
        self.write({'stage_id': 3})

    def firmado(self):
        stage = self.env['agreement.stage'].search([
            ('name', '=', 'FIRMADO'),
        ])
        self.write({'stage_id': stage.id})
        for line in self.line_ids:
            line.write({'state': 'firm'})

    def en_pro(self):
        stage = self.env['agreement.stage'].search([
            ('name', '=', 'EN PROGRESO'),
        ])
        self.write({'stage_id': stage.id})
        for line in self.line_ids:
            line.write({'state': 'in_progress'})

    def vencido(self):
        stage = self.env['agreement.stage'].search([
            ('name', '=', 'VENCIDO'),
        ])
        self.write({'stage_id': stage.id})
        for line in self.line_ids:
            line.write({'state': 'ven'})
        return True

    def revisado(self):
        self.write({'stage_id': 6, 'reviewed_user_id': self.write_uid.id, 'approved_user_id': self.write_uid.id,
                    'reviewed_date': datetime.now(), 'approved_date': datetime.now()})
        for line in self.line_ids:
            line.write({'state': 'revisado'})

    def cerrado(self):
        stage = self.env['agreement.stage'].search([
            ('name', '=', 'CERRADO'),
        ])
        self.write({'stage_id': stage.id})
        for line in self.line_ids:
            line.write({'state': 'close'})

    def soli_cancelar(self):
        self.write({'stage_id': 10})
        for line in self.line_ids:
            line.write({'state': 'sol_can'})

    def pro_cancelar(self):
        self.write({'stage_id': 11})
        for line in self.line_ids:
            line.write({'state': 'pro_can'})

    def cancelado(self):
        self.write({'stage_id': 12})
        for line in self.line_ids:
            line.write({'state': 'cancelado'})

    def sol_baja(self):
        self.write({'stage_id': 14})
        for line in self.line_ids:
            line.write({'state': 'sol_baja'})

    def pro_baja(self):
        self.write({'stage_id': 15})
        for line in self.line_ids:
            line.write({'state': 'proceso'})

    def no_vigente(self):
        self.write({'stage_id': 16})
        for line in self.line_ids:
            line.write({'state': 'prueba'})

    # Create New Version Button
    def create_new_version(self, vals):
        for rec in self:
            if not rec.state == "draft":
                # Make sure status is draft
                rec.state = "draft"
            default_vals = {
                "name": "{} - OLD VERSION".format(rec.name),
                "active": False,
                "parent_agreement_id": rec.id,
            }
            # Make a current copy and mark it as old
            rec.copy(default=default_vals)
            # Increment the Version
            rec.version = rec.version + 1
        # Reset revision to 0 since it's a new version
        vals["revision"] = 0
        return super(Agreement, self).write(vals)

    def create_new_agreement(self):
        default_vals = {
            "name": "NEW",
            "active": True,
            "version": 1,
            "revision": 0,
            "state": "draft",
            "stage_id": 1,#self.env.ref("agreement_legal.agreement_stage_new").id,
        }
        res = self.copy(default=default_vals)
        res.sections_ids.mapped('clauses_ids').write({'agreement_id': res.id})
        return {
            "res_model": "agreement",
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "view_type": "form",
            "res_id": res.id,
        }

    @api.model
    def _domain_selection(self):
        return [
            ('sale', _('Sale')),
            ('purchase', _('Purchase')),
            ]

    @api.onchange('modelo_id')
    def onchange_modelo_id(self):
        self.content = self.modelo_id.content

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        arrs = []
        today = datetime.now()
        domain = [('is_template', '=', True), ('expiration_date', '>=', today)]
        # if self.parent_agreement_id:
        #     domain.append(('template_child', '=', True))
        # if self.template_agreement_id.team_id_domain:
        #     domain.append(('team_id_domain', 'in', self.team_id.ids))
        # if self.template_agreement_id.partner_domain:
        #     domain.append(('partner_domain', 'in', self.partner_id.id))
        if self.type_contrib_partner:
            domain.append(('type_contrib', '=', self.type_contrib_partner.id))
        templates_ids = self.search(domain)
        if templates_ids:
            for x in templates_ids:
                arrs.append(x.id)
        if self.partner_id:
            self.type_contrib = self.partner_id.type_contrib.id
            self.notification_address_id = ''
            for i in self.line_ids:
                i.partner_con_id = ''
                i.partner_contact_id = ''

        if arrs:
            res = {}
            res['domain'] = {'template_agreement_id': [('id', 'in', arrs)]}
            return res

    @api.onchange('template_child')
    def onchange_template_child(self):
        res = {}
        if not self.template_child:
            type_contrib = self.env['agreement.type.contrib'].search([('code', '!=', 'ig')])
            payment_period = self.env['agreement.payment.period'].search([('code', '!=', 'ig')])
            payment_method = self.env['agreement.payment.method'].search([('code', '!=', 'ig')])
            payment_deadline = self.env['account.payment.term'].search([('name', '!=', 'Igual al Padre')])
            res['domain'] = {
                'payment_period_domain': [('id', 'in', payment_period.ids)],
                'payment_method_domain': [('id', 'in', payment_method.ids)],
                'payment_deadline_domain': [('id', 'in', payment_deadline.ids)],
                # 'type_contrib': [('id', 'in', self.template_agreement_id.type_contrib_domain.ids)],
                # 'type_partner': [('id', 'in', self.template_agreement_id.type_partner_domain.ids)],
                # 'pricelist_id': [('id', 'in', self.template_agreement_id.pricelist_id_domain.ids)],
                'type_contrib_domain': [('id', 'in', type_contrib.ids)]}
        else:
            res['domain'] = {
                'payment_period_domain': [],
                'payment_method_domain': [],
                'payment_deadline_domain': [],
                # 'type_contrib': [('id', 'in', self.template_agreement_id.type_contrib_domain.ids)],
                # 'type_partner': [('id', 'in', self.template_agreement_id.type_partner_domain.ids)],
                # 'pricelist_id': [('id', 'in', self.template_agreement_id.pricelist_id_domain.ids)],
                'type_contrib_domain': []}
        return res

    @api.onchange('agreement_discount')
    def onchange_agreement_discount(self):
        today = date.today()
        discount_ids = self.env['agreement.discount'].search(
            [('fecha_inicio', '<=', today), ('fecha_fin', '>=', today)])
        domain = {'agreement_discount': [('id', 'in', discount_ids.ids)]}
        return {'domain': domain}

    @api.onchange("field_domain", "default_value")
    def onchange_copyvalue(self):
        self.copyvalue = False
        if self.field_domain:
            string_list = self.field_domain.split(",")
            if string_list:
                field_domain = string_list[0][3:-1]
                self.copyvalue = "${{object.{} or {}}}".format(
                    field_domain,
                    self.default_value or "''")

    @api.onchange('test_day', 'start_date')
    def _onchange_num_dias(self):
        self.fecha_cobro = self.start_date + relativedelta(days=int(self.test_day.code))

    @api.onchange('agreement_type_id')
    def agreement_type_change(self):
        if self.agreement_type_id and self.agreement_type_id.domain:
            self.domain = self.agreement_type_id.domain

    @api.onchange('revisado_check')
    def onchange_revisado_check(self):
        if self.revisado_check:
            self.reviewed_user_id = self._uid
            self.reviewed_date = datetime.now().date()

    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        """Always assign a value for code because is required"""
        default = dict(default or {})
        if default.get('code', False):
            return super().copy(default)
        default.setdefault('code', _("%s (copy)") % (self.code))
        return super().copy(default)

    def agree_sale(self):
        if not self.inicio_fecha_alquiler or not self.fin_fecha_alquiler:
            raise UserError(_(
                'Disculpe, No se puede iniciar la orden de venta, \n \n  Porque no ha la fecha inicio y la fecha fin'))
        months = (
        "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre",
        "Diciembre")
        descuento = False
        # if self.payment_period.code == 'M':
        #     time_periodicy = 1
        # if self.payment_period.code == 'T':
        #     time_periodicy = 3
        # if self.payment_period.code == 'S':
        #     time_periodicy = 6
        # if self.payment_period.code == 'AM' or self.payment_period.code == 'A' or self.payment_period.code == 'AD':
        #     time_periodicy = 12
        # if self.payment_period.code == 'AM' or self.payment_period.code == 'A':
        #     descuento = 2
        # valid = self.fecha_cobro + relativedelta(days=1)
        #rental orders
        for line in self.line_ids:
            total_multas = 0.0
            total_tags = 0.0
            total_kms = 0.0
            vehicle = self.env['fleet.vehicle'].sudo().search([('product_id', '=', line.product_principal.id)])
            primero = True
            today = datetime.now().date() + relativedelta(days=1) # self.fecha_cobro
            numeracion = 1
            proporcional = True
            es_primero = 1
            # period_day = line.fecha_cobro.day
            # period_mes_ = line.fecha_cobro.month
            # period_anio = line.fecha_cobro.year
            # period_date = str(line.fecha_cobro.year) + '-' + str(line.fecha_cobro.month).zfill(2) + '-' + '01'
            # period_date = datetime.strptime(period_date, '%Y-%m-%d')
            # ultimo_de_mes = calendar.monthrange(period_date.year, period_date.month)
            # fin_mes = str(period_date.year) + '-' + str(period_date.month).zfill(2) + '-' + str(
            #     ultimo_de_mes[1])
            month = months[self.inicio_fecha_alquiler.month - 1]
            order_vals = {
                'partner_id': self.partner_id.id,
                'opportunity_id': self.crm_lead_id.id,
                #'agreement_type_id': self.agreement_type_id.id,
                'agreement_id': self.id,
                'date_order': datetime.now(),
                'validity_date': self.end_date,
                'user_id': self.crm_lead_id.user_id.id,
                'origin': self.crm_lead_id.name,
                'partner_dir_id': line.partner_contact_id.id,
                'is_rental_order': True,
                #'tipo_rental_order': 'mensualidad',
                'agreement_id': self.id,
                'agreement_line_ids': line.id,
                'payment_term_id': self.payment_term_id.id,
                #'payment_method': self.payment_method.id,
                #'payment_deadline': self.payment_deadline.id,
                'inicio_fecha_alquiler': self.inicio_fecha_alquiler,
                'fin_fecha_alquiler': self.fin_fecha_alquiler,
                'fecha_estimada': today,
                'fecha_fact_prog': today,
                'next_action_date': today,
                'periodo_mes': str(month) + '/' + str(self.fin_fecha_alquiler.year)
            }
            order = self.env['sale.order'].create(order_vals)
            # name_order = str(order.name) + ' ' + str(today) + ' - ' + str(numeracion)
            # order.write({'name': name_order})
            # today = today + relativedelta(months=time_periodicy)
            order_line = {
                'order_id': order.id,
                'product_id': line.product_id.id,
                'name': 'Renting ' + str(month) + ' ' + str(line.product_principal.name),
                'price_unit': line.price,
                'tax_id': [self.tax_id.id],
            }
            order_line = self.env['sale.order.line'].create(order_line)
            # Nota de Cobro
            init_anterior = self.inicio_fecha_alquiler - relativedelta(months=1)
            ultimo_de_mes = calendar.monthrange(init_anterior.year, init_anterior.month)
            end_anterior = str(init_anterior.year) + '-' + str(init_anterior.month).zfill(2) + '-' + str(ultimo_de_mes[1])
            km_end_anterior = 0
            promedio_km = 0
            co2_e = 0
            co2_a = 0
            odometer_anterior = self.env['fleet.vehicle.odometer'].sudo().search([
                        ('vehicle_id', '=', vehicle.id),
                        ('date', '>=', init_anterior),
                        ('date', '<=', end_anterior),
                        ('tag_ids', 'in', [2])], order='id asc')
            if odometer_anterior:
                end = odometer_anterior[0].value
                for mes in odometer_mes:
                    km_end_anterior =abs(end - mes.value)
            odometer_mes = self.env['fleet.vehicle.odometer'].sudo().search([
                ('vehicle_id', '=', vehicle.id),
                ('date', '>=', self.inicio_fecha_alquiler),
                ('date', '<=', self.fin_fecha_alquiler),
                ('tag_ids', 'in', [2])], order='id asc')
            if odometer_mes:
                init = odometer_mes[0].value
                for mes in odometer_mes:
                    total_kms =abs(init - mes.value)
                if total_kms > 0:
                    promedio_km = total_kms / (float(line.place_contract) - 1)
            if vehicle.co2 > 0 and km_end_anterior > 0:
                co2_e = float(vehicle.co2) * km_end_anterior / 1000
            if vehicle.co2 > 0 and total_kms > 0:
                co2_a = total_kms * float(vehicle.co2) / 1000
            nota_line = {
                'order_id': order.id,
                'name': line.product_principal.id,
                'code': line.product_principal.patente,
                'km_anterior': km_end_anterior,
                'km_acum': total_kms,
                'km_mes': promedio_km,
                'mes_contract': int(line.place_contract) -1,
                'contract': line.place_contract,
                'co2_e': co2_e,
                'co2_a': co2_a,
            }
            self.env['sale.order.detail'].create(nota_line)
            # Detalle Nota de Cobro
            odometer_det = self.env['fleet.vehicle.odometer'].sudo().search([
                ('vehicle_id', '=', vehicle.id),
                ('date', '>=', self.inicio_fecha_alquiler),
                ('date', '<=', self.fin_fecha_alquiler),
                ('tag_ids', 'in', [1])])
            for detalle in odometer_det:
                nota_line = {
                    'order_id': order.id,
                    'name': line.product_principal.id,
                    'date': detalle.date,
                    'concesion': detalle.concession,
                    'description': detalle.description,
                    'category': detalle.category,
                    #'km': 1,
                    'tarifa': detalle.amount,
                }
                self.env['sale.order.detaill'].create(nota_line)
            # kms Extra
            total = 0.0
            if total_kms > line.km_mes:
                total = total_kms - line.km_mes
                total = total * line.price_km_adi
            if total > 0:
                kms_line = {
                    'order_id': order.id,
                    'product_id': line.product_id.id,
                    'name': "KM'S Extra " + str(line.product_principal.patente) + " '" + str(month) + "' " + str(
                        line.price_km_adi) + str(line.currency_id_km.symbol) + " por kilometro adicional " + str(
                        total_kms) + "KM sobre " + str(
                        line.km_mes),
                    'price_unit': total,
                    'tax_id': [self.tax_id.id],
                }
                self.env['sale.order.line'].create(kms_line)
            # tags
            odometer_tag = self.env['fleet.vehicle.odometer'].sudo().search([
                ('vehicle_id', '=', vehicle.id),
                ('date', '>=', self.inicio_fecha_alquiler),
                ('date', '<=', self.fin_fecha_alquiler),
                ('tag_ids', 'in', [1])])
            if odometer_tag:
                for tag in odometer_tag:
                    total_tags = float(total_tags) + float(tag.amount)
                tags_line = {
                    'order_id': order.id,
                    'product_id': line.product_id.id,
                    'name': 'TAG ' + str(month) + ' ' + str(line.product_principal.patente),
                    'price_unit': total_tags,
                    'tax_id': [self.tax_id.id],
                }
                self.env['sale.order.line'].create(tags_line)
            # multas
            odometer_multas = self.env['fleet.vehicle.odometer'].sudo().search([
                ('vehicle_id', '=', vehicle.id),
                ('date', '>=', self.inicio_fecha_alquiler),
                ('date', '<=', self.fin_fecha_alquiler),
                ('tag_ids', 'in', [7])])
            if odometer_multas:
                for multa in odometer_multas:
                    total_multas = float(total_multas) + float(multa.amount)
                multas_line = {
                    'order_id': order.id,
                    'product_id': line.product_id.id,
                    'name': 'Multas ' + str(month) + ' ' + str(line.product_principal.patente),
                    'price_unit': total_multas,
                    'tax_id': [self.tax_id.id],
                }
                self.env['sale.order.line'].create(multas_line)
        return True

    def orden_compra(self):
        if self.reference_ids:
            for ref in self.reference_ids:
                if ref.active_s == True:
                    orders = self.sale_ids.search(
                        [('agreement_id', '=', self.id), ('state', '=', 'draft'),
                         ('inicio_fecha_alquiler', '<=', ref.date_init)])
                    for orden in orders:
                        orden.write({'reference_oc': ref.id})

    def agree_cancelled(self):
        orders = self.env['sale.order'].search([('agreement_id', '=', self.id)])
        for rental_order in orders:
            rental_order.write({'state': 'cancel'})

class AgreementPaymentMethod(models.Model):
    _name = 'agreement.payment.method'

    name = fields.Char(required=True, string='Nombre')
    code = fields.Char(required=True, string='Codigo')

class AgreementPaymentIntermediary(models.Model):
    _name = 'agreement.payment.intermediary'

    code = fields.Char(string='Codigo')
    name = fields.Char(required=True, string='Nombre')
    payment_method = fields.Many2one('agreement.payment.method', string="Metodo de Pago", domain=[('code', '!=', 'ig')])

class AgreementPaymentPeriod(models.Model):
    _name = 'agreement.payment.period'

    name = fields.Char(required=True, string='Nombre')
    code = fields.Char(required=True, string='Codigo')

class AgreementTypePartner(models.Model):
    _name = 'agreement.type.partner'

    name = fields.Char(required=True, string='Nombre')
    code = fields.Char(required=True, string='Codigo')

class AgreementTestDay(models.Model):
    _name = "agreement.test.day"
    _description = "Agreement Tests Day"

    name = fields.Char(required=True, string='Nombre')
    code = fields.Char(required=True, string='Dias')

class AgreementTypeContrib(models.Model):
    _name = "agreement.type.contrib"
    _description = "Agreement Type of taxpayer"

    name = fields.Char(required=True, string='Type')
    code = fields.Char(required=True, string='Code')

class AgreementSignedExtra(models.Model):
    _name = "agreement.signed.extra"
    _description = "Agreement Extra Document"
    _order = "sequence"

    sequence = fields.Integer(string="Secuencia", default=10)
    name = fields.Char(string="Nombre Archivo")
    type_extra = fields.Many2one(
        "type.signed.extra",
        string="Type",
        track_visibility="onchange")
    valid = fields.Boolean('Validado', default=False)
    document = fields.Binary(
        string="Documento", track_visibility="always")
    agreement_id = fields.Many2one(
        comodel_name='agreement', string='Agreement', ondelete='cascade',
        track_visibility='onchange', readonly=False, invisible=True)
    approved_date = fields.Date(
        string="Approved Date", track_visibility="onchange")
    approved_user_id = fields.Many2one(
        "res.users", string="Approved By", track_visibility="onchange")

class TypeSignedExtra(models.Model):
    _name = "type.signed.extra"
    _description = "Type Extra Documento"

    name = fields.Char(string="Type")

class AgreementExtraCharges(models.Model):
    _name = 'agreement.extra.charges'
    _rec_name = 'product_id'

    product_id = fields.Many2one('product.template', string='Producto')
    description = fields.Char('Descripcion')
    currency_id = fields.Many2one('res.currency', 'Moneda')
    pricelist_id = fields.Many2one('product.pricelist', 'Lista de Precios', readonly=False, invisible=True)
    zona_comercial = fields.Many2one('zona.comercial', string='Zona')
    price = fields.Float('Precio', readonly=False, track_visibility='onchange')
    #qty = fields.Float('Cantidad')
    #product_uom = fields.Many2one('uom.uom', 'Unidad de Medida')
    #time_spent = fields.Float('Tiempo/Horas', precision_digits=2)
    #charge = fields.Boolean('Cobrar', default=False)
    agreement_id = fields.Many2one(
        "agreement",
        string="Parent Agreement",)
    is_template = fields.Boolean(string='is_template', related='agreement_id.is_template', track_visibility='onchange')

    @api.onchange("product_id")
    def _onchange_product_id(self):
        self.description = self.product_id.name
        self.uom_id = self.product_id.uom_id.id

class TypeDocumentExtra(models.Model):
    _name = "type.document.extra"
    _description = "Type Extra"

    name = fields.Char(string="Type")

class CrmCanal(models.Model):
    _name = 'crm.canal'

    name = fields.Char(required=True, string='Nombre')

class CrmSubCanal(models.Model):
    _name = 'crm.subcanal'

    name = fields.Char(required=True, string='Nombre')
    canal_id = fields.Many2one(
        'crm.canal',
        string='Canal')
