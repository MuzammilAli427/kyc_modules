# -*- coding: utf-8 -*-
from odoo import api, fields, models
from datetime import date


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    @api.model
    def create(self, field_list):
        res = super(AccountPayment, self).create(field_list)
        res.update({
            'waiting_state': 'draft',
        })
        return res

    waiting_state = fields.Selection(
        [('draft', 'Draft'), ('waiting_for_approval', 'Waiting for Approval'), ('done', 'Done')], default="draft",
        string='Waiting State')
    approval_hide = fields.Boolean(compute='compute_approval', string='Approval Hide', store=True)
    approved_by = fields.Many2one('res.users', string='Approved By')
    approved_date = fields.Date(string='Approved Date')

    @api.depends('journal_id')
    def compute_approval(self):
        for rec in self:
            if rec.journal_id.verification_required == True:
                rec.approval_hide = True
            else:
                rec.approval_hide = False

    def action_submit_for_approval(self):
        if self.journal_id.verification_required == True:
            self.write({'waiting_state': 'waiting_for_approval'})

    def action_approval(self):
        for rec in self:
            rec.waiting_state = 'done'
            rec.write({'approved_by': rec.env.user and rec.env.user.id or False, 'approved_date': date.today()})
            display_msg = """ """
            display_msg += 'Approved By : ' + ' ' + str(rec.env.user.name)
            display_msg += """ <br/> """
            display_msg += 'Approved Date : ' + ' ' + str(date.today())
            rec.message_post(body=display_msg)
            rec.action_post()

    def action_draft(self):
        super(AccountPayment, self).action_draft()
        for rec in self:
            rec.write({'waiting_state': 'draft'})
            pass

    def action_cancel(self):
        self.state = 'cancel'
        return super(AccountPayment, self).action_cancel()
