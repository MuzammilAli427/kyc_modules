# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies.
from odoo import models, fields, api, _


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    def _reconcile_payments(self, to_process, edit_mode=False):
        for vals in to_process:
            vals['payment'].sh_to_reconcile=vals['to_reconcile']
        super()._reconcile_payments( to_process, edit_mode=False)
