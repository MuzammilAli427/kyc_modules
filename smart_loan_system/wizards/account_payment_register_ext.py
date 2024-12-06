# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _


class AccountPaymentRegisterExt(models.TransientModel):
    _inherit = 'account.payment.register'

    # @api.model
    # def default_get(self, fields):
    #     context = dict(self._context or {})
    #     active_model = context.get('active_model')
    #     active_id = context.get('active_id')
    #     res = super(AccountPaymentRegisterExt, self).default_get(fields)
    #     move = self.env['account.move']
    #     if res.get('move_id', ''):
    #         move = move.search([('id', '=', res.get('move_id', ''))], limit=1)
    #     elif active_model == 'account.move':
    #         move = move.browse(active_id)
    #     if move.loan_id.is_straight_through:
    #         res.update({'journal_id': move.loan_id.payment_journal_id.id})
    #
    #     return res

    def action_create_payments(self):
        res = super(AccountPaymentRegisterExt, self).action_create_payments()
        payment = self.env['account.payment'].search([('ref', '=', self.communication)], order='id desc', limit=1)
        if payment:
            payment.write({'loan_id': self.move_id.loan_id.id})
            self.move_id.write({'custom_payment_id': payment.id})

        res

        return res
