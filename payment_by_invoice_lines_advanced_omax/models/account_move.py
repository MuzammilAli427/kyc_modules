# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class AccountMove(models.Model):
    _inherit = "account.move"

    @api.depends('invoice_line_ids.fully_paid','invoice_line_ids.partial_paid')
    def _compute_pay_by_line_execute(self):
        for move in self:
            move.pay_by_line_execute = False
            #if move.move_type == 'out_invoice':
            if move.move_type != 'entry':
                paid_lines = move.invoice_line_ids.filtered(lambda line: line.display_type == 'product' and (line.fully_paid == True or line.partial_paid == True))
                if paid_lines and move.payment_state in ['in_payment','paid','partial']:
                    self.pay_by_line_execute = True

    # def button_draft(self):
    #     #if self.move_type == 'out_invoice':
    #     if self.move_type == 'out_invoice' or self.move_type == 'in_invoice':
    #         lines = self.invoice_line_ids.filtered(lambda l:l.display_type == 'product' and (l.partial_paid or l.fully_paid))
    #         for line in lines:
    #             line.partial_paid = False
    #             line.paid_amount = False
    #             line.unpaid_amount = False
    #             line.fully_paid = False
    #             line.select = False
    #         if self.payment_state in ['in_payment','paid','partial'] and lines:
    #             payments = self.env['account.payment'].search([('reconciled_invoice_ids','in',self._origin.id),('paid_inv_line_ids', '!=', False), ('payment_inv_line', '!=', False)])
    #             if payments:
    #                 for payment in payments:
    #                     payment.paid_inv_line_ids = False
    #                     payment.payment_inv_line = False
    #     res = super(AccountMove, self).button_draft()
    #     return res

    def js_remove_outstanding_partial(self, partial_id):
        if self._context.get('payment_main_id'):
            payment_id = self._context.get('payment_main_id')
            payment_rec = self.env['account.payment'].browse(payment_id)
            if payment_rec.reconciled_invoice_ids:
                for move in payment_rec.reconciled_invoice_ids:
                    #if move.move_type == 'out_invoice':
                    if move.move_type != 'entry':
                        if payment_rec.payment_inv_line:
                            for line in payment_rec.payment_inv_line:
                                move_line = line.move_line_id 
                                move_line.paid_amount -= line.paid_amount
                                move_line.unpaid_amount -= line.paid_amount
                                payment_rec.paid_inv_line_ids -= move_line
                                move_line.select = False
                                if move_line.price_total == line.paid_amount:
                                    move_line.fully_paid = False
                                if move_line.price_total != line.paid_amount:
                                    move_line.partial_paid = True
                                    move_line.fully_paid = False
                                if not move_line.paid_amount:
                                    move_line.partial_paid = False
                                    move_line.fully_paid = False
                            payment_rec.payment_inv_line = False
        res = super(AccountMove, self).js_remove_outstanding_partial(partial_id)
        return res


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    paid_amount = fields.Monetary(currency_field='currency_id', store=True, readonly=False, digits='Product Unit of Measure', string='Paid',copy=0)
    unpaid_amount = fields.Monetary(currency_field='currency_id', store=True, readonly=False, digits='Product Unit of Measure',string='Un-Paid',copy=0, default=lambda self: self.price_unit * self.quantity)
    partial_paid = fields.Boolean('Partial Paid', copy=0)

    @api.onchange('unpaid_amount')
    def _onchange_unpaid_amount(self):
        unpaid_amount = float('{:.2f}'.format(self.unpaid_amount))
        if (self.price_total - self.paid_amount) < unpaid_amount:
            raise UserError(_("Unpaid amount is bigger than remaining Amount."))


class AccountPayment(models.Model):
    _inherit = "account.payment"

    payment_inv_line = fields.One2many('account.payment.inv.line', 'payment_id', string='Paid Inv Line', copy=False,)

    def action_draft(self):
        ''' posted -> draft '''
        if self.reconciled_invoice_ids:
            for move in self.reconciled_invoice_ids:
                #if move.move_type == 'out_invoice':
                if move.move_type != 'entry':
                    if self.payment_inv_line:
                        for line in self.payment_inv_line:
                            move_line = line.move_line_id 
                            move_line.paid_amount -= line.paid_amount
                            move_line.unpaid_amount += line.paid_amount
                            self.paid_inv_line_ids -= move_line

                            move_line.select = False

                            if move_line.price_total == line.paid_amount:
                                move_line.fully_paid = False
                            if move_line.price_total != line.paid_amount:
                                move_line.partial_paid = True
                                move_line.fully_paid = False
                            if not move_line.paid_amount:
                                move_line.partial_paid = False
                                move_line.fully_paid = False
                        self.payment_inv_line = False
        if self.paid_inv_line_ids:
            self.paid_inv_line_ids = False
        res = super(AccountPayment, self).action_draft()
        return res

class AccountPaymentInvLine(models.Model):
    _name = "account.payment.inv.line"
    _description = "Account Payment Invoice Line"

    name = fields.Char('Name')
    payment_id = fields.Many2one('account.payment', string='Payment')#o2m
    move_line_id = fields.Many2one('account.move.line', string='Move Line')
    currency_id = fields.Many2one(related='move_line_id.currency_id')
    paid_amount = fields.Monetary(currency_field='currency_id', store=True, readonly=False, digits='Product Unit of Measure', string='Paid')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
