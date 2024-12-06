# -*- coding: utf-8 -*-
###################################################################################
{
    'name':'Financial Dashboard',
    'version':'1.0',
    'category':'Dashboard',
    'summary':'This Module is Displaying Dashboard Analysis of financials.',
    'description':'Financial data with trendy graphs.',
    'author': 'Warlock Technologies Pvt Ltd.',
    'website': 'http://warlocktechnologies.com',
    'support': 'support@warlocktechnologies.com',
    'depends':['account', 'web', 'account_reports', 'base', 'sale_management'],
    'data':[
        'views/wt_dashboard.xml',
    ],
    'assets':{
        'web.assets_frontend':[
        ],
        'web.assets_common':[
            
         ],
         'web.assets_backend':[
             'https://pro.fontawesome.com/releases/v5.10.0/css/all.css',
             'wt_financial_dashboard/static/src/components/**/*.js',
             'wt_financial_dashboard/static/src/components/**/*.xml',
             'wt_financial_dashboard/static/src/scss/style.scss',
         ]
    },
    'images':['images/screen_image.png'],
    'installable': True,
    'application': True,
    'license': 'OPL-1',
    'price' : 150.00,
    'currency' : 'USD',
    'external_dependencies': {
    },
}