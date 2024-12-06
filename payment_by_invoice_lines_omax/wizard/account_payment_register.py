# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    inv_line_ids = fields.Many2many('account.move.line', 'account_payment_register_inv_line_rel', 'wizard_id', 'inv_line_id',
        string="Invoice Line", copy=False,)
    is_customer_inv = fields.Boolean(string='Is Inv')
    selected_amount = fields.Monetary(currency_field='currency_id', store=True, readonly=False, digits='Product Unit of Measure')
    move_id = fields.Many2one('account.move', string='Move')

    @api.onchange('inv_line_ids','currency_id')
    def _onchange_inv_line_ids(self):
        move = False
        #if self.move_id and self.move_id.move_type == 'out_invoice':
        if self.move_id and (self.move_id.move_type != 'entry'):
            selected_lines_price = self.inv_line_ids.filtered(lambda x: x.select == True).mapped('price_total')
            if selected_lines_price:
                total_amount = sum(selected_lines_price)
                move = self.move_id
                convert_value = move.currency_id._convert(total_amount,self.currency_id, move.company_id,move.invoice_date)
                self.amount = convert_value
                self.selected_amount = convert_value
            else:
                self.selected_amount = False
                self._compute_amount()

    @api.model
    def default_get(self, fields):
        context = dict(self._context or {})
        active_model = context.get('active_model')
        active_id = context.get('active_id')
        res = super(AccountPaymentRegister, self).default_get(fields)
        if active_model == 'account.move':
            move = self.env['account.move'].browse(active_id)
            res.update({'move_id':move.id})
            #if move.move_type == 'out_invoice':
            if move.move_type != 'entry':
                res.update({'is_customer_inv':True})
                invoice_lines = move.invoice_line_ids.filtered(lambda line: line.display_type == 'product' and line.fully_paid == False)    #False changed to 'product' for v_16
                if invoice_lines:
                    res.update({'inv_line_ids': [(6, 0, invoice_lines.ids)]})
                paid_lines = move.invoice_line_ids.filtered(lambda line: line.display_type == 'product' and line.fully_paid == True)    #False changed to 'product' for v_16
                if move.amount_total != move.amount_residual and not paid_lines:
                    res.update({'is_customer_inv':False})
        return res

    @api.onchange('amount')
    def _onchange_amount(self):
        if self.move_id:
            #if self.move_id.move_type == 'out_invoice' and self.selected_amount:
            if (self.move_id.move_type != 'entry') and self.selected_amount:
                if float('{:.2f}'.format(self.amount)) != float('{:.2f}'.format(self.selected_amount)):
                    self.amount = self.selected_amount
                    return {'warning':
                                {'title': 'Warning', 'message': "Cannot allow to change Amount because 'Register payment by invoice line' execute."
                                 }
                            }#Cannot change Amount because invoice lines selected

    @api.depends('source_amount', 'source_amount_currency', 'source_currency_id', 'company_id', 'currency_id', 'payment_date')
    def _compute_amount(self):
        for wizard in self:
            if wizard.source_currency_id == wizard.currency_id:
                # Same currency.
                wizard.amount = wizard.source_amount_currency
            elif wizard.currency_id == wizard.company_id.currency_id:
                # Payment expressed on the company's currency.
                wizard.amount = wizard.source_amount
            else:
                # Foreign currency on payment different than the one set on the journal entries.
                amount_payment_currency = wizard.company_id.currency_id._convert(wizard.source_amount, wizard.currency_id, wizard.company_id, wizard.payment_date)
                wizard.amount = amount_payment_currency
            #custom
            #change payment mode and line selected then set line total as amount
            if wizard.move_id:
                #if wizard.move_id.move_type == 'out_invoice' and wizard.selected_amount:
                if (wizard.move_id.move_type != 'entry') and wizard.selected_amount:
                    wizard.amount = wizard.selected_amount

    def action_create_payments(self):
        res = super(AccountPaymentRegister, self).action_create_payments()
        if self.move_id:
            #if self.move_id.move_type == 'out_invoice':
            if self.move_id.move_type != 'entry':
                selected_lines = self.inv_line_ids.filtered(lambda x: x.select == True)
                for selected_line in selected_lines:
                    selected_line.select = False
                    selected_line.fully_paid = True
                if not selected_lines and self.move_id.payment_state == 'paid' and self.is_customer_inv:
                    for selected_line in self.inv_line_ids:
                        #selected_line.select = False
                        selected_line.fully_paid = True
        return res

    def _create_payment_vals_from_wizard(self, batch_result):  #batch_result added for v_16
        res = super(AccountPaymentRegister, self)._create_payment_vals_from_wizard(batch_result) #batch_result added for v_16
        if self.is_customer_inv and self.inv_line_ids:
            lines = self.inv_line_ids.filtered(lambda l:l.select == True)
            if lines:
                res.update({'paid_inv_line_ids':[(6,0,lines.ids)]})
            else:
                res.update({'paid_inv_line_ids':[(6,0,self.inv_line_ids.ids)]})
        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
