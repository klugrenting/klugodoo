{   'name': 'Herencia modulo de reparacion de autos',
    'version': '1.0',
    'description': '',
    'summary': '',
    'author': '',
    'website': '',
    'license': 'LGPL-3',
    'category': '',
    'depends': [
        'bi_car_repair_management', 'account', 'sale', 'sale_management', 'maintenance', 'web', 'base', 'portal'
    ],
    'data': [
        "security/ir.model.access.csv",
        #'views/car_management_view.xml',
        'views/sale_order_view.xml',
        'views/maintenance_view.xml',
        'views/maintenance_portal_template.xml',
        'report/car_diagnosys.xml',
        'report/sale_order.xml'
    ],
    'auto_install': False,
    'application': False,
    'assets': {
        
    }
}
