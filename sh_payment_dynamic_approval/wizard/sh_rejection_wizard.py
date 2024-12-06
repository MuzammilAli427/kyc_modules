# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies.
from odoo import api, fields, tools, models, _
from datetime import datetime


class RejectionReasonWizard(models.TransientModel):
    _inherit = 'sh.reject.reason.wizard'
    _description = "Reject Reason Wizard"

    def action_reject_order(self):

        active_obj = self.env[self.env.context.get('active_model')].browse(
            self.env.context.get('active_id'))
        if self.env.context.get('active_model') == 'account.payment':
            active_obj.write({
                'state': 'reject',
                'reject_reason': self.name,
                'reject_by': active_obj.env.user,
                'rejection_date': datetime.now(),
            })
            if active_obj.payment_inv_line:
                for inv_line in active_obj.payment_inv_line:
                    inv_line.move_line_id.write({'unpaid_amount': inv_line.move_line_id.unpaid_amount + inv_line.paid_amount,
                                                 'paid_amount':  inv_line.move_line_id.paid_amount - inv_line.paid_amount,
                                                 'fully_paid': False})
            if active_obj.payment_inv_line:
                active_obj.payment_inv_line.unlink()

            payment_reject_template_id = active_obj.env.ref(
                "sh_payment_dynamic_approval.email_template_reject_payment")
            if active_obj.user_id and payment_reject_template_id:
                payment_reject_template_id.sudo().send_mail(active_obj.id, force_send=True, email_values={
                    'email_from': active_obj.env.user.email, 'email_to': active_obj.user_id.email})
                active_obj.env['bus.bus']._sendone(active_obj.user_id.partner_id, 'sh_notification_info',
                                                   {'title': _('Notitification'),
                                                    'message': 'Dear User!! Your payment has been rejected'
                                                    })

        return super(RejectionReasonWizard, self).action_reject_order()
