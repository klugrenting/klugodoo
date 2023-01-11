# Copyright (C) 2022 - TODAY, Jescalante@blueminds.cl
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import re
from odoo import fields, models, api
from odoo.exceptions import Warning, UserError
from stdnum import get_cc_module

class Partner(models.Model):
    _inherit = "res.partner"

    def _get_contact_name(self, partner, name):
        res = super(Partner, self)._get_contact_name(partner, name)
        res = name
        return res

    def get_ep(self):
        return [1, 4, 5]

    agreement_ids = fields.One2many(
        "agreement",
        "partner_id",
        string="Agreements")
    etiqueta_person = fields.Many2many('etiqueta.person', 'etiqueta_person_rel', 'person_id',
                                             'partner_id', default=get_ep,
                                             string='Tipo de persona')
    type_contrib = fields.Many2one(
        "agreement.type.contrib", required=False,
        string="Tipo de Contribuyente", domain=[("code", "not in", ['ig','na','igp'])])

    commune = fields.Many2one('res.country.commune', 'Comuna')

    l10n_latam_identification_type_id = fields.Many2one('l10n_latam.identification.type',
        string="Identification Type", index=True, auto_join=True,
        default=lambda self: self.env.ref('l10n_latam_base.it_vat', raise_if_not_found=False),
        help="The type of identification")
    vat = fields.Char(string='Identification Number', help="Identification Number for selected type")

    add_another_number = fields.Boolean(string="Agregar otro numero")
    add_another_number1 = fields.Boolean(string="+")
    add_another_number2 = fields.Boolean(string="+")
    add_another_number3 = fields.Boolean(string="+")
    phone0 = fields.Char(string="Teléfono0")
    phone1 = fields.Char(string="Teléfono1")
    phone2 = fields.Char(string="Teléfono2")
    phone3 = fields.Char(string="Teléfono3")
    phone4 = fields.Char(string="Teléfono4")
    etiqueta_telefono = fields.Selection([('movil', 'Movil'), ('trabajo', 'Trabajo'), ('casa', 'Casa'), ('otro', 'Otro')], string="Categorias")
    etiqueta1 = fields.Selection([('movil', 'Movil'), ('trabajo', 'Trabajo'), ('casa', 'Casa'), ('otro', 'Otro')], string="Categorias")
    etiqueta2 = fields.Selection([('movil', 'Movil'), ('trabajo', 'Trabajo'), ('casa', 'Casa'), ('otro', 'Otro')], string="Categorias")
    etiqueta3 = fields.Selection([('movil', 'Movil'), ('trabajo', 'Trabajo'), ('casa', 'Casa'), ('otro', 'Otro')], string="Categorias")
    etiqueta4 = fields.Selection([('movil', 'Movil'), ('trabajo', 'Trabajo'), ('casa', 'Casa'), ('otro', 'Otro')], string="Categorias")
    means_ids = fields.Many2many('means', string="Recursos")
    capabilities_ids = fields.Many2many('capabilities', string="Capacidades")
    geolocation_x = fields.Char(string="Geolocalización X")
    geolocation_y = fields.Char(string="Geolocalización Y")
    geolocation_url = fields.Char(string="Geolocalización URL")
    phone_code = fields.Integer('Codigo de llamada de pais')
    sucursal = fields.Char(string="Sucursal")
    zona_comercial = fields.Many2one('zona.comercial', string='Zona')
    fact_integral = fields.Selection([('integral', 'Integral Cliente'), ('contrato', 'Separada por Contrato')],
                                 string="Tipo de Facturación", default='contrato')
    status_payment = fields.Selection(
        [('al', 'Al Día'), ('atr', 'Atrasado')], string='Payment status')
    status_method_payment = fields.Char(string='Payment Method Status')
    vinculation_id = fields.Many2one('res.partner', string='Vinculation Contact', index=True)

    @api.onchange('company_type')
    def onchange_company_type(self):
        if self.company_type == 'company':
            type_contrib = self.env['agreement.type.contrib'].search([
                ('code', '=', 'J')], limit=1)
            self.type_contrib = type_contrib.id
        else:
            type_contrib = self.env['agreement.type.contrib'].search([
                ('code', '=', 'N')], limit=1)
            self.type_contrib = type_contrib.id

    @api.onchange('type_contrib')
    def onchange_type_contrib(self):
        if self.type_contrib.code == 'J':
            self.l10n_cl_sii_taxpayer_type = '1'
        if self.type_contrib.code == 'N':
            self.l10n_cl_sii_taxpayer_type = '3'
        if self.type_contrib.code == 'PE':
            self.l10n_cl_sii_taxpayer_type = '4'
        if self.type_contrib.code == 'PBH':
            self.l10n_cl_sii_taxpayer_type = '2'


    def validate_phone(self, phone):
        if self.country_id.name == 'Chile':
            numero = list(phone)
            for num in numero:
                if not num.isdigit():
                    raise UserError("El campo |Teléfono| debe tener unicamente valores numericos")
            if len(numero) == 9:
                res_country_code = self.country_id.phone_code
                cod_area_f = str(res_country_code)
                numero1 = '+' + cod_area_f + phone
                phone = numero1
            else:
                raise UserError('El campo |Teléfono| Debe tener 9 digitos')
        return phone



    @api.onchange('mobile', 'phone0', 'phone1', 'phone2', 'phone3', 'phone4')
    def activate_phone_validation(self):
        for record in self:
            if record.country_id.name == 'Chile':
                if record.mobile:
                    record.validate_phone(record.mobile)
            if record.phone0:
                record.validate_phone(record.phone0)
            if record.phone1:
                record.validate_phone(record.phone1)
            if record.phone2:
                record.validate_phone(record.phone2)
            if record.phone3:
                record.validate_phone(record.phone3)
            if record.phone4:
                record.validate_phone(record.phone4)


    @api.onchange('email')
    def validate_email(self):
        if self.email:
            email_format = re.compile(r"[^@]+@[^@]+\.[^@]+")
            if not email_format.match(self.email):
                raise UserError("El campo |Correo electrónico| tiene un formato invalido")


    @api.onchange('vat')
    def validate_rut(self):
        mod = get_cc_module('cl', 'rut')
        if self.country_id.name == 'Chile':
            if self.vat:
                val_rut = mod.is_valid(self.vat)
                if val_rut == False:
                    raise UserError("El rut ingresado |{0}| no es valido".format(self.vat))


    @api.onchange('country_id')
    def place_code_according_to_country(self):
        if self.country_id:
            code = self.country_id.phone_code
            self.phone_code = code
        else:
            self.phone_code = 0

    @api.model
    def create(self, vals):
        if vals.get('parent_id'):
            name = ''
            if vals.get('type') == 'other' or vals.get('type') == 'delivery':
                comuna = self.env['res.country.commune'].search([('id', '=', vals['commune'])])
                if vals['street']:
                    name = str(vals['street'])
                if comuna:
                    name = name + ' ' +str(comuna.name)
                if vals['street2']:
                    name = name + ' ' +str(vals['street2'])
                if vals['sucursal']:
                    name = name + ' ' +str(vals['sucursal'])
                vals['name'] = name

        res = super(Partner, self).create(vals)
        if res.company_type == 'person':
            contact_values = {
                    'name': res.name,
                    'sucursal': res.sucursal,
                    'title': res.title,
                    'function': res.function,
                    'country_id': res.country_id.id,
                    'comment': res.comment,
                    'email': res.email,
                    'l10n_latam_identification_type_id': res.l10n_latam_identification_type_id.id,
                    'vat': res.vat,
                    'etiqueta_person': res.etiqueta_person.ids,
                    'phone_code': res.phone_code,
                    'phone0': res.phone0,
                    'phone1': res.phone1,
                    'phone2': res.phone2,
                    'phone3': res.phone3,
                    'phone4': res.phone4,
                    'etiqueta_telefono': res.etiqueta_telefono,
                    'etiqueta1': res.etiqueta1,
                    'etiqueta2': res.etiqueta2,
                    'etiqueta3': res.etiqueta3,
                    'etiqueta4': res.etiqueta4,
                    'add_another_number': res.add_another_number,
                    'add_another_number1': res.add_another_number1,
                    'add_another_number2': res.add_another_number2,
                    'add_another_number3': res.add_another_number3,
                    'parent_id': res.id,
                    'type': 'contact',
            }
            child = super(Partner, self).create(contact_values)
            res.write({'vinculation_id': child.id})
        return res


    def write(self, values):
        if self.parent_id:
            name = ''
            if self.type == 'other' or self.type == 'delivery':
                if 'street' in values or 'street2' in values or 'commune' in values or 'sucursal' in values:
                    if 'commune' in values:
                        comuna = self.env['res.country.commune'].search([('id', '=', values['commune'])])
                    else:
                        comuna = self.env['res.country.commune'].search([('id', '=', self.commune.id)])
                    if 'street' in values:
                        name = str(values['street'])
                    else:
                        name = str(self.street)
                    if comuna:
                        name = name + ' ' + str(comuna.name)
                    if 'street2' in values:
                        name = name + ' ' + str(values['street2'])
                    else:
                        name = name + ' ' + str(self.street2)
                    if 'sucursal' in values:
                        name = name + ' ' + str(values['sucursal'])
                    else:
                        name = name + ' ' + str(self.sucursal)
                    values['name'] = name
        if self.vinculation_id:
            self.vinculation_id.write(values)
        return super(Partner, self).write(values)

    # @api.model
    # def write(self, vals):
    #     if self.parent_id:
    #         name = ''
    #         if self.type == 'other' or self.type == 'delivery':
    #             if 'street' in vals or 'street2' in vals or 'commune' in vals or 'sucursal' in vals:
    #                 comuna = self.env['res.country.commune'].search([('id', '=', vals['commune'])])
    #                 if vals['street']:
    #                     name = str(vals['street'])
    #                 if comuna:
    #                     name = ' ' + str(comuna.name)
    #                 if vals['street2']:
    #                     name = ' ' + str(vals['street2'])
    #                 if vals['sucursal']:
    #                     name = ' ' + str(vals['sucursal'])
    #                 vals['name'] = name
    #     return super(Partner, self).write()

    @api.constrains('parent_id')
    def _check_parent_id(self):
        if not self._check_recursion():
            return True
            #raise ValidationError(_('You cannot create recursive Partner hierarchies.'))


class EtiquetaPerson(models.Model):
    _name = 'etiqueta.person'
    _description = 'Etiqueta Tipo de persona'

    name = fields.Char('Nombre')

class ResCountryStateRegion(models.Model):
    _name = 'res.country.state.region'
    _description = 'Region of a state'

    name = fields.Char(string='Region Name', required=True,
                       help='The state code.')
    code = fields.Char(string='Region Code', required=True,
                       help='The region code.')
    # child_ids = fields.One2many('res.country.state', 'region_id',
    #                             string='Child Regions')


class ResCountryProvinces(models.Model):
    _name = 'res.country.provinces'
    _description = "Res Country Provinces"

    name = fields.Char('Nombre', size=30)
    code = fields.Char('Código', size=30)
    state_id = fields.Many2one('res.country.state', 'Región')

class ResCountryCommune(models.Model):
    _name = 'res.country.commune'
    _description = "Res Country Commune"

    name = fields.Char('Nombre', size=30)
    code = fields.Char('Código', size=30)
    prov_id = fields.Many2one('res.country.provinces', 'Provincia')
