# -*- coding: utf-8 -*-
# Copyright (C) 2022 - TODAY, Jescalante@blueminds.cl
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Custom Smart Report Blueminds',
    'version': '15.0',
    'author': 'Klug Spa'
              'Daniel Fernandez (daniel@klugrenting.com)',
    'maintainer': 'Klug SpA',
    'website':  'http://www.blueminds.cl,',
    'license': 'AGPL-3',
    'category': 'API',
    'summary': 'API de smart report con cron para que tome los valores automaticamente',
    'depends': ['base', 'fleet', 'agreement_blueminds', 'smart_report_bm'],
    'data': [
           
            'views/fleet_vehicle_odometer_view.xml',
           
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
