# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies.

{
    "name": "Payment Dynamic Approval | Account Payment Approvals | Dynamic Payment Approval | Payment Approval Process | Payment Rejection",
    "author": "Softhealer Technologies",
    "website": "https://www.softhealer.com",
    "support": "support@softhealer.com",
    "category": "Accounting",
    "summary": "Dynamic Payment Approval Dynamic Payments Approval Payment Multi Approval Payment Multiple Approval Payments Multi Approval Payments Multiple Approval Double Approval Payment Double Approval Payment Dynamic Approvals User Wise Approval Group Wise Approval Reject Payment Approve Payment Validation Invoice Appprove Payment Approve Bill Appprove Credit Note Appprove Debit Note Appprove Refund Appprove Invoice Approval Bill Approval Odoo",
    "description": """This module allows you to set dynamic and multi-level approvals in payments can be approved by many levels. Payment can be approved by particular users or groups they get emails notification about payment that waiting for approval. When a payment approves or rejects user gets a notification about it.""",
    "version": "16.0.3",
    "depends": ["account", "bus","sh_base_dynamic_approval", "payment_by_invoice_lines_advanced_omax"],
    "data": [
        'security/ir.model.access.csv',
        'data/mail_data.xml',
        'views/sh_approval_info_views.xml',
        'views/sh_payment_approval_config_line_views.xml',
        'views/sh_payment_approval_config_views.xml',
        'wizard/sh_rejection_wizard_views.xml',
        'views/account_payment_views.xml',
    ],


    "auto_install": False,
    "installable": True,
    "application": True,
    "license": "OPL-1",
    "images": ["static/description/background.png", ],
    "price": 30,
    "currency": "EUR"
}
