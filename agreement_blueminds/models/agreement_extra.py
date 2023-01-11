# © 2022 (Jamie Escalante <jescalante@blueminds.cl>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from requests import options
from odoo import api, models, tools, fields, _
import base64
import logging
from io import BytesIO
from xlwt import Workbook, easyxf
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class AgreementExtra(models.Model):
    _name = "agreement.extra"
    _inherit = ['mail.render.mixin']
    _description = "Agreement Extra"
    _order = "sequence"
    _AGREEMENT_EXTRA_FIELDS = ['content', 'dynamic_content']

    name = fields.Char(string="Nombre", required=True)
    title = fields.Char(
        string="Titulo",
        help="The title is displayed on the PDF." "The name is not.")
    sequence = fields.Integer(string="Secuencia", default=10)
    content = fields.Html(string="Content", render_engine='qweb', translate=True, sanitize=False)
    dynamic_content = fields.Html(
        compute='_compute_dynamic_content',
        string="Dynamic Content",
        sanitize=False,
        help="compute dynamic Content")
    agreement_id = fields.Many2one(
        "agreement", string="Agreement", ondelete="cascade")
    require_maihue = fields.Boolean(
        string="Requerido",
        default=True)
    required_sign = fields.Boolean(
        string="Debe Firmarse",
        default=False)
    active = fields.Boolean(
        string="Activo",
        default=True,
        help="If unchecked, it will allow you to hide this recital without "
        "removing it.")
    type_extra = fields.Many2one(
        "type.document.extra",
        string="Tipo",
        track_visibility="onchange")
    is_template = fields.Boolean(string='is_template', related='agreement_id.is_template', track_visibility='onchange')

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
    firma = fields.Selection([
        ('digital', 'Digital'),
        ('fisica', 'Fisica'),
        ('ambas', 'Ambas')
    ], string="Firma", default="digital")
    signed_contract_filename = fields.Char(string="Documento")
    signed_contract = fields.Binary(
        string="Documento", track_visibility="always")
    partner_id = fields.Many2one(
        "res.partner",
        string="Partner", related="agreement_id.partner_id")
    partner_signed_date = fields.Date(
        string="Signed on (Partner)",
        track_visibility="onchange",
        help="Date the contract was signed by the Partner.")
    partner_signed_user_id = fields.Many2one(
        "res.partner",
        string="Firmante R1",
        track_visibility="onchange",
        help="Contact on the account that signed the agreement/contract.")
    fecha_repres1 = fields.Date(
        string="Fecha Firma R1", track_visibility="onchange")
    fecha_envio1 = fields.Date(
        string="Fecha Envio R1", track_visibility="onchange")
    state_firm1 = fields.Selection(selection=[
        ('M', 'Firmado'),
        ('T', 'Pend. Firma'),
        ('S', 'Firma en Revisión'),
        ('cancelled', 'Cancelado')], string='Estado Firma R1')
    company_signed_user_dos_id = fields.Many2one(
        "res.partner",
        string="Firmante R2",
        track_visibility="onchange",
        help="Segundo Usuario que autorizo/firmo el acuerdo o contrato")
    fecha_repres2 = fields.Date(
        string="Fecha Firma R2", track_visibility="onchange")
    fecha_envio2 = fields.Date(
        string="Fecha Envio R2", track_visibility="onchange")
    state_firm2 = fields.Selection(selection=[
        ('M', 'Firmado'),
        ('T', 'Pend. Firma'),
        ('S', 'Firma en Revisión'),
        ('cancelled', 'Cancelado')], string='Estado Firma R2')
    company_signed_user_tres_id = fields.Many2one(
        "res.partner",
        string="Firmante R3",
        track_visibility="onchange",
        help="Tercera Usuario que autorizo/firmo el acuerdo o contrato")
    fecha_repres3 = fields.Date(
        string="Fecha Firma R3", track_visibility="onchange")
    fecha_envio3 = fields.Date(
        string="Fecha Envio R3", track_visibility="onchange")
    state_firm3 = fields.Selection(selection=[
        ('M', 'Firmado'),
        ('T', 'Pend. Firma'),
        ('S', 'Firma en Revisión'),
        ('cancelled', 'Cancelado')], string='Estado Firma R3')
    company_signed_date = fields.Date(
        string="Firmado en",
        track_visibility="onchange",
        help="Date the contract was signed by Company.")
    company_signed_user_id = fields.Many2one(
        "res.partner",
        string="Firmante Maihue",
        track_visibility="onchange",
        help="The user at our company who authorized/signed the agreement or "
             "contract.")
    state_firm4 = fields.Selection(selection=[
        ('M', 'Firmado'),
        ('T', 'Pend. Firma'),
        ('S', 'Firma en Revisión'),
        ('cancelled', 'Cancelado')], string='Estado Firma')
    signed_contract = fields.Binary(
        string="Documento Firmado", track_visibility="always")
    firma_type = fields.Selection([
        ('avanzada', 'Avanzada'),
        ('simple', 'Simple'),
        ('sin', 'Sin Firma')
    ], string="Tipo de Firma", default="avanzada")

    @api.onchange("firma")
    def onchange_firma(self):
        if self.firma:
            if self.firma == 'fisica':
                self.firma_type = 'sin'

    @api.model
    def create(self, vals):
        if 'agreement_id' in vals:
            agreement = self.env['agreement'].browse(vals['agreement_id'])
        #     if not agreement.is_template:
        #         new = self.copy({
        #     'agreement_id': vals['agreement_id']
        # })

        return super(AgreementExtra, self).create(vals)

    @api.depends('content')
    def _compute_dynamic_content(self):
        copy_depends_values = {'lang': 'es_CL'}
        context = self._context.get('lang')
        agreement_extra_id = self.with_context(lang=context)
        try:
            mail_values = agreement_extra_id.with_context(template_preview_lang=context).generate_email(
                self._origin.ids, self._AGREEMENT_EXTRA_FIELDS)
            mail_values = mail_values[self._origin.id]
            self._set_mail_attributes(values=mail_values)
        except UserError as user_error:
            _logger.info(user_error.args[0])
            self._set_mail_attributes()
        finally:
            for key, value in copy_depends_values.items():
                self[key] = value

    def _set_mail_attributes(self, values=None):
        # for field in self._AGREEMENT_EXTRA_FIELDS:
        #     if field != 'content':
        #         field_value = values.get(field, False) if values else self[field]
        #         self[field] = field_value   
        # self.partner_ids = values.get('partner_ids', False) if values else False
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
        for lang, (template, template_res_ids) in self._classify_per_lang(res_ids).items():
            template.render_model = 'agreement.extra'
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

    def export_fields_contract(self):
        IrModelFields = self.env['ir.model.fields']
        fields = IrModelFields.search([('model', '=', 'agreement')])
        fields_line = IrModelFields.search([('model', '=', 'agreement.line')])
        fields_contact = IrModelFields.search([('model', '=', 'res.partner')])
        report_name = 'Campos Contrato'
        workbook = Workbook()
        ws = workbook.add_sheet('Contrato')
        ws.write(0, 0, 'Nombre técnico')
        ws.write(0, 1, 'Etiqueta')
        ws.write(0, 2, 'Ayuda')
        row = 1
        for field in fields:
            ws.write(row, 0, field.name)
            ws.write(row, 1, field.field_description)
            ws.write(row, 2, field.help or '')
            row += 1

        ws = workbook.add_sheet('Lineas del Contrato')
        ws.write(0, 0, 'Nombre técnico')
        ws.write(0, 1, 'Etiqueta')
        ws.write(0, 2, 'Ayuda')
        row = 1
        for field in fields_line:
            ws.write(row, 0, field.name)
            ws.write(row, 1, field.field_description)
            ws.write(row, 2, field.help or '')
            row += 1

        ws = workbook.add_sheet('Contacto')
        ws.write(0, 0, 'Nombre técnico')
        ws.write(0, 1, 'Etiqueta')
        ws.write(0, 2, 'Ayuda')
        row = 1
        for field in fields_contact:
            ws.write(row, 0, field.name)
            ws.write(row, 1, field.field_description)
            ws.write(row, 2, field.help or '')
            row += 1

        ws = workbook.add_sheet('Formulas')
        ws.write(0, 0, 'Acción')
        ws.write(0, 1, 'Formula')
        ws.write(0, 2, 'Ayuda')
        # Condicional
        ws.write(1, 0, 'Sentencia condicional')
        ws.write(1, 1, '% if object.campo \n % endif')
        ws.write(1, 2, 'La sentencia condicional es una instrucción o grupo de instrucciones que se pueden ejecutar o no en función del valor de una condición')
        # Ciclo FOR
        ws.write(2, 0, 'Recorrer Líneas del contrato')
        ws.write(2, 1, '% for linea in object.line_ids \n % endfor')
        ws.write(2, 2, 'Por ejemplo, si se quiere imprimir el nombre de cada producto indicado en cada linea del contrato se colocaria lo siguiente % for linea in object.line_ids ${linea.product_id.name} % endfor')
        # Sumar dos campos del contrato
        ws.write(3, 0, 'Sumar dos campos')
        ws.write(3, 1, '% set total_suma = object.campo1 + object.campo2 ${total_suma}')
        ws.write(3, 2, 'Para sumar 2 campos simplemente con la palabra set creamos una variable donde guardaremos el resultado de la sumatoria y luego colocamos ${total_suma} donde queramos que se muestre')# Sumar dos campos del contrato
        # Sumar dos campos del contrato
        ws.write(4, 0, 'Multiplicar dos campos')
        ws.write(4, 1, '% set total_multiplicacion = object.campo1 * object.campo2 ${total_multiplicacion}')
        ws.write(4, 2, 'Para multiplicar 2 campos simplemente con la palabra set creamos una variable donde guardaremos el resultado de la multiplcacion y luego colocamos ${total_multiplicacion} donde queramos que se muestre')
        # Sumar un campos por un valor fijo del contrato
        ws.write(5, 0, 'Multiplicar un campo por un valor fijo ')
        ws.write(5, 1, '% set total_multiplicacion = object.campo1 * 1.19 ${total_multiplicacion}')
        ws.write(5, 2, 'Para multiplicar un campo por un valor fijo simplemente con la palabra set creamos una variable donde guardaremos el resultado de la multiplcacion y luego colocamos ${total_multiplicacion} donde queramos que se muestre')
        # Restar dos campos del contrato
        ws.write(6, 0, 'Restar dos campos')
        ws.write(6, 1, '% set total_resta = object.campo1 - object.campo2 ${total_resta}')
        ws.write(6, 2, 'Para restar 2 campos simplemente con la palabra set creamos una variable donde guardaremos el resultado de la resta y luego colocamos ${total_resta} donde queramos que se muestre')
        # Dividir dos campos del contrato
        ws.write(7, 0, 'Dividir dos campos')
        ws.write(7, 1, '% set total_division = object.campo1 / object.campo2 ${total_division}')
        ws.write(7, 2, 'Para dividir 2 campos simplemente con la palabra set creamos una variable donde guardaremos el resultado de la division y luego colocamos ${total_division} donde queramos que se muestre. Se debe tener cuidado con la division por 0. Se recomienda colocar una sentencia condicional para la parte divisoria')
        # Formato moneda
        ws.write(8, 0, 'Formato de Moneda')
        ws.write(8, 1, '${format_amount(sumatoria, object.pricelist_id.currency_id)}')
        ws.write(8, 2, 'Para dar formato de moneda a un valor numerico se usa una funcion llamada format_amount y dentro de los parentesis se debe indicar primero el campo que contiene el valor numerico y luego se indica la moneda que tiene definida la tarifa de esta forma object.pricelist_id.currency_id')
        fp = BytesIO()
        workbook.save(fp)
        fp.seek(0)
        data = fp.read()
        fp.close()
        data_b64 = base64.encodestring(data)
        attach = self.env['ir.attachment'].create({
            'name': '%s.xls' % (report_name),
            'type': 'binary',
            'datas': data_b64,
        })
        return {
            'type': "ir.actions.act_url",
            'url': "web/content/?model=ir.attachment&id=" + str(
                attach.id) + "&filename_field=datas_fname&field=datas&download=true&filename=" + str(attach.name),
            'target': "self",
            'no_destroy': False,
        }
