from odoo import api, fields, models, _
from odoo.exceptions import UserError, Warning


class SBApprovalWizard(models.TransientModel):
    _name = 'sb.approval.wizard'
    _description = "SB Approval Wizard"

    loan_id = fields.Many2one('account.loan')
    is_bod_approve = fields.Boolean(related='loan_id.is_bod_approve')
    first_action_require = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No')
    ], 'Action Require')
    action_require = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No')
    ])

    def confirm_first_action(self):
        if self.first_action_require == 'yes':
            self.loan_id.write({'is_bod_approve': True,
                                'first_bod_rejection': False,
                                'approver_ids': [(4, self.env.user.id)]})
        else:
            self.loan_id.write({'is_bod_approve': True,
                                'first_bod_rejection': True,
                                'approver_ids': [(4, self.env.user.id)]
                                })
        admin = self.env['res.users'].search([('id', '=', 2)])
        group = self.env.ref('smart_loan_system.group_loan_second_bod')
        users_in_group = self.env['res.users'].search([('groups_id', 'in', group.id)])
        for user in users_in_group:
            self.env['mail.message'].create({
                'message_type': "notification",
                'body': "The Loan" + ' ' + self.loan_id.name + ' has been sent to you for further action-',
                'subject': "Action Required",
                'partner_ids': [(4, user.partner_id.id)],
                'model': 'account.loan',
                'res_id': self.loan_id.id,
                'notification_ids': [(0, 0,
                                      {
                                          'res_partner_id': user.partner_id.id,
                                          'notification_type': 'inbox'
                                      }
                                      )],
                'author_id': self.env.user.partner_id and self.env.user.partner_id.id
            })
            template_id = self.env.ref('smart_loan_system.stage_action_required_mail_template')
            template = self.env['mail.template'].browse(template_id.id)
            if template:
                template.write({'email_to': user.email or user.partner_id.email,
                                'email_from': admin.email if admin else False})
                template.send_mail(self.loan_id.id, True)

        return {
            'name': _('LAF Stage Comment'),
            'domain': [('loan_id', '=', self.loan_id.id)],
            'res_model': 'laf.stage.comment',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_loan_id': self.loan_id.id}
        }

    def confirm_action(self):
        admin = self.env['res.users'].search([('id', '=', 2)])
        group = False
        users_in_group = False
        if self.action_require == 'yes' and self.loan_id.first_bod_rejection == False:
            group = self.env.ref('smart_loan_system.group_loan_sb')
            users_in_group = self.env['res.users'].search([('groups_id', 'in', group.id)])
            self.loan_id.write({'laf_state': 'sb_approve',
                                'approver_ids': [(4, self.env.user.id)]})
        elif self.action_require == 'yes' and self.loan_id.first_bod_rejection == True:
            raise UserError(
                _('BOD 1 Rejected this Loan to go for "SB Approval" so you also need to Reject it for "SB Approval".'))
        elif self.action_require == 'no' and self.loan_id.first_bod_rejection == False:
            raise UserError(
                _('BOD 1 Accepted this Loan to go for "SB Approval" so you also need to Accept it for "SB Approval".'))
        elif self.action_require == 'no' and self.loan_id.first_bod_rejection == True:
            group = self.env.ref('smart_loan_system.group_loan_cam')
            users_in_group = self.env['res.users'].search([('groups_id', 'in', group.id)])
            self.loan_id.write({'laf_state': 'commitment_pa_letter',
                                'bod_to_commitment': True,
                                'approver_ids': [(4, self.env.user.id)]})
        for user in users_in_group:
            self.env['mail.message'].create({
                'message_type': "notification",
                'body': "The Loan" + ' ' + self.loan_id.name + ' has been sent to you for further action-',
                'subject': "Action Required",
                'partner_ids': [(4, user.partner_id.id)],
                'model': 'account.loan',
                'res_id': self.loan_id.id,
                'notification_ids': [(0, 0,
                                      {
                                          'res_partner_id': user.partner_id.id,
                                          'notification_type': 'inbox'
                                      }
                                      )],
                'author_id': self.env.user.partner_id and self.env.user.partner_id.id
            })
            template_id = self.env.ref('smart_loan_system.stage_action_required_mail_template')
            template = self.env['mail.template'].browse(template_id.id)
            if template:
                template.write({'email_to': user.email or user.partner_id.email,
                                'email_from': admin.email if admin else False})
                template.send_mail(self.loan_id.id, True)

        return {
            'name': _('LAF Stage Comment'),
            'domain': [('loan_id', '=', self.loan_id.id)],
            'res_model': 'laf.stage.comment',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_loan_id': self.loan_id.id}
        }
