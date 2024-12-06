# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

{
    "name" : "Cron Failure Notification and Activity",
    "version" : "16.0.0.0",
    "category" : "Extra Tools",
    'summary': "Cron Job Failure Notifications cron failure history corn job failure activity corn failure activity history corn failure notification send by email cron job failure email notification cron failure notification cron job failure schedule action failure",
    "description": """
    
        Cron Job Failure Notifications in odoo,
        Add followers in cron failure history in odoo,
        Followers got notificaion if cron job got failure in odoo,
        Cron Failure History in odoo,
        Execute Cron job in odoo,
    
    """,
    "author": "BrowseInfo",
    "website" : "https://www.browseinfo.com",
    "price": 29,
    "currency": 'EUR',
    "depends" : ['base','mail', 'portal', 'base_setup'],
    "data": [
        'security/ir.model.access.csv',
        'views/cron_failure_view.xml',
        'views/ir_cron.xml',
        'reports/ir_cron_fail.xml',
        'reports/ir_cron_fail_report_template.xml',
        'data/mail_template_data.xml',
        
    ],
    'qweb': [],
    'license':'OPL-1',
    "auto_install": False,
    "installable": True,
    "live_test_url":'https://youtu.be/DvWhGavmlWc',
    "images":["static/description/Banner.gif"],
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
