# -*- coding: utf-8 -*-
# Copyright (C) 2022 - TODAY, Jescalante@blueminds.cl
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.osv import expression
from odoo.addons.fleet.models.fleet_vehicle_model import FUEL_TYPES
import base64
import json
import requests
from urllib.request import urlretrieve
from urllib.parse import urlencode
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime


class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    incidencia_line = fields.One2many(
        'fleet.vehicle.incidencia', 'vehicle_id', string='Incidencias')

    def api_odometer_cron(self):
        Odometer = self.env['fleet.vehicle.odometer']
        vehicle_ids = self.env['fleet.vehicle'].search([('state_id', '=', 3)])
        for record in vehicle_ids:
            
            last_odometer = Odometer.search([('vehicle_id', '=', record.id), ('tag_ids', 'in', [2])], order='id desc',
                                            limit=1)
            if last_odometer:
                self.call_api_odometer_cron(last_odometer)
                self.call_api_tag_cron(last_odometer)
        
        
        

    def hide_api_odo(self):
        self.api_odo = self.company_id.api_odometer

    def hide_api_tag(self):
        self.api_tag = self.company_id.api_tag

    api_odo = fields.Boolean(computed=hide_api_odo)
    api_tag = fields.Boolean(computed=hide_api_tag)

    def call_api_tag_cron(self, last_odometer):
        Odometer = self.env['fleet.vehicle.odometer']
        now = datetime.now()
        
        config = self.env['ir.config_parameter'].sudo()
        if not config.get_param('api_odometer'):
            raise UserError('Operacion no permitida, contacte al Administrador para activar API TAG y Multas.')
        # fecha1 = datetime.now() - relativedelta(days=1)
        # fecha2 = datetime.now()
        url = str(config.get_param('tag_url')) + str(config.get_param('odo_user')) + '?'
        # url = 'http://api.smartreport.cl/v2/odometro/klugrent?token=c175289b8a2fca7ce92ecf9ba6f3a6c2&patente=PYFV-13&fecha1=2022-08-31%2006:20:00&fecha2=2022-08-31%2018:30:30'
        license_plate = last_odometer.vehicle_id.license_plate[:-2] + "-" + last_odometer.vehicle_id.license_plate[4:6]
        params = {
            'token': config.get_param('odo_token'),
            'patente': license_plate,
            'fecha1': str(last_odometer.date.strftime("%Y-%m-%d  %H:%M:%S")),
            'fecha2': str(now.strftime("%Y-%m-%d %H:%M:%S"))
        }
        metodo = []
        qstr = urlencode(params)
        print(json.dumps(params, indent=4, ensure_ascii=False))
        response = requests.post(url+qstr)
        if response.status_code != 200:
            raise UserError('Por favor contacte con el Administrador: %s', response.text)
        dict_list = json.loads(response.text.encode('utf8'))
        if dict_list.get('status') != 0 and dict_list.get('status') != 4:
            pass
            # jamie = dict_list.get('mensaje')
            # raise UserError('Por favor revise el siguiente error: ' + str(dict_list.get('mensaje')))
        if dict_list.get('tag'):
            for tag in dict_list.get('tag'):
                vals_tag = {
                            'vehicle_id': last_odometer.vehicle_id.id,
                            'date': datetime.strptime(str(tag.get('fecha')), '%d-%m-%Y %H:%M'),
                            'tag_ids': [1],
                            'amount': tag.get('tarifa'),
                            'concession': tag.get('concesion'),
                            'description': tag.get('description'),
                            'category': tag.get('categoria'),
                }
                Odometer.create(vals_tag)
        if dict_list.get('multa'):
            for tag in dict_list.get('multa'):
                vals_multa = {
                            'vehicle_id': last_odometer.vehicle_id.id,
                            'date': datetime.strptime(str(tag.get('fecha')), '%d-%m-%Y %H:%M'),
                            'tag_ids': [7],
                            'amount': tag.get('tarifa'),
                            'description': tag.get('via'),
                            'category': tag.get('tipo_multa'),
                }
                Odometer.create(vals_multa)
        if dict_list.get('incidencia'):
            for tag in dict_list.get('incidencia'):
                vals_incidencia = {
                                'vehicle_id': last_odometer.vehicle_id.id,
                                'date': datetime.strptime(str(tag.get('fecha')), '%d-%m-%Y'),
                                'name': tag.get('proveedor'),
                                'mensaje': tag.get('mensaje'),
                                'mensaje_consul': dict_list.get('mensaje'),
                }
                self.env['fleet.vehicle.incidencia'].create(vals_incidencia)



    def call_api_odometer_cron(self, last_odometer):
        
        Odometer = self.env['fleet.vehicle.odometer']
        now = datetime.now()
        config = self.env['ir.config_parameter'].sudo()
        if not config.get_param('api_odometer'):
            raise UserError('Operacion no permitida, contacte al Administrador para activar API TAG y Multas.')
        # fecha1 = datetime.now() - relativedelta(days=1)
        # fecha2 = datetime.now()
        url = str(config.get_param('odo_url')) + str(config.get_param('odo_user')) + '?'
        # url = 'http://api.smartreport.cl/v2/odometro/klugrent?token=c175289b8a2fca7ce92ecf9ba6f3a6c2&patente=PYFV-13&fecha1=2022-08-31%2006:20:00&fecha2=2022-08-31%2018:30:30'
        license_plate = last_odometer.vehicle_id.license_plate[:-2] + "-" + last_odometer.vehicle_id.license_plate[4:6]
        params = {
            'token': config.get_param('odo_token'),
            'patente': license_plate, # 'PYFV-59',
            'fecha1': str(last_odometer.date.strftime("%Y-%m-%d  %H:%M:%S")),
            'fecha2': str(now.strftime("%Y-%m-%d %H:%M:%S"))
        }
        metodo = []
        qstr = urlencode(params)
        print(json.dumps(params, indent=4, ensure_ascii=False))
        response = requests.post(url + qstr)
        if response.status_code != 200:
            pass
            # raise UserError('Por favor contacte con el Administrador: %s', response.text)
        dict_list = json.loads(response.text.encode('utf8'))
        if dict_list.get('status') != 0:
            pass
            # jamie = dict_list.get('mensaje')
            # raise UserError('Por favor revise el siguiente error: ' + str(dict_list.get('mensaje')))
        ult_valor = last_odometer.value
        if dict_list.get('data'):
            for tag in dict_list.get('data'):
                valor = float(tag.get('odometro')) / 1000
                ult_valor = float(ult_valor) + float(valor)
                vals_data = {
                            'vehicle_id': last_odometer.vehicle_id.id,
                            'date': datetime.strptime(str(tag.get('fecha')), '%d-%m-%Y %H:%M'),
                            'value': ult_valor,
                            'tag_ids': [2],
                }
                Odometer.create(vals_data)