# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from datetime import date


class PaymentAmountWizard(models.TransientModel):
    _name = "payment.amount.wizard"
    _description = "Payment Amount Wizard"

    # partner_ids = fields.Many2many('res.partner', string="Partners")
    date_from = fields.Date()
    date_to = fields.Date()

    def _build_comparison_context(self, data):
        result = {'date_from': data['form']['date_from'] or False,
                  'date_to': data['form']['date_to'] or False}
        return result

    def check_report(self):
        data = {'form': self.read(['date_from', 'date_to'])[0]}
        comparison_context = self._build_comparison_context(data)
        data['form']['comparison_context'] = comparison_context
        return self.env.ref('bit_financial_chart.action_report_payment_amount').report_action(self, data=data)
