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
from io import BytesIO
import base64
import xlwt
import re


class FleetVehicleOdometer(models.TransientModel):
    _name = 'odometer.fleet'

    vehicle_id = fields.Many2one('fleet.vehicle')

    date_start = fields.Datetime('Fecha inicio')
    date_end = fields.Datetime('Fecha Final')

    

    def export_api_tag(self, last_odometer):
        Odometer = self.env['fleet.vehicle.odometer']
        last_odometer = Odometer.search([('vehicle_id', '=', self.vehicle_id.id), ('tag_ids', 'in', [2])], order='id desc',
                                        limit=1)
        
        workbook = xlwt.Workbook(encoding='utf-8')
        sheet = workbook.add_sheet('TAG')
        today = datetime.now().date()
        center = xlwt.easyxf('align: horiz centre')
        file_name = 'Extracto bancario' + str(today)
        sheet.write(0, 0, 'Auto', center)
        sheet.write(0, 1, 'Fecha de consulta', center)
        sheet.write(0, 2, 'Valor', center)
        sheet.write(0, 3, 'Tipo de Consulta', center)

        line = 0

        Odometer = self.env['fleet.vehicle.odometer']
        now = datetime.now()

        config = self.env['ir.config_parameter'].sudo()
        if not config.get_param('api_odometer'):
            raise UserError(
                'Operacion no permitida, contacte al Administrador para activar API TAG y Multas.')
        # fecha1 = datetime.now() - relativedelta(days=1)
        # fecha2 = datetime.now()
        url = str(config.get_param('tag_url')) + \
                  str(config.get_param('odo_user')) + '?'
        # url = 'http://api.smartreport.cl/v2/odometro/klugrent?token=c175289b8a2fca7ce92ecf9ba6f3a6c2&patente=PYFV-13&fecha1=2022-08-31%2006:20:00&fecha2=2022-08-31%2018:30:30'
        params = {
            'token': config.get_param('odo_token'),
            'patente': last_odometer.vehicle_id.license_plate,
            'fecha1': str(self.date_start.strftime("%Y-%m-%d  %H:%M:%S")),
            'fecha2': str(self.date_end.strftime("%Y-%m-%d %H:%M:%S"))
        }
        metodo = []
        qstr = urlencode(params)
        print(json.dumps(params, indent=4, ensure_ascii=False))
        response = requests.post(url+qstr)
        if response.status_code != 200:
            raise UserError(
                'Por favor contacte con el Administrador: %s', response.text)
        dict_list = json.loads(response.text.encode('utf8'))
        if dict_list.get('status') != 0 and dict_list.get('status') != 4:
            pass
            # jamie = dict_list.get('mensaje')
            # raise UserError('Por favor revise el siguiente error: ' + str(dict_list.get('mensaje')))
        if dict_list.get('tag'):
            for tag in dict_list.get('tag'):
                vals_tag = {
                            'vehicle_id': self.id,
                            'date': datetime.strptime(str(tag.get('fecha')), '%d-%m-%Y %H:%M'),
                            'tag_ids': [1],
                            'amount': tag.get('tarifa'),
                            'concession': tag.get('concesion'),
                            'description': tag.get('description'),
                            'category': tag.get('categoria'),
                }
                # Odometer.create(vals_tag)
        if dict_list.get('multa'):
            for tag in dict_list.get('multa'):
                vals_multa = {
                            'vehicle_id': self.id,
                            'date': datetime.strptime(str(tag.get('fecha')), '%d-%m-%Y %H:%M'),
                            'tag_ids': [7],
                            'amount': tag.get('tarifa'),
                            'description': tag.get('via'),
                            'category': tag.get('tipo_multa'),
                }
                # Odometer.create(vals_multa)

        for record in vals_tag:

            line += 1
            sheet.write(line, 0, record.vehicle_id.name)
        fp = BytesIO()
        workbook.save(fp)
        fp.seek(0)
        data = fp.read()
        fp.close()
        data_b64 = base64.encodestring(data)
        doc = self.env['ir.attachment'].create({
            'name': '%s.xls' % (file_name),
            'datas': data_b64,
            'store_fname': '%s.xls' % (file_name),
            'type': 'url'
        })
        return {
            'type': "ir.actions.act_url",
            'url': "web/content/?model=ir.attachment&id=" + str(
                doc.id) + "&filename_field=name&field=datas&download=true&filename=" + str(doc.name),
            'target': "current",
        }


