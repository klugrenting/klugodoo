{
    'name': 'Contratos en subscripciones',
    'version': '1.0',
    'description': '',
    'summary': '',
    'author': '',
    'website': '',
    'license': 'LGPL-3',
    'category': '',
    'depends': [
        'sale_subscription', 'sale', 'portal'
    ],
    'data': [
        #'security/ir.model.access.csv',
        'report/agreement.xml',
        'report/agreement_delivery.xml',
        'report/agreement_defund.xml',
        #'wizard/subscription_invoice.xml',
        'views/portal_agreement.xml',
        'views/subscription_view.xml'

    ],

    'auto_install': False,
    'application': False,
    'assets': {

    }
}
