# -*- coding: utf-8 -*-
{
    'name': "Cesión de Facturas",

    'summary': """
        Proceso de cesión de facturas
    """,

    'description': """
        Proceso de cesión de facturas
    """,

    'author': "Blueminds",
    'website': "http://blueminds.cl",
    'contribuitors': "Frank Quatromani <fquatromani@blueminds.cl>",
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'account',
        'l10n_cl',
        'l10n_cl_edi',
        'l10n_latam_invoice_document',
    ],

    # always loaded
    'data': [
        'template/dte_factoring.xml',
        'views/account_move_views.xml'
    ],
    
    'installable': True,
    'auto_install': False,
    'demo': [],
    'test': [],
}
