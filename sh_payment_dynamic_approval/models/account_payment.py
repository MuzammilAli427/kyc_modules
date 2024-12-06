# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies.
from odoo import fields, models, api, _
from datetime import datetime


class AccountPayment(models.Model):
    _inherit = 'account.payment'
    sh_to_reconcile = fields.Many2many('account.move.line',string="Line to reconcile")
    approval_config_id = fields.Many2one(
        'sh.payment.approval.config', string="Payment Approval Level", compute="_compute_approval_level")
    user_ids = fields.Many2many('res.users', string="Users")
    level = fields.Integer(string="Next Approval Level")
    group_ids = fields.Many2many('res.groups', string="Groups")
    approval_info_line = fields.One2many(
        'sh.approval.info', 'sh_payment_id')
    rejection_date = fields.Datetime(string="Reject Date")
    reject_by = fields.Many2one(
        'res.users', string="Reject By")
    reject_reason = fields.Char(string="Reject Reason")
    is_approval_user = fields.Boolean(
        'Is Approval User', search="_search_is_approval_user", compute="_compute_is_approval_user")

    def action_post(self):
        for rec in self:
            payment_approval_template_id = self.env.ref("sh_payment_dynamic_approval.email_template_for_approve_payment")
            if rec.approval_config_id and rec.approval_config_id.payment_approval_line:
                rec.state = 'waiting'
                rec.approval_info_line = False
                lines = rec.approval_config_id.payment_approval_line
                for line in lines:
                    dictt = []
                    dictt.append((0, 0, {
                        'level': line.level,
                        'user_ids': [(6, 0, line.user_ids.ids)],
                        'group_ids': [(6, 0, line.group_ids.ids)],
                    }))
                    rec.update({
                        'approval_info_line': dictt
                    })
                users = lines[0].user_ids
                rec.level = lines[0].level
                if lines[0].approve_by == 'group':
                    rec.group_ids = lines[0].group_ids
                    rec.user_ids = False
                    users = rec.group_ids.users
                elif lines[0].approve_by == 'user':
                    rec.group_ids = False
                    rec.user_ids = lines[0].user_ids
                    users = lines[0].user_ids

                for user in users:
                    payment_approval_template_id.sudo().send_mail(rec.id, force_send=True, email_values={
                                'email_from': self.env.user.email, 'email_to': user.email})
                    self.env['bus.bus']._sendone(user.partner_id, 'sh_notification_info',
                                                {'title': _('Notitification'),
                                                'message': 'You have approval notification for payment'
                                                })
            else:
                super(AccountPayment, rec).action_post()

    def action_approve(self):
        # self.state = 'draft'
        payment_approval_template_id = self.env.ref("sh_payment_dynamic_approval.email_template_for_approve_payment")
        payment_posted_template_id = self.env.ref("sh_payment_dynamic_approval.email_template_posted_payment")
        info_line = self.approval_info_line.filtered(
            lambda x: x.level == self.level)
        if info_line:
            info_line.status = True
            info_line.approval_date = datetime.now()
            info_line.approved_by = self.env.user

        curr_line_id = self.env['sh.payment.approval.config.line'].search(
            [('payment_approval_config_id', '=', self.approval_config_id.id), ('level', '=', self.level)])
        nxt_line_id = self.env['sh.payment.approval.config.line'].search(
            [('payment_approval_config_id', '=', self.approval_config_id.id), ('id', '>', curr_line_id.id)], limit=1)

        if nxt_line_id:
            self.level = nxt_line_id.level
            if nxt_line_id.approve_by == 'group':
                self.group_ids = nxt_line_id.group_ids
                self.user_ids = False
                users = self.group_ids.users
            elif nxt_line_id.approve_by == 'user':
                self.group_ids = False
                self.user_ids = nxt_line_id.user_ids
                users = nxt_line_id.user_ids

            for user in users:
                payment_approval_template_id.sudo().send_mail(self.id, force_send=True, email_values={
                            'email_from': self.env.user.email, 'email_to': user.email})
                self.env['bus.bus']._sendone(user.partner_id, 'sh_notification_info',
                                             {'title': _('Notitification'),
                                                 'message': 'You have approval notification for payment'
                                              })
        else:
            if self.user_id:
                payment_posted_template_id.sudo().send_mail(self.id, force_send=True, email_values={
                    'email_from': self.env.user.email, 'email_to': self.user_id.email})
                self.env['bus.bus']._sendone(self.user_id.partner_id, 'sh_notification_info',
                                             {'title': _('Notitification'),
                                              'message': 'Dear User!! Your payment request has been approved'
                                              })
            self.write({'level': 0,
                        'group_ids': False,
                        'user_ids': False})
            super(AccountPayment, self).action_post()
            if self.sh_to_reconcile:
                domain = [
                ('parent_state', '=', 'posted'),
                ('account_type', 'in', ('asset_receivable', 'liability_payable')),
                ('reconciled', '=', False),
                ]
                payment_lines = self.line_ids.filtered_domain(domain)
                for account in payment_lines.account_id:
                    (payment_lines + self.sh_to_reconcile)\
                        .filtered_domain([('account_id', '=', account.id), ('reconciled', '=', False)])\
                        .reconcile()

    @api.depends('amount')
    def _compute_approval_level(self):
        for rec in self:
            rec.approval_config_id = False
            rec.approval_config_id = rec.env['sh.payment.approval.config'].search(domain=[(
                'min_amount', '<', rec.amount), ('company_ids.id', 'in', [rec.env.company.id])], order='min_amount desc', limit=1)

    def _compute_is_approval_user(self):
        self.is_approval_user = False
        for rec in self:
            if self.env.user in self.user_ids or any(item in self.env.user.groups_id.ids for item in rec.group_ids.ids):
                rec.is_approval_user = True

    def _search_is_approval_user(self, operator, value):
        results = []
        if value:
            payment_ids = self.env['account.payment'].search([])
            if payment_ids:
                for payment_id in payment_ids:
                    if self.env.user.id in payment_id.user_ids.ids or any(item in self.env.user.groups_id.ids for item in payment_id.group_ids.ids):
                        results.append(payment_id.id)
        return [('id', 'in', results)]
