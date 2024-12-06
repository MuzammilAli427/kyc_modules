# -*- coding: utf-8 -*-
from odoo import fields, models

class AccountJournal(models.Model):
    _inherit = 'account.journal'
    
    verification_required = fields.Boolean(string='Verification Required')
    