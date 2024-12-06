# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies.
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class PaymentApprovalConfig(models.Model):
    _name = 'sh.payment.approval.config'
    _description = 'Payment Approval Configuration'

    name = fields.Char(string="Name")
    min_amount = fields.Float(string="Minimum Amount", required=True)
    company_ids = fields.Many2many(
        'res.company', string="Allowed Companies", default=lambda self: self.env.company)
    payment_approval_line = fields.One2many('sh.payment.approval.config.line', 'payment_approval_config_id',string='Payment approval line')

    @api.constrains('payment_approval_line')
    def approval_line_level(self):
        if self.payment_approval_line:
            levels = self.payment_approval_line.mapped('level')
            if len(levels) != len(set(levels)):
                raise ValidationError('Levels must be different!!!')
