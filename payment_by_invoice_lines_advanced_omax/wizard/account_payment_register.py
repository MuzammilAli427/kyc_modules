# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    @api.onchange('inv_line_ids','currency_id')
    def _onchange_inv_line_ids(self):
        move = False
        #if self.move_id and self.move_id.move_type == 'out_invoice':
        if self.move_id and (self.move_id.move_type != 'entry'):
            #selected_lines_price = self.inv_line_ids.filtered(lambda x: x.select == True).mapped('price_total')
            selected_lines_price = self.inv_line_ids.filtered(lambda x: x.select == True).mapped('unpaid_amount')
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
            #if move.move_type == 'out_invoice':
            if move.move_type != 'entry':
                res.update({'is_customer_inv':True})
                invoice_lines = move.invoice_line_ids.filtered(lambda line: line.display_type == 'product' and line.fully_paid == False)
                if invoice_lines:
                    for line in invoice_lines:
                        if not line.unpaid_amount:
                            line.unpaid_amount = line.price_total
                        else:
                            line.unpaid_amount = line.price_total - line.paid_amount
                            pass
                    res.update({'inv_line_ids': [(6, 0, invoice_lines.ids)]})

                paid_lines = move.invoice_line_ids.filtered(lambda line: line.display_type == 'product' and (line.fully_paid == True or line.partial_paid == True))
                if move.amount_total != move.amount_residual and not paid_lines:
                    res.update({'is_customer_inv':False})
        return res

    def action_create_payments(self):
        selected_lines = []
        if self.move_id:
            #if self.move_id.move_type == 'out_invoice':
            if self.move_id.move_type != 'entry':
                selected_lines = self.inv_line_ids.filtered(lambda x: x.select == True)
        res = super(AccountPaymentRegister, self).action_create_payments()
        for sel_line in selected_lines:
            sel_line.select = False
            sel_line.paid_amount += sel_line.unpaid_amount
            sel_line.unpaid_amount = sel_line.price_total - sel_line.paid_amount
            sel_line.paid_amount = sel_line.paid_amount
            if round(sel_line.paid_amount,2) == round(sel_line.price_total,2):
                sel_line.fully_paid = True
                sel_line.partial_paid = False
            else:
                sel_line.fully_paid = False
                sel_line.partial_paid = True
        if not selected_lines and self.move_id.payment_state == 'paid' and self.is_customer_inv:
            for sel_line in self.inv_line_ids:
                sel_line.fully_paid = True
                sel_line.partial_paid = False
                sel_line.paid_amount = sel_line.price_total
                sel_line.unpaid_amount = sel_line.price_total - sel_line.paid_amount
        return res

    def _create_payment_vals_from_wizard(self,batch_result):
        lines = self.inv_line_ids.filtered(lambda l:l.select == True)
        payment_res = {}
        if self.is_customer_inv and self.inv_line_ids and self.move_id:
            lines = self.inv_line_ids.filtered(lambda l:l.select == True)
            if lines:
                payment_res.update({'paid_inv_line_ids':[(6,0,lines.ids)]})
            else:
                if round(self.move_id.amount_residual,2) == round(self.amount,2):
                    payment_res.update({'paid_inv_line_ids':[(6,0,self.inv_line_ids.ids)]})
            payment_inv_line_lst = []
            for line in lines or self.inv_line_ids:
                if not lines and round(self.move_id.amount_residual,2) == round(self.amount,2):
                    payment_inv_line_lst.append((0, 0, 
                        {'name':line.name,
                         'move_line_id':line.id,
                         'paid_amount':line.unpaid_amount,
                        }))
                if lines:
                    payment_inv_line_lst.append((0, 0, 
                        {'name':line.name,
                         'move_line_id':line.id,
                         'paid_amount':line.unpaid_amount,
                        }))
            if payment_inv_line_lst:
                payment_res.update({'payment_inv_line':payment_inv_line_lst})
        res = super(AccountPaymentRegister, self)._create_payment_vals_from_wizard(batch_result)

        res.update(payment_res)
        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
