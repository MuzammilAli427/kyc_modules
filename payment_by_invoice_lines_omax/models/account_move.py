# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class AccountMove(models.Model):
    _inherit = "account.move"

    pay_by_line_execute = fields.Boolean('Payment by Line', copy=0, compute='_compute_pay_by_line_execute', store=True)

    @api.depends('invoice_line_ids.fully_paid')
    def _compute_pay_by_line_execute(self):
        for move in self:
            move.pay_by_line_execute = False
            #if move.move_type == 'out_invoice':
            if move.move_type != 'entry':
                paid_lines = move.invoice_line_ids.filtered(lambda line: line.display_type == 'product' and line.fully_paid == True) #False changed to 'product' for v_16
                if paid_lines and move.payment_state in ['in_payment','paid','partial']:
                    self.pay_by_line_execute = True

    def button_draft(self):
        res = super(AccountMove, self).button_draft()
        #if self.move_type == 'out_invoice':
        if self.move_type != 'entry':
            for line in self.invoice_line_ids: #False changed to 'product' for v_16
                line.write({'unpaid_amount': line.price_total,
                            'paid_amount': 0.0,
                            'fully_paid': False,
                            'select': False,
                            'partial_paid': line.partial_paid})
        return res

    def js_remove_outstanding_partial(self, partial_id):
        ''' Called by the 'payment' widget to remove a reconciled entry to the present invoice.
        :param partial_id: The id of an existing partial reconciled with the current invoice.
        '''
        if self._context.get('payment_main_id'):
            payment_id = self._context.get('payment_main_id')
            payment_rec = self.env['account.payment'].browse(payment_id)
            if payment_rec.reconciled_invoice_ids:
                for move in payment_rec.reconciled_invoice_ids:
                    #if move.move_type == 'out_invoice':
                    if move.move_type != 'entry':
                        if payment_rec.paid_inv_line_ids:
                            for line in move.invoice_line_ids.filtered(lambda l:l.id in payment_rec.paid_inv_line_ids.ids):
                                line.fully_paid = False
                                line.select = False
                            payment_rec.paid_inv_line_ids = False
        res = super(AccountMove, self).js_remove_outstanding_partial(partial_id)
        return res

    def _get_inv_pay_report_base_filename(self):
        for move in self:
            #if move.move_type != 'out_invoice':
            if move.move_type not in ['out_invoice', 'in_invoice']:
                raise UserError(_("This feature is developed for Customer invoices or Vendor bills only."))
            #if move.move_type == 'out_invoice' and not move.pay_by_line_execute:
            if move.move_type == 'out_invoice':
                if move.move_type == 'out_invoice' and not move.pay_by_line_execute:
                    raise UserError(_("This invoice has followed standard flow so it will not cover in this printout.\nCustomer Invoices which has used Customised flow will be covered in this printout."))
            if move.move_type == 'in_invoice':
                if move.move_type == 'in_invoice' and not move.pay_by_line_execute:
                    raise UserError(_("This bill has followed standard flow so it will not cover in this printout.\nVendor Bills which has used Customised flow will be covered in this printout."))
                
        return self._get_move_display_name()

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    select = fields.Boolean('Select', copy=0)
    fully_paid = fields.Boolean('Paid', copy=0)

class AccountPayment(models.Model):
    _inherit = "account.payment"

    paid_inv_line_ids = fields.Many2many('account.move.line', 'payment_inv_line_rel', 'payment_id', 'inv_line_id', string="Invoice Line", copy=False,)

    def action_draft(self):
        ''' posted -> draft '''
        if self.reconciled_invoice_ids:
            for move in self.reconciled_invoice_ids:
                #if move.move_type == 'out_invoice':
                if move.move_type != 'entry':
                    if self.paid_inv_line_ids:
                        for line in move.invoice_line_ids.filtered(lambda l:l.id in self.paid_inv_line_ids.ids):
                            line.fully_paid = False
                            line.select = False
                        self.paid_inv_line_ids = False
        if self.paid_inv_line_ids:
            self.paid_inv_line_ids = False
        res = super(AccountPayment, self).action_draft()
        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
