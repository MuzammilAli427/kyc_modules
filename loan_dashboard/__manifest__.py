{
    'name': 'loan_dashboard',
    'summary': 'loan_dashboard',
    'version': '1.0.0',
    'author': '',
    'category': 'General',
    'description': 'loan_dashboard',
    'depends': ['smart_loan_system','web'],
    'data': [
    	'security/ir.model.access.csv',
        'views/dashboard_webclient_view.xml'
    ],

    'assets': {
        'web.assets_backend': [
    		'loan_dashboard/static/**/*.js',
    		'loan_dashboard/static/**/*.xml',
    		'loan_dashboard/static/**/*.css'
        ],
        'web.assets_frontend': []

    },
    'installable': True,
    'application': True,
    'auto_install': False,

}

