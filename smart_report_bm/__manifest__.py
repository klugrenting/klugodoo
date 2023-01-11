# -*- coding: utf-8 -*-
# Copyright (C) 2022 - TODAY, Jescalante@blueminds.cl
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Smart Report Blueminds',
    'version': '15.0',
    'author': 'Blue Minds SpA'
              'Jamie Escalante (jescalante@blueminds.cl)',
    'maintainer': 'Blue Minds SpA',
    'website':  'http://www.blueminds.cl,',
    'license': 'AGPL-3',
    'category': 'API',
    'summary': 'API de smart report',
    'depends': ['base', 'fleet', 'agreement_blueminds'],
    'data': [
           'security/ir.model.access.csv',
           'views/res_config_settings.xml',
           'views/fleet_vehicle_view.xml',
           'views/fleet_vehicle_odometer_view.xml',
           # 'views/zona_ejecutivo_view.xml',
           # 'views/maihue_ejecutivo_view.xml',
           # 'views/menu.xml',
           # 'views/agreement_view.xml'
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
