# -*- coding: utf-8 -*-
{
    'name': 'Journal Entry Verification',
    'summary':'Journal entry two step verification, Journal Entries Verification, Account Entry Verification, Entries Approval, JV Approval, Verify Accounting Entries, Accounting Maker Checker, JV Maker Checker, Accounting Maker Checker. JV Maker Checker, Payment Verification',
    'version': '16.0.0.1',
    'category': 'Accounting',
    'author': 'Evozard',
    'website': 'https://evozard.com/',
    'license': 'OPL-1',
    'price': 45,
    'currency': 'USD',    
    'support':'support@evozard.com',
    'description':"""
            Journal Entries Verification. Account Entry Verification
            Entries Approval. JV Approval.
            Verify Accounting Entries. Journal Voucher double Verification.
            Accounting Maker Checker. JV Maker Checker.
    """,    
    'depends': ['account'],
    'data': [
            'security/security.xml',
            'views/account_journal_view.xml',
            'views/account_move_view.xml',
            'views/account_payment_view.xml',
        ],
         
    'images': ["static/description/banner.png"],    
    'installable': True,
    'auto_install': False,
    
}
