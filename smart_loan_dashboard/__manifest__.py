# -*- coding: utf-8 -*-
###################################################################################
{
    'name': 'Smart Loan Dashboard',
    'version': '1.0',
    'category': 'Dashboard',
    'summary': 'This Module is Displaying Dashboard Analysis of financials.',
    'description': 'Smart Loan Dashboard: Financial data with trendy graphs.',
    'author': 'Muzammil Ali',
    'website': 'http://warlocktechnologies.com',
    'depends': ['wt_financial_dashboard'],
    'data': [
        'views/smart_loan_dasboard_view.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'smart_loan_dashboard/static/src/components/**/*.js',
            'smart_loan_dashboard/static/src/components/**/*.xml',
            'smart_loan_dashboard/static/src/**/*.scss',
        ]
    },
    'installable': True,
    'application': True,
    'license': 'OPL-1',
}
