# -*- coding: utf-8 -*-
{
	'name': "3CX CRM Template full integration",
	'summary': """
		Generates 3CX CRM Template and fully integrate it in Odoo:
        - Contact Search/Create
        - Call Log
        - Livechat Log
        - Open Contact Page
    """,
	'description': """
		Generates 3CX CRM Template and fully integrate it in Odoo:
        - Contact Search/Create
        - Call Log
        - Livechat Log
        - Open Contact Page
	""",
	'author': "Nalios",
	'website': "https://www.nalios.be",
	'category': 'Customizations',
	'version': '16.0.1',
    'license': "OPL-1",
    'price': 290.00,
    'currency': 'EUR',
    'images': ['static/description/main_screenshot.png',],
    'support': 'lop@nalios.be',
	'depends': ['contacts'],
    'external_dependencies': {
        'python': ["phonenumbers"]
    },
	'data': [
		'security/ir.model.access.csv',
        'data/3cx_config.xml',
		'views/3cx_views.xml',
        'views/res_partner_views.xml',
	],
}
