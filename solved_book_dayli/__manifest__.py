# -*- coding: utf-8 -*-
{
    'name': "Solved Book Dayli",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Blueminds",
    'website': "http://blueminds.cl",
    'contribuitors': "Frank Quatromani <fquatromani@blueminds.cl>",
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['account'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'wizard/generate_book_missing_views.xml',
    ],
}