# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies.
from odoo import fields, models


class PaymentApprovalConfigLine(models.Model):
    _name = 'sh.payment.approval.config.line'
    _description = 'Dynamic Payment Approaval Configuration Line'

    level = fields.Integer(string="Level", required=True)
    approve_by = fields.Selection(
        [('group', 'Group'), ('user', 'User')], string="Approve Process By", default="user", required=True,)
    user_ids = fields.Many2many('res.users', string="Users")
    group_ids = fields.Many2many('res.groups', string="Groups")
    payment_approval_config_id = fields.Many2one('sh.payment.approval.config')
