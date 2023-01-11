{
    'name': 'Cambios al modulo de flota',
    'version': '1.0',
    'description': '',
    'summary': '',
    'author': '',
    'website': '',
    'license': 'LGPL-3',
    'category': '',
    'depends': [
        'fleet', 'base', 'sale_subscription', 'purchase', 'account', 'theme_prime'
    ],
    'data': [
        'security/ir.model.access.csv',        
        'views/fleet_view.xml',
        'views/portal_view.xml'
    ],

    'auto_install': False,
    'application': False,
    'assets': {

    }
}
