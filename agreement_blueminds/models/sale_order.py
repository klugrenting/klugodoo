# Copyright (C) 2022 - TODAY, Jescalante@blueminds.cl
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)..

from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    agreement_template_id = fields.Many2one(
        'agreement',
        string="Agreement Template",
        domain="[('is_template', '=', True)]")
    agreement_id = fields.Many2one(
        comodel_name='agreement', string='Agreement', ondelete='restrict',
        track_visibility='onchange', readonly=True, copy=False,
        states={'draft': [('readonly', False)], 'sent': [('readonly', False)]})

    agreement_type_id = fields.Many2one(
        comodel_name="agreement.type", string="Agreement Type",
        ondelete="restrict",
        track_visibility='onchange', readonly=True, copy=True,
        states={'draft': [('readonly', False)], 'sent': [('readonly', False)]})
    reference_oc = fields.Many2one('l10n_cl.account.invoice.reference', string='Purchase order')
    req_orden = fields.Boolean(related='agreement_id.req_orden',
                               string='Allows purchase order or prior contract order?')
    l10ncl_domain = fields.Many2many(related='agreement_id.l10ncl_domain',
                                     string='Required documents')
    reference_ids = fields.One2many(
        "l10n_cl.account.invoice.reference", "sale_id", readonly=True,
        states={"draft": [("readonly", False)]})
    partner_dir_id = fields.Many2one(
        'res.partner', string='Direccion', readonly=True,
        states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
        required=False, change_default=True, index=True, tracking=1,
        domain="[('type', '=', 'delivery')]")
    payment_period = fields.Many2one(
        "agreement.payment.period", required=False,
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]}, copy=True,
        string="Periodicidad de Pago")
    payment_method = fields.Many2one(
        "agreement.payment.method", required=True,
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]}, copy=True,
        string="Método de Pago")
    maihue_zone = fields.Many2one('maihue.zone', string='Zona',
                                  states={'cancel': [('readonly', True)], 'done': [('readonly', True)]}, copy=True,
                                  auto_join=True)

    # validation_income = fields.Many2many('maihue.validation.income', 'sale_maihue_validation_income_rel', 'order_id',
    #                                      'validation_id',
    #                                      string='Estado Validación de Ingreso')
    # commission_ids = fields.Many2many('maihue.commission', 'sale_maihue_commission_rel', 'order_id', 'commission_id',
    #                                   string='¿Comisiona?')
    state = fields.Selection(
        selection_add=[
            ('baja', 'En Proceso de Baja'),
        ])
    # reference_oc = fields.One2many(related="agreement_id.reference_ids", string="Ordenes de compra")
    agreement_line_ids = fields.Many2one('agreement.line', track_visibility="onchange", string="Linea de Contrato")
    # unificacion modulo 'custom_fecha_fact_prog'
    fecha_fact_prog = fields.Date("Fecha Fact Prog")
    fecha_estimada = fields.Date("Fecha Estimada")
    # unificacion modulo 'custom_periodo_rango_on_rental_order
    tipo_rental_order = fields.Selection([
        ('instalacion', 'Instalacion'),
        ('mensualidad', 'Mensualidad'),
        ('descuento', 'Descuento'),
        ('incidencia', 'Incidencia')], "Tipo")

    periodo_mes_alquiler = fields.Selection([
        ('enero', 'Enero'),
        ('febrero', 'Febrero'),
        ('marzo', 'Marzo'),
        ('abril', 'Abril'),
        ('mayo', 'Mayo'),
        ('junio', 'Junio'),
        ('julio', 'Julio'),
        ('agosto', 'Agosto'),
        ('septiembre', 'Septiembre'),
        ('octubre', 'Octubre'),
        ('noviembre', 'Noviembre'),
        ('diciembre', 'Diciembre')], "Periodo")
    periodo_mes = fields.Char(required=False, string='Periodo')
    inicio_fecha_alquiler = fields.Date("De")
    fin_fecha_alquiler = fields.Date("Hasta")
    pre_liquid = fields.Boolean('Preliquidacion')
    agreement_currency_id = fields.Many2one("res.currency", string="Currency")
    detail_line = fields.One2many('sale.order.detail', 'order_id', string='Nota de cobro')
    detaill_line = fields.One2many('sale.order.detaill', 'order_id', string='Detalle Nota de cobro')

    def _prepare_invoice(self):
        vals = super()._prepare_invoice()
        vals['agreement_id'] = self.agreement_id.id or False
        return vals

    @api.model
    def _action_confirm(self):
        res = super(SaleOrder, self)._action_confirm()
        for order in self:
            if order.agreement_template_id:
                order.agreement_id = order.\
                    agreement_template_id.copy(default={
                        'name': order.name,
                        'code': order.name,
                        'is_template': False,
                        'sale_id': order.id,
                        'partner_id': order.partner_id.id,
                        'analytic_account_id': order.analytic_account_id and
                        order.analytic_account_id.id or False,
                    })
                for line in order.order_line:
                    # Create agreement line
                    self.env['agreement.line'].\
                        create(self._get_agreement_line_vals(line))
                    # Create SP's based on product_id config
                    if line.product_id.is_serviceprofile:
                        self.create_sp_qty(line, order)
        return res

    def create_sp_qty(self, line, order):
        """ Create line.product_uom_qty SP's """
        if line.product_id.product_tmpl_id.is_serviceprofile:
            for i in range(1, int(line.product_uom_qty)+1):
                self.env['agreement.serviceprofile'].\
                    create(self._get_sp_vals(line, order, i))

    def _get_agreement_line_vals(self, line):
        return {
            'product_id': line.product_id.id,
            'name': line.name,
            'agreement_id': line.order_id.agreement_id.id,
            'qty': line.product_uom_qty,
            'sale_line_id': line.id,
            'uom_id': line.product_uom.id
        }

    def _get_sp_vals(self, line, order, i):
        return {
            'name': line.name + ' ' + str(i),
            'product_id': line.product_id.product_tmpl_id.id,
            'agreement_id': order.agreement_id.id,
        }

    def action_confirm(self):
        # If sale_timesheet is installed, the _action_confirm()
        # may be setting an Analytic Account on the SO.
        # But since it is not a dependency, that can happen after
        # we create the Agreement.
        # To work around that, we check if that is the case,
        # and make sure the SO Analytic Account is copied to the Agreement.
        res = super(SaleOrder, self).action_confirm()
        for order in self:
            agreement = order.agreement_id
            if (order.analytic_account_id and agreement and
                    not agreement.analytic_account_id):
                agreement.analytic_account_id = order.analytic_account_id
        return res
