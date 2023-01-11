# © 2022 (Jamie Escalante <jescalante@blueminds.cl>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta
from datetime import datetime
import calendar
from odoo.exceptions import UserError, ValidationError


class AgreementLine(models.Model):
    _name = "agreement.line"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Agreement Lines"

    def name_get(self):
        result = []
        for group in self:
            if group.is_template:
                name = group.name
            else:
                name = group.name + ' ' + group.product_id.name
            result.append((group.id, name))
        return result

    product_id = fields.Many2one('product.product')
    product_domain = fields.Many2many(related='agreement_id.product_domain', string='Services')
    name = fields.Char(
        string="Line",
        required=False, readonly=True, track_visibility='onchange',
        states={'draft': [('readonly', False)],'pre': [('readonly', False)], 'vali': [('readonly', False)], 'revisado': [('readonly', False)]})
    agreement_id = fields.Many2one(
        "agreement",
        string="Agreement",
        ondelete="cascade",
        track_visibility='onchange',
        states={'draft': [('readonly', False)],'pre': [('readonly', False)], 'vali': [('readonly', False)], 'revisado': [('readonly', False)]})
    qty = fields.Float(string="Quantity", default=1,
        states={'draft': [('readonly', False)],'pre': [('readonly', False)], 'vali': [('readonly', False)], 'revisado': [('readonly', False)]})
    uom_id = fields.Many2one(
        "uom.uom",
        string="Unit of Measure",
        required=False,
        track_visibility='onchange',
        states={'draft': [('readonly', False)],'pre': [('readonly', False)], 'vali': [('readonly', False)], 'revisado': [('readonly', False)]})
    location = fields.Char('Location',
        track_visibility='onchange',
        states={'draft': [('readonly', False)],'pre': [('readonly', False)], 'vali': [('readonly', False)], 'revisado': [('readonly', False)]})
    price_km_adi = fields.Float('Precio por KM Adicional', readonly=False,
        track_visibility='onchange')
    price = fields.Float('Monthly Price', readonly=False,
        track_visibility='onchange')
    price_instalacion = fields.Float('installation price', readonly=False, track_visibility='onchange')
    partner_id = fields.Many2one(
        related="agreement_id.partner_id",
        string="Client",
        required=False,
        copy=True,
        track_visibility='onchange',
        help="The customer or vendor this agreement is related to.")
    partner_vat = fields.Char(
        related="partner_id.vat", track_visibility='onchange', string="Rut", readonly=True)
    partner_contact_id = fields.Many2one(
        "res.partner",
        string="Installation Address",
        copy=True,
        track_visibility='onchange',
        domain="[('type', '=', 'delivery'), ('parent_id', '=', partner_id)]",
        help="The primary partner contact (If Applicable).",
        #states={'draft': [('readonly', False)],'pre': [('readonly', False)], 'vali': [('readonly', False)], 'revisado': [('readonly', False)]}
    )
    partner_invoice_id = fields.Many2one(
        "res.partner",
        string="Contact Billing",
        copy=True,
        track_visibility='onchange',
        #domain="[('type', '=', 'invoice'), ('parent_id', '=', partner_id)]",
        #states={'draft': [('readonly', False)],'pre': [('readonly', False)], 'vali': [('readonly', False)], 'revisado': [('readonly', False)]}
    )
    valor = fields.Float("Inst Value", store=True, digits='Account',
        track_visibility='onchange',
        #states={'draft': [('readonly', False)],'pre': [('readonly', False)], 'vali': [('readonly', False)], 'revisado': [('readonly', False)]}
                         )
    is_template = fields.Boolean(string='is_template', related='agreement_id.is_template', track_visibility='onchange')
    agreement_line_keys = fields.Many2one("agreement.line.keys", string="Serial number", copy=True,
        track_visibility='onchange',
        #states={'draft': [('readonly', False)],'pre': [('readonly', False)], 'vali': [('readonly', False)], 'revisado': [('readonly', False)]}
                                          )
    # key_contact_id = fields.Many2one(
    #     "res.partner",
    #     string="Contacto Clave",
    #     copy=True,
    #     domain="[('parent_id', '=', partner_id)]")
    # user_install_id = fields.Many2one('res.users', string='Instalador Prueba', ondelete='cascade')
    # user_finish_id = fields.Many2one('res.users', string='Instalador Definitivo', ondelete='cascade')
    # charge_maintence = fields.Many2one('res.users', string='Encargado Mantenciones', ondelete='cascade')
    # date_test = fields.Date(string='Inicio Prueba', default=fields.Date.context_today)
    # date_finish = fields.Date(string='Definitiva', default=fields.Date.context_today)
    mantenedor = fields.Many2one(
        "res.users", string="Maintainer", track_visibility="onchange",
        #states={'draft': [('readonly', False)],'pre': [('readonly', False)], 'vali': [('readonly', False)], 'revisado': [('readonly', False)]}
    )
    product_principal = fields.Many2one(
        "product.product",
        string="Product", track_visibility='onchange',
        #states={'draft': [('readonly', False)],'pre': [('readonly', False)], 'vali': [('readonly', False)], 'revisado': [('readonly', False)]}
    )
    partner_con_id = fields.Many2one(
        "res.partner",
        string="Contact Service",
        copy=True,
        track_visibility='onchange',
        #domain="[('type', '=', 'contact'), ('parent_id', '=', partner_id)]", readonly=True,
        #states={'draft': [('readonly', False)],'pre': [('readonly', False)], 'vali': [('readonly', False)], 'revisado': [('readonly', False)]}
    )
    start_date = fields.Date(
        string="Test Start", #default=fields.Date.context_today,
        track_visibility="onchange",
        help="Test start date",
        #states={'draft': [('readonly', False)],'pre': [('readonly', False)], 'vali': [('readonly', False)], 'revisado': [('readonly', False)]}
    )
    test_day = fields.Many2one(
        "agreement.test.day", required=False, track_visibility='onchange',
        string="Days without charge",
        #states={'draft': [('readonly', False)],'pre': [('readonly', False)], 'vali': [('readonly', False)], 'revisado': [('readonly', False)]}
    )
    state = fields.Selection(
        [("draft", "Borrador"), ("firm", "Firmado"), ("in_progress", "En Progreso"), ("ven", "Vencido"),
         ("close", "Cerrado")],
        default="draft",
        track_visibility="always")
    invoicing_line_ids = fields.One2many(
        "invoice.line",
        "agreement_line_ids",
        string="Invoices", readonly=True,
        track_visibility='onchange',
        copy=False)
    # tickets_line_ids = fields.One2many(
    #     "helpdesk.ticket",
    #     "agreement_line_ids",
    #     string="Tickets", readonly=True,
    #     track_visibility='onchange',
    #     copy=False)
    date_end_contract = fields.Date(
        string="Discharge date", readonly=False,
        track_visibility="onchange",
        help="Date of cancellation of the contract line")
    pricelist_inst = fields.Many2one(related='agreement_id.pricelist_id', string='Installation Rate')
    pricelist_mens = fields.Many2one(related='agreement_id.pricelist_id', string='Monthly rate')
    pricelist_inst_domain = fields.Many2many('product.pricelist', 'agreement_pricelist_inst', 'pricelist_id',
                                           'agreement_line_id',
                                           string='Installation Rate', readonly=True,
                                           track_visibility='onchange',
        #states={'draft': [('readonly', False)],'pre': [('readonly', False)], 'vali': [('readonly', False)], 'revisado': [('readonly', False)]}
                                             )
    pricelist_mens_domain = fields.Many2many('product.pricelist', 'agreement_pricelist_mens', 'pricelist_id',
                                           'agreement_line_id',
                                           string='Monthly rate', readonly=True,
                                           track_visibility='onchange',
        states={'draft': [('readonly', False)],'pre': [('readonly', False)], 'vali': [('readonly', False)], 'revisado': [('readonly', False)]}
                                             )
    date_inst = fields.Date(
        string="Test Installation Date", track_visibility="onchange", readonly=True,
        states={'draft': [('readonly', False)],'pre': [('readonly', False)], 'vali': [('readonly', False)], 'revisado': [('readonly', False)]}
    )
    state_inst = fields.Char(
        string="Status Installation Test",
        required=False, readonly=True,
        track_visibility='onchange',
        states={'draft': [('readonly', False)],'pre': [('readonly', False)], 'vali': [('readonly', False)], 'revisado': [('readonly', False)]}
    )
    state_desinst = fields.Char(
        string="Uninstall Status",
        required=False, readonly=True,
        track_visibility='onchange',
        states={'draft': [('readonly', False)],'pre': [('readonly', False)], 'vali': [('readonly', False)], 'revisado': [('readonly', False)]}
    )
    date_def = fields.Date(
        string="Final Installation Date", track_visibility="onchange", readonly=True,
        states={'draft': [('readonly', False)],'pre': [('readonly', False)], 'vali': [('readonly', False)], 'revisado': [('readonly', False)]}
    )
    date_desinst = fields.Date(
        string="Uninstall Date", track_visibility="onchange", readonly=True,
        states={'draft': [('readonly', False)],'pre': [('readonly', False)], 'vali': [('readonly', False)], 'revisado': [('readonly', False)]}
    )
    state_def = fields.Char(
        string="Final Installation Status",
        required=False, readonly=True,
        track_visibility='onchange',
        states={'draft': [('readonly', False)],'pre': [('readonly', False)], 'vali': [('readonly', False)], 'revisado': [('readonly', False)]}
    )
    type_line = fields.Many2one('agreement.line.type', string='Line Type', readonly=True,
                                      track_visibility='onchange',
                                      states={'draft': [('readonly', False)], 'pre': [('readonly', False)],
                                              'vali': [('readonly', False)], 'revisado': [('readonly', False)]}
                                      )
    zona_com = fields.Many2one('maihue.zone', string="Commercial zone", readonly=True, track_visibility='onchange',
                               states={'draft': [('readonly', False)],'pre': [('readonly', False)], 'vali': [('readonly', False)], 'revisado': [('readonly', False)]}
                               )
    zona_comercial = fields.Many2one('zona.comercial', string='Commercial zone', readonly=True, track_visibility='onchange',
                               states={'draft': [('readonly', False)],'pre': [('readonly', False)], 'vali': [('readonly', False)], 'revisado': [('readonly', False)]}
                                     )
    zona_mantencion = fields.Many2one('sector.mantencion', string='Maintenance Sector', readonly=True, track_visibility='onchange',
                               states={'draft': [('readonly', False)],'pre': [('readonly', False)], 'vali': [('readonly', False)], 'revisado': [('readonly', False)]}
                                      )
    zona_man = fields.Many2one('maihue.zone', string="Maintenance area", readonly=True, track_visibility='onchange',
                               states={'draft': [('readonly', False)],'pre': [('readonly', False)], 'vali': [('readonly', False)], 'revisado': [('readonly', False)]}
                               )
    comisiona_id = fields.Many2one('res.users', string='Responsible Commission', readonly=True, track_visibility='onchange',
                                         states={'draft': [('readonly', False)],'pre': [('readonly', False)], 'vali': [('readonly', False)], 'revisado': [('readonly', False)]}
                                   )
    date_comision_pag = fields.Date(
        string="Commission Payment Date", track_visibility="onchange", readonly=False,
        #states={'draft': [('readonly', False)],'pre': [('readonly', False)], 'vali': [('readonly', False)], 'revisado': [('readonly', False)]}
    )
    state_comision = fields.Char('State Commission', readonly=False, track_visibility='onchange',
                           #states={'draft': [('readonly', False)],'pre': [('readonly', False)], 'vali': [('readonly', False)], 'revisado': [('readonly', False)]}
                                 )
    insta_prueba_id = fields.Many2one('res.users', string='Test Installer', readonly=True, track_visibility='onchange',
                                   states={'draft': [('readonly', False)],'pre': [('readonly', False)], 'vali': [('readonly', False)], 'revisado': [('readonly', False)]}
                                      )
    desinst_id = fields.Many2one('res.users', string='Uninstaller', readonly=True, track_visibility='onchange',
                                   states={'draft': [('readonly', False)],'pre': [('readonly', False)], 'vali': [('readonly', False)], 'revisado': [('readonly', False)]}
                                 )
    insta_def_id = fields.Many2one('res.users', string='Ultimate Installer', readonly=True, track_visibility='onchange',
                                   states={'draft': [('readonly', False)],'pre': [('readonly', False)], 'vali': [('readonly', False)], 'revisado': [('readonly', False)]}
                                   )
    cost_center = fields.Char(string="Cost center",
        required=False, readonly=True,
        states={'draft': [('readonly', False)],'pre': [('readonly', False)], 'vali': [('readonly', False)], 'revisado': [('readonly', False)]}
                                  )
    asesor_id = fields.Many2one('hr.employee', string='Advised By',
        required=False, readonly=True, track_visibility='onchange',
        states={'draft': [('readonly', False)],'pre': [('readonly', False)], 'vali': [('readonly', False)], 'revisado': [('readonly', False)]}
                                )
    gestor_id = fields.Many2one(related="agreement_id.gestor_id", string='Managed by',
        required=False, readonly=True, track_visibility='onchange',
        states={'draft': [('readonly', False)],'pre': [('readonly', False)], 'vali': [('readonly', False)], 'revisado': [('readonly', False)]}
                                )
    team_id = fields.Many2one(related="agreement_id.team_id", string='Sales team',
        required=False, readonly=True, track_visibility='onchange',
        states={'draft': [('readonly', False)],'pre': [('readonly', False)], 'vali': [('readonly', False)], 'revisado': [('readonly', False)]}
                              )
    fecha_cobro = fields.Date(
        string="Fecha Cobro", track_visibility="onchange", invisible=True)
    general_msj = fields.Text('General Message', readonly=True, track_visibility='onchange',
        states={'draft': [('readonly', False)],'pre': [('readonly', False)], 'vali': [('readonly', False)], 'revisado': [('readonly', False)]}
                              )
    means_ids = fields.Many2many('means', string="Resources", track_visibility='onchange')
    capabilities_ids = fields.Many2many('capabilities', string="Capabilities", track_visibility='onchange')
    zona_domain = fields.Many2many('zona.comercial', 'agreement_zona_rel', 'zona_id',
                                             'agreement_line_id',
                                             string='Commercial zone', readonly=True,
                                             track_visibility='onchange',
                                             states={'draft': [('readonly', False)], 'pre': [('readonly', False)],
                                                     'vali': [('readonly', False)], 'revisado': [('readonly', False)]}
                                   )
    date_entrega = fields.Date(
        string="Fecha de Entrega")
    incidencia = fields.Boolean('Contractual Incidence', default=False)
    comuna_id = fields.Many2one(related='partner_contact_id.commune', string='Commune', required=False)
    referidor_id = fields.Many2one(related="agreement_id.referidor_id", string='Referrer')
    currency_id_inst = fields.Many2one("res.currency", string="currency", default=168)
    currency_id_km = fields.Many2one("res.currency", string="currency", default=168)
    currency_id_men = fields.Many2one("res.currency", string="currency", default=168)
    reason_dis = fields.Selection([
        ('b_mai', 'BAJA MAIHUE'),
        ('b_cli', 'BAJA CLIENTE'),
        ('tras', 'TRASPASO'),
        ('up', 'UPGRADE'),
        ('down', 'DOWNGRADE')], 'Reason for Discharge',
        copy=False, readonly=False)
    description_dis = fields.Text('Description for Discharge', readonly=False)
    fut_line_rel = fields.Many2one("agreement.line", string="Fut Related Line")
    fut_state_rele = fields.Selection(related='fut_line_rel.state', string="Fut Related Line",)
    fut_motivo_rel = fields.Selection([
        ('b_mai', 'BAJA MAIHUE'),
        ('b_cli', 'BAJA CLIENTE'),
        ('tras', 'TRASPASO'),
        ('up', 'UPGRADE'),
        ('down', 'DOWNGRADE')], 'Fut Reason Related',
        copy=False, readonly=False)
    fut_description_rel = fields.Text('Fut Related Description')
    pass_line_rel = fields.Many2one("agreement.line", string="Pass Related Line")
    pass_state_rele = fields.Selection(related='pass_line_rel.state', string="Pass State Related Line",)
    pass_motivo_rel = fields.Selection([
        ('b_mai', 'BAJA MAIHUE'),
        ('b_cli', 'BAJA CLIENTE'),
        ('tras', 'TRASPASO'),
        ('up', 'UPGRADE'),
        ('down', 'DOWNGRADE')], 'Pass Reason Related',
        copy=False, readonly=False)
    pass_description_rel = fields.Text('Pass Related Description')
    sale_line_id = fields.Many2one('sale.order.line',
                                   string='Sales Order Line')
    maintenance_id = fields.Many2one('product.maintenance_m', string='Maintenance')
    maintenance = fields.Char(string='Mantención')
    agreement_penalty = fields.Many2one(
        "agreement.penalty", required=False,
        string="Penalty", readonly=False,
        states={'pre': [('readonly', False)]})
    discounts_line_ids = fields.One2many('agreement.discount', 'agreement_id', string='Discounts', copy=True,
                                         auto_join=True)
    signed_contract_filename = fields.Char(string="Nombre Archivo")
    signed_contract = fields.Binary(
        string="Acta de Entrega", track_visibility="always")
    deducible = fields.Float('Deducible (UF)')
    place_contract = fields.Integer('Plazo Contrato (Meses)')
    km_salida = fields.Integer('Kilometraje de Salida')
    km_devo = fields.Integer('Kilometraje de Devolución')
    km_mes = fields.Integer('Kilometros Mensuales Contratados')
    fecha_inicio = fields.Date('Fecha Inicio')
    fecha_fin = fields.Date('Fecha Final')
    warranty = fields.Selection(
        selection=[
            ('tarjeta', 'Tarjeta Bancaria'),
            ('trans', 'Transferencia')],
        string='Forma de Pago Garantia',
        required=True)
    estanque_salida = fields.Selection(
        selection=[
            ('full', 'Full'),
            ('medio', 'Medio'),
            ('bajo', 'Bajo')],
        string='Estanque de Salida',
        required=True)
    estanque_devo = fields.Selection(
        selection=[
            ('full', 'Full'),
            ('medio', 'Medio'),
            ('bajo', 'Bajo')],
        string='Estanque de Devolución',
        required=False)

    # @api.onchange('test_day', 'start_date')
    # def _onchange_num_dias(self):
    #     self.fecha_cobro = self.start_date + relativedelta(days=int(self.test_day.code))

    @api.onchange('pass_line_rel')
    def _onchange_pass_line_rel(self):
        if self.pass_line_rel:
            self.pass_motivo_rel = self.pass_line_rel.reason_dis
            self.pass_description_rel = self.pass_line_rel.description_dis

    def agree_revisado(self):
        self.write({'state': 'revisado'})

    def agree_baja(self):
        self.write({'state': 'sol_baja'})
        self.agreement_id.write({'stage_id': 14})

    def agree_baja_pro(self):
        self.write({'state': 'proceso'})
        self.agreement_id.write({'stage_id': 15})

    def agree_no_vigente(self):
        if self.fut_line_rel:
            if self.fut_line_rel.state == 'act':
                existentes = self.env['sale.order'].search([('agreement_line_ids', '=', self.id)])
                if existentes:
                    if len(existentes) > 1:
                        for exi in existentes:
                            exi.unlink()
            else:
                raise UserError(_('Lo Siento, El estado de la linea futura debe ser Activo'))
        #     self.line_rel.write({'pass_line_rel': self.id, 'pass_motivo_rel': self.motivo_rel, 'pass_description_rel': self.description_rel})
        self.write({'state': 'no_vigente'})
        self.agreement_id.write({'stage_id': 16})

    def agree_cerrar(self):
        self.write({'state': 'cerrado'})

    # @api.onchange("test_day")
    # def _onchange_test_day(self):
    #     res = {}
    #     res['domain'] = {
    #         'test_day': [('id', 'in', self.agreement_id.template_agreement_id.test_day_domain.ids)]}
    #     return res

    def unlink(self):
        user = self.env['res.users'].browse(self.env.uid)
        raise UserError(_('Sorry, you are not authorized to delete contract lines'))

    def agree_maintenance(self):
        # if self.line_rel:
        #     self.line_rel.write({'state_rel': 'no_vi'})
        months = (
        "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre",
        "Diciembre")
        # instalacion
        for line in self:
            todayI = datetime.now().date() + relativedelta(days=1)
            ultimo_de_mes = calendar.monthrange(line.start_date.year, line.start_date.month)
            fin_mes = str(line.start_date.year) + '-' + str(line.start_date.month).zfill(2) + '-' + str(ultimo_de_mes[1])
            month = months[line.start_date.month - 1]
            order_valsI = {
                        'partner_id': self.agreement_id.partner_id.id,
                        'opportunity_id': self.agreement_id.crm_lead_id.id,
                        'agreement_type_id': self.agreement_id.agreement_type_id.id,
                        'agreement_id': self.agreement_id.id,
                        'date_order': datetime.now(),
                        'validity_date': self.agreement_id.end_date,
                        'user_id': self.agreement_id.crm_lead_id.user_id.id,
                        'origin': self.agreement_id.crm_lead_id.name,
                        'partner_dir_id': line.partner_contact_id.id,
                        'is_rental_order': True,
                        'tipo_rental_order': 'instalacion',
                        'agreement_id': self.agreement_id.id,
                        'agreement_line_ids': line.id,
                        'payment_period': self.agreement_id.payment_period.id,
                        'payment_method': self.agreement_id.payment_method.id,
                        'payment_term_id': self.agreement_id.payment_term_id.id,
                        'inicio_fecha_alquiler': line.start_date,
                        'fin_fecha_alquiler': line.start_date,
                        'fecha_fact_prog': todayI,
                        'fecha_estimada': todayI,
                        'periodo_mes': str(month) + '/' + str(line.start_date.year),
                        'state': 'draft', #'sale',
                        'currency_id': self.agreement_id.currency_id.id,
                        'pricelist_id': line.pricelist_inst.id,
                        'reference_ids': [self.agreement_id.reference_ids.id],
                        'agreement_currency_id': line.currency_id_inst.id,
                    }
            orderI = self.env['sale.order'].create(order_valsI)
            name_orderI = str(orderI.name) + ' Contrato: ' + str(self.name) + ' - ' + str(todayI)
            orderI.write({'name': name_orderI})
            precio_inst = round(line.price_instalacion,4) + 0.001
            order_lineI = {
                'order_id': orderI.id,
                'product_id': line.product_id.id,
                'name': str(line.product_id.name_key) + '/' + str(line.maintenance_id.name) + '/' + str(
                    line.currency_id_inst.name) + '' + str(precio_inst) + '+iva',
                'price_unit': line.price_instalacion,
                'tax_id': [self.agreement_id.tax_id.id],
            }
            order_lineI = self.env['sale.order.line'].create(order_lineI)
        # Rentals
        meses = 0
        meses2 = 0
        time_periodicy = 0
        descuento = False
        if self.agreement_id.payment_period.code == 'M':
            time_periodicy = 1
        if self.agreement_id.payment_period.code == 'T':
            time_periodicy = 3
        if self.agreement_id.payment_period.code == 'S':
            time_periodicy = 6
        if self.agreement_id.payment_period.code == 'AM' or self.agreement_id.payment_period.code == 'A' or self.agreement_id.payment_period.code == 'AD':
            time_periodicy = 12
        if self.agreement_id.payment_period.code == 'AM' or self.agreement_id.payment_period.code == 'A':
            descuento = 2
        if self.agreement_id.agreement_discount:
            ultimo_de_mesD = calendar.monthrange(line.fecha_cobro.year,
                                                 line.fecha_cobro.month)
            fin_mes = str(line.fecha_cobro.year) + '-' + str(line.fecha_cobro.month).zfill(
                2) + '-' + str(ultimo_de_mesD[1])
            monthD = months[line.fecha_cobro.month - 1]
            if self.agreement_id.agreement_discount.type == 'porcentaje':
                total = 0.0
                for line in self:
                    porcentaje = 0
                    porcentaje = (float(self.agreement_id.agreement_discount.code) * line.price) / 100.0
                    total = total + porcentaje
                order_vals = {
                    'partner_id': self.agreement_id.partner_id.id,
                    'opportunity_id': self.agreement_id.crm_lead_id.id,
                    'agreement_type_id': self.agreement_id.agreement_type_id.id,
                    'agreement_id': self.agreement_id.id,
                    'date_order': datetime.now(),
                    'validity_date': self.agreement_id.end_date,
                    'user_id': self.agreement_id.crm_lead_id.user_id.id,
                    'origin': self.agreement_id.crm_lead_id.name,
                    'partner_dir_id': line.partner_contact_id.id,
                    'is_rental_order': True,
                    'cost_center_id': line.cost_center,
                    'tipo_rental_order': 'descuento',
                    'agreement_id': self.agreement_id.id,
                    'agreement_line_ids': line.id,
                    'payment_period': self.agreement_id.payment_period.id,
                    'payment_method': self.agreement_id.payment_method.id,
                    'payment_term_id': self.agreement_id.payment_term_id.id,
                    'inicio_fecha_alquiler': line.fecha_cobro,
                    'fin_fecha_alquiler': fin_mes,
                    'fecha_fact_prog': datetime.now().date() + relativedelta(days=1),
                    'fecha_estimada': datetime.now().date() + relativedelta(days=1),
                    'periodo_mes': str(monthD) + '/' + str(line.fecha_cobro.year),
                    'state': 'draft',  # 'sale',
                    'currency_id': self.agreement_id.currency_id.id,
                    'pricelist_id': line.pricelist_mens.id,
                    'reference_ids': [self.agreement_id.reference_ids.id],
                    #'agreement_currency_id': line.currency_id_men.id,
                }
                order = self.env['sale.order'].create(order_vals)
                name_order = str(order.name) + ' ' + str(line.fecha_cobro) + ' - Descuento Promocional'
                order.write({'name': name_order})
                order_line = {
                    'order_id': order.id,
                    'product_id': line.product_id.id,
                    'price_unit': - total,
                    'tax_id': [self.agreement_id.tax_id.id],
                }
                order_line = self.env['sale.order.line'].create(order_line)
            if self.agreement_id.agreement_discount.type == 'valor':
                total = float(self.agreement_id.agreement_discount.code)
                order_vals = {
                    'partner_id': self.agreement_id.partner_id.id,
                    'opportunity_id': self.agreement_id.crm_lead_id.id,
                    'agreement_type_id': self.agreement_id.agreement_type_id.id,
                    'agreement_id': self.agreement_id.id,
                    'date_order': datetime.now(),
                    'validity_date': self.agreement_id.end_date,
                    'user_id': self.agreement_id.crm_lead_id.user_id.id,
                    'origin': self.agreement_id.crm_lead_id.name,
                    'partner_dir_id': line.partner_contact_id.id,
                    'is_rental_order': True,
                    'cost_center_id': line.cost_center,
                    'tipo_rental_order': 'descuento',
                    'agreement_id': self.agreement_id.id,
                    'agreement_line_ids': line.id,
                    'payment_period': self.agreement_id.payment_period.id,
                    'payment_method': self.agreement_id.payment_method.id,
                    'payment_term_id': self.agreement_id.payment_term_id.id,
                    'inicio_fecha_alquiler': line.fecha_cobro,
                    'fin_fecha_alquiler': fin_mes,
                    'fecha_fact_prog': datetime.now().date() + relativedelta(days=1),
                    'fecha_estimada': datetime.now().date() + relativedelta(days=1),
                    'periodo_mes': str(monthD) + '/' + str(line.fecha_cobro.year),
                    'state': 'draft',  # 'sale',
                    'currency_id': self.agreement_id.currency_id.id,
                    'pricelist_id': line.pricelist_mens.id,
                    'reference_ids': [self.agreement_id.reference_ids.id],
                }
                order = self.env['sale.order'].create(order_vals)
                name_order = str(order.name) + ' ' + str(line.fecha_cobro) + ' - Descuento Promocional'
                order.write({'name': name_order})
                order_line = {
                    'order_id': order.id,
                    'product_id': line.product_id.id,
                    'price_unit': - total,
                    'tax_id': [self.agreement_id.tax_id.id],
                }
                order_line = self.env['sale.order.line'].create(order_line)
        #rental orders
        for line in self:
            primero = True
            today = datetime.now().date() + relativedelta(days=1)
            today_defasado = today
            fin_ciclo = today + relativedelta(months=time_periodicy)
            end_period = str(fin_ciclo.year) + '-' + str(line.fecha_cobro.month).zfill(2) + '-' + str(
                line.fecha_cobro.day).zfill(2)
            end_period = datetime.strptime(end_period, '%Y-%m-%d')
            if self.agreement_id.payment_period.code == 'S' or self.agreement_id.payment_period.code == 'T' or self.agreement_id.payment_period.code == 'M':
                end_period = fin_ciclo
            numeracion = 1
            proporcional = True
            primero_seq = False
            prorrateo = True
            end_12 = ''
            end_for = ''
            es_primero = 1
            period_day = line.fecha_cobro.day
            period_mes_ = line.fecha_cobro.month
            period_anio = line.fecha_cobro.year
            period_date = str(line.fecha_cobro.year) + '-' + str(line.fecha_cobro.month).zfill(2) + '-' + '01'
            period_date = datetime.strptime(period_date, '%Y-%m-%d')
            if line.fecha_cobro.day == 1 or line.fecha_cobro.day == 2 or line.fecha_cobro.day == 3:
                primero = False
                primero_seq = True
                prorrateo = True
                proporcional = False
            if primero == True:
                first = line.fecha_cobro
                monthRange = calendar.monthrange(first.year, first.month)
                month = monthRange[1]  # es primera vez
                dia = month - first.day + 1
                por_dia = line.price / month
                total = por_dia * dia
                ultimo_de_mes = calendar.monthrange(period_date.year, period_date.month)
                fin_mes = str(period_date.year) + '-' + str(period_date.month).zfill(2) + '-' + str(ultimo_de_mes[1])
                month = months[period_date.month - 1]
                order_vals = {
                    'partner_id': self.agreement_id.partner_id.id,
                    'opportunity_id': self.agreement_id.crm_lead_id.id,
                    'agreement_type_id': self.agreement_id.agreement_type_id.id,
                    'agreement_id': self.agreement_id.id,
                    'date_order': datetime.now(),
                    'validity_date': self.agreement_id.end_date,
                    'user_id': self.agreement_id.crm_lead_id.user_id.id,
                    'origin': self.agreement_id.crm_lead_id.name,
                    'partner_dir_id': line.partner_contact_id.id,
                    'is_rental_order': True,
                    'cost_center_id': line.cost_center,
                    'tipo_rental_order': 'mensualidad',
                    'agreement_id': self.agreement_id.id,
                    'agreement_line_ids': line.id,
                    'payment_period': self.agreement_id.payment_period.id,
                    'payment_method': self.agreement_id.payment_method.id,
                    'payment_term_id': self.agreement_id.payment_term_id.id,
                    'inicio_fecha_alquiler': line.fecha_cobro,
                    'fin_fecha_alquiler': fin_mes,
                    'fecha_fact_prog': today,
                    'fecha_estimada': today,
                    'periodo_mes': str(month) + '/' + str(period_date.year),
                    'state': 'draft', #'sale',
                    'currency_id': self.agreement_id.currency_id.id,
                    'pricelist_id': line.pricelist_mens.id,
                    'reference_ids': [self.agreement_id.reference_ids.id],
                    'agreement_currency_id': line.currency_id_men.id,
                }
                order = self.env['sale.order'].create(order_vals)
                name_order = str(order.name) + ' ' + str(today) + ' - ' + str(numeracion)
                order.write({'name': name_order})
                precio_men = round(total, 3) + 0.001
                order_line = {
                    'order_id': order.id,
                    'product_id': line.product_id.id,
                    'name': str(line.product_id.name_key) + '/' + str(line.maintenance_id.name) + '/' + str(
                        line.currency_id_men.name) + '' + str(precio_men) + '+iva',
                    'price_unit': total,
                    'tax_id': [self.agreement_id.tax_id.id]
                }
                order_line = self.env['sale.order.line'].create(order_line)
                period_date = period_date + relativedelta(months=1)
                primero = False
            while (meses < 36):
                if today_defasado > datetime.strptime(str(period_date)[0:10], '%Y-%m-%d').date():
                    meses = meses
                else:
                    meses = meses + time_periodicy
                if self.agreement_id.payment_period.code == 'AM' and meses2 == 12:
                    time_periodicy = 1
                if self.agreement_id.payment_period.code == 'A' and meses2 == 12:
                    descuento = 2
                if self.agreement_id.payment_period.code == 'A' and meses2 == 24:
                    descuento = 2
                if self.agreement_id.payment_period.code == 'A' and meses2 == 36:
                    descuento = 2
                if self.agreement_id.payment_period.code == 'A' and meses2 == 48:
                    descuento = 2
                if self.agreement_id.payment_period.code == 'A' and meses2 == 60:
                    descuento = 2
                if self.agreement_id.payment_period.code == 'A' and meses2 == 72:
                    descuento = 2
                if self.agreement_id.payment_period.code == 'A' and meses2 == 84:
                    descuento = 2
                if self.agreement_id.payment_period.code == 'A' and meses2 == 96:
                    descuento = 2
                if self.agreement_id.payment_period.code == 'A' and meses2 == 108:
                    descuento = 2
                if self.agreement_id.payment_period.code == 'A' and meses2 == 120:
                    descuento = 2
                if self.agreement_id.payment_period.code == 'A' and meses2 == 132:
                    descuento = 2
                if self.agreement_id.payment_period.code == 'A' and meses2 == 144:
                    descuento = 2
                if self.agreement_id.payment_period.code == 'A' and meses2 == 156:
                    descuento = 2
                prorrateo = False
                lista = range(time_periodicy)
                listadef = list(lista)
                meses2 = meses2 + time_periodicy
                if today_defasado > datetime.strptime(str(period_date)[0:10], '%Y-%m-%d').date() or datetime.strptime(
                        str(end_period)[0:10], '%Y-%m-%d').date() >= datetime.strptime(str(period_date)[0:10],
                                                                                       '%Y-%m-%d').date():
                    today = today_defasado
                else:
                    if end_12 == '':
                        end_12 = today
                        today = period_date
                for i in listadef:

                    dia_ = today.day
                    mes_ = today.month
                    anio_ = today.year
                    date_def = today
                    if descuento:
                        des = range(descuento)
                        listades = list(des)
                        for des in listades:
                            period_date_des = period_date
                            if prorrateo:
                                period_date_des = period_date + relativedelta(months=1)
                            ultimo_de_mes = calendar.monthrange(period_date_des.year, period_date_des.month)
                            fin_mes = str(period_date_des.year) + '-' + str(period_date_des.month).zfill(2) + '-' + str(
                                ultimo_de_mes[1])
                            order_vals = {
                                'partner_id': self.agreement_id.partner_id.id,
                                'opportunity_id': self.agreement_id.crm_lead_id.id,
                                'agreement_type_id': self.agreement_id.agreement_type_id.id,
                                'agreement_id': self.agreement_id.id,
                                'date_order': datetime.now(),
                                'validity_date': self.agreement_id.end_date,
                                'user_id': self.agreement_id.crm_lead_id.user_id.id,
                                'origin': self.agreement_id.crm_lead_id.name,
                                'partner_dir_id': line.partner_contact_id.id,
                                'is_rental_order': True,
                                'cost_center_id': line.cost_center,
                                'tipo_rental_order': 'descuento',
                                'agreement_id': self.agreement_id.id,
                                'agreement_line_ids': line.id,
                                'payment_period': self.agreement_id.payment_period.id,
                                'payment_method': self.agreement_id.payment_method.id,
                                'payment_term_id': self.agreement_id.payment_term_id.id,
                                'inicio_fecha_alquiler': period_date_des,
                                'fin_fecha_alquiler': fin_mes,
                                'fecha_fact_prog': date_def,
                                'fecha_estimada': date_def,
                                'periodo_mes': str(months[period_date_des.month - 1]) + '/' + str(period_date_des.year),
                                'state': 'draft',  # 'sale',
                                'currency_id': self.agreement_id.currency_id.id,
                                'pricelist_id': line.pricelist_mens.id,
                                'reference_ids': [self.agreement_id.reference_ids.id],
                                'agreement_currency_id': line.currency_id_men.id,
                            }
                            order = self.env['sale.order'].create(order_vals)
                            name_order = str(order.name) + ' ' + str(today) + ' - ' + str(numeracion)
                            order.write({'name': name_order})
                            precio_men = round(line.price, 3) + 0.001
                            order_line = {
                                'order_id': order.id,
                                'product_id': line.product_id.id,
                                'name': str(line.product_id.name_key) + '/' + str(line.maintenance_id.name) + '/' + str(
                                    line.currency_id_men.name) + '' + str(- precio_men) + '+iva',
                                'price_unit': - line.price,
                                'tax_id': [self.agreement_id.tax_id.id],
                            }
                            order_line = self.env['sale.order.line'].create(order_line)
                            descuento = False
                    line_price = line.price
                    ultimo_de_mes = calendar.monthrange(period_date.year, period_date.month)
                    fin_mes = str(period_date.year) + '-' + str(period_date.month).zfill(2) + '-' + str(
                        ultimo_de_mes[1])
                    month = months[period_date.month - 1]
                    if primero_seq:
                        date_def = today
                        monthRange = calendar.monthrange(period_date.year, period_date.month)
                        montha = monthRange[1]  # es primera vez
                        dia = montha - period_date.day
                        por_dia = line.price / montha
                        line_price = por_dia * dia
                    else:
                        period_date = str(period_date.year) + '-' + str(
                            period_date.month).zfill(2) + '-' + '01'
                        period_date = datetime.strptime(period_date, '%Y-%m-%d')
                    primero_seq = False

                    order_vals = {
                        'partner_id': self.agreement_id.partner_id.id,
                        'opportunity_id': self.agreement_id.crm_lead_id.id,
                        'agreement_type_id': self.agreement_id.agreement_type_id.id,
                        'agreement_id': self.agreement_id.id,
                        'date_order': datetime.now(),
                        'validity_date': self.agreement_id.end_date,
                        'user_id': self.agreement_id.crm_lead_id.user_id.id,
                        'origin': self.agreement_id.crm_lead_id.name,
                        'partner_dir_id': line.partner_contact_id.id,
                        'is_rental_order': True,
                        'cost_center_id': line.cost_center,
                        'tipo_rental_order': 'mensualidad',
                        'agreement_id': self.agreement_id.id,
                        'agreement_line_ids': line.id,
                        'payment_period': self.agreement_id.payment_period.id,
                        'payment_method': self.agreement_id.payment_method.id,
                        'payment_term_id': self.agreement_id.payment_term_id.id,
                        'inicio_fecha_alquiler': period_date,
                        'fin_fecha_alquiler': fin_mes,
                        'fecha_fact_prog': date_def,
                        'fecha_estimada': date_def,
                        'periodo_mes': str(month) + '/' + str(period_date.year),
                        'state': 'draft', #'sale',
                        'currency_id': self.agreement_id.currency_id.id,
                        'pricelist_id': line.pricelist_mens.id,
                        'reference_ids': [self.agreement_id.reference_ids.id],
                        'agreement_currency_id': line.currency_id_men.id,
                    }
                    order = self.env['sale.order'].create(order_vals)
                    name_order = str(order.name) + ' ' + str(today) + ' - ' + str(numeracion)
                    order.write({'name': name_order})
                    precio_men = round(line_price, 3) + 0.001
                    order_line = {
                        'order_id': order.id,
                        'product_id': line.product_id.id,
                        'name': str(line.product_id.name_key) + '/' + str(line.maintenance_id.name) + '/' + str(
                            line.currency_id_men.name) + '' + str(precio_men) + '+iva',
                        'price_unit': line_price,
                        'tax_id': [self.agreement_id.tax_id.id],
                    }
                    order_line = self.env['sale.order.line'].create(order_line)
                    numeracion = numeracion + 1
                    primero = False
                    proporcional = False
                    period_date = period_date + relativedelta(months=1)
                today = today + relativedelta(months=time_periodicy)


        # Mantenciones
        # for line in self:
        #     if line.maintenance_id:
        #         todayM = line.start_date# datetime.now().date()
        #         period_m = datetime.now().date()
        #         #period_m = str(line.start_date.year) + '-' + str(line.start_date.month).zfill(2) + '-' + '01'
        #         #period_m = datetime.strptime(period_date, '%Y-%m-%d')
        #         meses = 0
        #         mesesM = 0
        #         numeracionM = 1
        #         mj2 = []
        #         num = 0
        #         for j in line.maintenance_id.maintenance_m_line:
        #             if j.number not in mj2:
        #                 mj2.append(j.number)
        #         while (mesesM < 36):
        #             name_list = []
        #             mj2 = sorted(mj2, reverse=False)
        #             for i in mj2:
        #                 if datetime.strptime(str(period_m)[0:10], '%Y-%m-%d').date() > todayM:
        #                     mesesM = mesesM
        #                 else:
        #                     mesesM = mesesM + int(mj2[0])
        #                 meses = meses + int(mj2[0])
        #                 if mesesM >= 36:
        #                     break
        #                 todayM = todayM + relativedelta(months=int(mj2[0]))
        #                 num = i
        #                 ticket_man = self.env['helpdesk.ticket'].create({
        #                     'name': 'Mantención ' + line.product_id.name + ' - ' + str(numeracionM),
        #                     'partner_id': self.agreement_id.partner_id.id,
        #                     'assign_date': todayM,
        #                     'fecha_registro_ticket': todayM,
        #                     'agreement_id': self.agreement_id.id,
        #                     'ticket_type_id': 1,
        #                     'agreement_line_ids': line.id,
        #                     'partner_email': self.agreement_id.partner_id.email,
        #                     #'user_id': line.mantenedor or False,
        #                 })
        #                 order_lineM = self.env['project.task'].create({
        #                     'name': 'Mantención ' + line.product_id.name + ' - ' + str(numeracionM),
        #                     'partner_id': self.agreement_id.partner_id.id,
        #                     'helpdesk_ticket_id': ticket_man.id,
        #                     'description': self.general_msj,
        #                     'stage_id': 4,
        #                     'fsm_done': False,
        #                     'project_id': 2,
        #                 })
        #                 for x in line.maintenance_id.maintenance_m_line:
        #                     if x.number <= num:
        #                         if x.type not in name_list:
        #                             name_list.append(x.type)
        #                         order_lineM_l = self.env['project.task.product'].create({
        #                             'product_id': x.product_id.id,
        #                             'description': x.product_id.name,
        #                             'planned_qty': x.quantity,
        #                             'product_uom': x.product_id.uom_id.id,
        #                             'time_spent': x.time_spent,
        #                             'task_id': order_lineM.id,
        #                         })
        #                 name_new = ''
        #                 for n in name_list:
        #                     name_new = name_new + ' ' + n
        #                 ticket_man.write({'name': ticket_man.name + ' ' + name_new})
        #                 order_lineM.write({'name': order_lineM.name + ' ' + name_new})
        #                 numeracionM = numeracionM + 1
        #     self.write({'state': 'act'})
        #
        # orden_compra = self.agreement_id.orden_compra()

        state = True
        for line in self:
            line.write({'state': 'act'})
            state_id = self.env['agreement.stage'].search([('name', '=', 'ACTIVADO COMPLETO')], limit=1)
            line.agreement_id.write({'stage_id': state_id})
                #state = False
        # if state == False:
        #     state_id = self.env['agreement.stage'].search([('name', '=', 'ACTIVADO PARCIAL')], limit=1)
        #     line.agreement_id.write({'stage_id': state_id})
        # if state == True:
        #     state_id = self.env['agreement.stage'].search([('name', '=', 'ACTIVADO COMPLETO')], limit=1)
        #     line.agreement_id.write({'stage_id': state_id})

        return True

    def cancel_agreement(self):
        self.write({'state': 'proceso'})
        rentals = self.env['sale.order'].search([
            ('agreement_line_ids', '=', self.id),
            ('state', '=', 'sale')])
        rentals.action_cancel()
        jamie = 1

    def close_agreement(self):
        self.write({'state': 'cerrado'})

    def no_vigent_agreement(self):
        self.write({'state': 'prueba'})

    @api.model
    def create(self, vals):
        agreement_name = self.env['agreement'].search([('id', '=', vals['agreement_id'])])
        product = self.env['product.product'].search([('id', '=', vals['product_principal'])])
        vals['name'] = str(agreement_name.name) + '/' + str(product.patente)
        res = super(AgreementLine, self).create(vals)
        return res

    # def write(self, vals):
    #     if 'pass_line_rel' in vals:
    #         rel = self.browse(vals['pass_line_rel'])
    #         rel.write({
    #                     'fut_line_rel': self.id,
    #                     # 'fut_motivo_rel': self.pass_motivo_rel,
    #                     # 'fut_description_rel': self.pass_description_rel
    #         })
    #     if 'cost_center' in vals:
    #         orders = self.env['sale.order'].search(
    #             [('agreement_id', '=', self.agreement_id.id), ('agreement_line_ids', '=', self.id), ('state', '=', 'draft')])
    #         if orders:
    #             orders.write({'cost_center_id': vals['cost_center']})
    #     return super(AgreementLine, self).write(vals)

class ProductMaintenance(models.Model):
    _name = 'product.maintenance_m'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']

    sequence = fields.Integer('Sequence')
    name = fields.Text(string='Name', required=True)
    product_id = fields.Many2one('product.product', string='Service')
    maintenance_m_line = fields.One2many('product.maintenance_m.line', 'maintenance_id', string='Maintenance Lines')

    @api.onchange('product_id')
    def get_product_maintenance(self):
        if self.product_id:
            for m in self.maintenance_m_line.product_id:
                m.product_id = self.product_id.id


class ProductMaintenanceLine(models.Model):
    _name = 'product.maintenance_m.line'

    sequence = fields.Integer('Sequence')
    maintenance_id = fields.Many2one('product.maintenance_m', string='Maintenance Reference', required=True, ondelete='cascade', index=True)
    periodicity = fields.Selection(
        selection=[
            ('hours', 'Hours'),
            ('days', 'Days'),
            ('month', 'Month'),
            ('year', 'Years')],
        string='Periodicity',
        default='month',
        required=True)
    time_spent = fields.Float('Time/Hours', precision_digits=2)
    type = fields.Selection(
        selection=[
            ('media', 'Mean'),
            ('full', 'Full'),
            ('membrana', 'Membrane')],
        string='Type',
        default='media',
        required=True)
    number = fields.Integer('Number')
    product_id = fields.Many2one('product.product', string='Product')
    quantity = fields.Float("Quantity", default=1, required=True)

class AgreementLineKeys(models.Model):
    _name = "agreement.line.keys"
    _description = "Agreement Invoice Lines Ids products"

    name = fields.Char(
        string="Number",
        required=True)

class AgreementPenalty(models.Model):
    _name = 'agreement.penalty'

    name = fields.Char(required=True, string='Name')
    code = fields.Float(required=True, string='Value')
    type = fields.Selection(selection=[('porcentaje', 'Percentage'), ('valor', 'Net worth')], string='Type')
    type_id = fields.Many2one('penalty.type', 'Class', readonly=False)
    pricelist_id = fields.Many2one('product.pricelist', 'Rate', readonly=False)
    med_apl = fields.Text(string='Metodología de Aplicación', required=True)

class AgreementDiscount(models.Model):
    _name = 'agreement.discount'

    @api.model
    def _cron_agreement_discounts(self):
        discounts = self.env['agreement.discount'].sudo().search([
                        ('state', '=', 'in_progress')])
        for dis in discounts:
            months = (
                "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre",
                "Noviembre",
                "Diciembre")
            today = datetime.now().date()
            if dis.intervalo:
                descuento = 1
                state = 'in_progress'
                des = range(descuento)
                listades = list(des)
                for des in listades:
                    period_date_des = dis.fecha_inicio
                    date_def = period_date_des
                    ultimo_de_mes = calendar.monthrange(period_date_des.year, period_date_des.month)
                    fin_mes = str(period_date_des.year) + '-' + str(period_date_des.month).zfill(2) + '-' + str(
                        ultimo_de_mes[1])
                    order_vals = {
                        'partner_id': dis.agreement_id.partner_id.id,
                        'opportunity_id': dis.agreement_id.crm_lead_id.id,
                        'agreement_type_id': dis.agreement_id.agreement_type_id.id,
                        'agreement_id': dis.agreement_id.id,
                        'date_order': datetime.now(),
                        'validity_date': dis.agreement_id.end_date,
                        'user_id': dis.agreement_id.crm_lead_id.user_id.id,
                        'origin': dis.agreement_id.crm_lead_id.name,
                        'partner_dir_id': dis.agreement_line_id.partner_contact_id.id,
                        'is_rental_order': True,
                        'cost_center_id': dis.agreement_line_id.cost_center,
                        'tipo_rental_order': 'descuento',
                        'agreement_id': dis.agreement_id.id,
                        'agreement_line_ids': dis.agreement_line_id.id,
                        'payment_period': dis.agreement_id.payment_period.id,
                        'payment_method': dis.agreement_id.payment_method.id,
                        'payment_term_id': dis.agreement_id.payment_term_id.id,
                        'inicio_fecha_alquiler': period_date_des,
                        'fin_fecha_alquiler': fin_mes,
                        'fecha_fact_prog': date_def,
                        'fecha_estimada': date_def,
                        'periodo_mes': str(months[period_date_des.month - 1]) + '/' + str(period_date_des.year),
                        'state': 'draft',  # 'sale',
                        'currency_id': dis.agreement_id.currency_id.id,
                        'pricelist_id': dis.agreement_line_id.pricelist_mens.id,
                        'reference_ids': [dis.agreement_id.reference_ids.id],
                        'agreement_currency_id': dis.agreement_line_id.currency_id_men.id,
                    }
                    order = self.env['sale.order'].create(order_vals)
                    name_order = str(order.name) + ' ' + str(today)
                    order.write({'name': name_order})
                    valor = 0
                    if dis.aplic == 'inst':
                        valor = dis.agreement_line_id.price_instalacion
                    else:
                        valor = dis.agreement_line_id.price
                    if dis.type == 'valor':
                        precio = dis.code
                    else:
                        precio = (float(dis.code) * valor) / 100.0
                    order_line = {
                        'order_id': order.id,
                        'product_id': dis.product_id.id,
                        'name': 'Descuento',
                        'price_unit': - precio,
                        'tax_id': [dis.agreement_id.tax_id.id],
                    }
                    order_line = self.env['sale.order.line'].create(order_line)
                    #self.fecha_inicio = self.fecha_inicio + relativedelta(months=1)
        return True

    name = fields.Char(required=True, string='Name')
    code = fields.Float(required=True, string='Value')
    intervalo = fields.Integer(required=True, string='Num Repeticiones')
    type = fields.Selection(selection=[('porcentaje', 'Porcentaje'), ('valor', 'Valor Neto')], string='Tipo')
    fecha_inicio = fields.Date('Fecha Inicio')
    fecha_fin = fields.Date('Fecha Final')
    pricelist_id = fields.Many2one('product.pricelist', 'Rate', readonly=False)
    agreement_id = fields.Many2one('agreement', ondelete='cascade', index=True, copy=False)
    agreement_line_id = fields.Many2one('agreement.line', ondelete='cascade', index=True, copy=False)
    aplic = fields.Selection(
        [("inst", "Instalation"), ("men", "Mensualidad")],
        default="men",
        track_visibility="always", string='Aplicar a')
    state = fields.Selection(
        [("draft", "Draft"), ("confir", "Confirmed"), ("in_progress", "In Progress"), ("done", "done")],
        default="draft",
        track_visibility="always")
    product_id = fields.Many2one('product.product', string='Producto Descuento')

    def confirm(self):
        months = (
            "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre",
            "Noviembre",
            "Diciembre")
        today = datetime.now().date()
        if self.intervalo:
            descuento = 0
            if self.intervalo == -1:
                descuento = 1
                state = 'in_progress'
            else:
                descuento = self.intervalo
                state = 'confir'
            des = range(descuento)
            listades = list(des)
            for des in listades:
                period_date_des = self.fecha_inicio
                date_def = period_date_des
                ultimo_de_mes = calendar.monthrange(period_date_des.year, period_date_des.month)
                fin_mes = str(period_date_des.year) + '-' + str(period_date_des.month).zfill(2) + '-' + str(
                    ultimo_de_mes[1])
                order_vals = {
                    'partner_id': self.agreement_id.partner_id.id,
                    'opportunity_id': self.agreement_id.crm_lead_id.id,
                    'agreement_type_id': self.agreement_id.agreement_type_id.id,
                    'agreement_id': self.agreement_id.id,
                    'date_order': datetime.now(),
                    'validity_date': self.agreement_id.end_date,
                    'user_id': self.agreement_id.crm_lead_id.user_id.id,
                    'origin': self.agreement_id.crm_lead_id.name,
                    'partner_dir_id': self.agreement_line_id.partner_contact_id.id,
                    'is_rental_order': True,
                    'cost_center_id': self.agreement_line_id.cost_center,
                    'tipo_rental_order': 'descuento',
                    'agreement_id': self.agreement_id.id,
                    'agreement_line_ids': self.agreement_line_id.id,
                    'payment_period': self.agreement_id.payment_period.id,
                    'payment_method': self.agreement_id.payment_method.id,
                    'payment_term_id': self.agreement_id.payment_term_id.id,
                    'inicio_fecha_alquiler': period_date_des,
                    'fin_fecha_alquiler': fin_mes,
                    'fecha_fact_prog': date_def,
                    'fecha_estimada': date_def,
                    'periodo_mes': str(months[period_date_des.month - 1]) + '/' + str(period_date_des.year),
                    'state': 'draft',  # 'sale',
                    'currency_id': self.agreement_id.currency_id.id,
                    'pricelist_id': self.agreement_line_id.pricelist_mens.id,
                    'reference_ids': [self.agreement_id.reference_ids.id],
                    'agreement_currency_id': self.agreement_line_id.currency_id_men.id,
                }
                order = self.env['sale.order'].create(order_vals)
                name_order = str(order.name) + ' ' + str(today)
                order.write({'name': name_order})
                valor = 0
                if self.aplic == 'inst':
                    valor = self.agreement_line_id.price_instalacion
                else:
                    valor = self.agreement_line_id.price
                if self.type == 'valor':
                    precio = self.code
                else:
                    precio = (float(self.code) * valor) / 100.0
                order_line = {
                    'order_id': order.id,
                    'product_id': self.product_id.id,
                    'name': 'Descuento',
                    'price_unit': - precio,
                    'tax_id': [self.agreement_id.tax_id.id],
                }
                order_line = self.env['sale.order.line'].create(order_line)
                self.fecha_inicio = self.fecha_inicio + relativedelta(months=1)
        self.write({'state': state})

    @api.onchange('pricelist_id')
    def _onchange_pricelist_id(self):
        if self.pricelist_id:
            product_domain = []
            for item in self.pricelist_id.item_ids:
                if item.compute_price == 'percentage':
                    product_domain.append(item.product_tmpl_id.id)
            return {'domain':{'product_id':[('id','in',product_domain)]}}

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            for item in self.pricelist_id.item_ids:
                if item.product_tmpl_id.id == self.product_id.id:
                    self.type = 'porcentaje'
                    self.code = item.percent_price



class AgreementLineType(models.Model):
    _name = 'agreement.line.type'

    name = fields.Char(required=True, string='Name')
    code = fields.Char(required=True, string='Code')

class AgreementL10nCl(models.Model):
    _name = 'agreement.l10ncl'

    name = fields.Char(required=True, string='Name')
    code = fields.Char(required=True, string='Code')

class PenaltyType(models.Model):
    _name = 'penalty.type'

    name = fields.Char(required=True, string='Name')

