# -*- coding: utf-8 -*-

{
    "name": "GSH Reporting",
    "version": "16.0.0.1",
    "category": "Extra Tools",
    "description": """""",
    "depends": ["account", "account_reports"],
    "data": [
        "security/ir.model.access.csv",
        "wizard/gsh_wizard_view.xml",
        "wizard/gsh_report.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "gsh_reporting/static/src/js/action_manager.js",
        ],
    },
    "installable": True,
    "license": "LGPL-3",
}
