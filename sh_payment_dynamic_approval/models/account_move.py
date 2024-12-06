# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies.
from odoo import models,fields


class AccountMove(models.Model):
    _inherit = 'account.move'

    state = fields.Selection(selection_add=[('waiting', 'Waiting for Approval'), (
        'reject', 'Reject'), ('posted',)], ondelete={'waiting': 'cascade', 'reject': 'cascade'})
