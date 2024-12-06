# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
	'name': 'Partial Payment by Selected Invoice/Bill lines',
	'version': '16.0',
	'category': 'Accounting',
	'author': 'OMAX Informatics',
	'description': """ Partial Payment by Selected Invoice/Bill lines""",
	'summary': """ Partial Payment by Invoice lines,Partial Payment by Bill lines,
	selected lines,selected invoice lines,selected bills lines,
	partial payment by selected invoice lines,partial payment by selected bill lines
	Payment by invoice lines,Payment by bill lines, partial payment,
	payment, partial, register payment by lines,
	partial payment by lines,
	partial payment by inoice lines,partial payment by bill lines
	lines paid report, lines unpaid report,
	lines paid unpaid report,
	partial payment register,Customer payment,
	Customer invoice,Customer bill,customer invoice payment,customer bill payment,
	register payment,payment,partial,customer,invoice,bill,
	paid report,unpaid report,partial payment report,
	report for partial payment,customer payment report,
	customer payment,customer partial payment,
	partial customer payment,paid,unpaid,register payment,
	invoice line,bill line,invoice line payment,bill line payment, line wise payment,
	partial payment,partial payment report,customer invoice report,Vendor bill report,
	customer invoice,Vendor Bill
	 """,
	'website': 'https://www.omaxinformatics.com',
	'depends': [
		'sale','purchase','account', 'stock', 'sale_management', 'purchase_stock',
	],
	'data': [
	    'wizard/account_payment_register.xml',
	    'views/account_move.xml',
	    'report/report.xml',
        'report/report_menu.xml',
	],
	'demo': [],
	'test': [],
    'qweb': [
    ],
    'assets': {
       'web.assets_backend': [
            'payment_by_invoice_lines_omax/static/src/js/account_payment_field.js',
        ],
        'web.assets_qweb': [
            'payment_by_invoice_lines_omax/static/src/xml/**/*',
        ],
    },
	"images": ["static/description/banner.png",],
    'license': 'AGPL-3',
    'currency':'USD',
    'price': 75.0,
    'installable' : True,
    "auto_install" : False,
    "application" : True,
    'live_test_url': 'https://youtu.be/TuUH91kf82k',
    "pre_init_hook": "pre_init_check",
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:        
