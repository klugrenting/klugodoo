{
    'name': 'Generación de facturas',
    'version': '0.1',
    'category': 'Uncategorized',
    'summary': 'Modulo para agrupacion de Facturas',
    'description': 'Modulo para agrupacion de Facturas',
    'author': 'Blueminds',
    'website': 'https://blueminds.cl',
    'contribuitors': 'Boris Silva <bsilva@blueminds.cl>'
               'Frank Quatromani <fquatromani@blueminds.cl>',
    'depends': [
        'account', 'sale', 'sale_renting', 'agreement_blueminds'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/account_move_view.xml',
        'wizard/invoice_gen_wzd.xml',
        'data/invoice_move_data.xml',
        'views/sale_view.xml',
        'views/invoice_generation_queue_views.xml',
    ],
    'installable': True,
    'auto_install': False,
}