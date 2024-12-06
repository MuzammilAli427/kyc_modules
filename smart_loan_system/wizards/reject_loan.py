from odoo import api, fields, models, _
import pytz  # Importing pytz to handle time zones
from datetime import datetime  # Importing datetime to get the current time

class RejectLoan(models.TransientModel):
    _name = 'reject.loan'
    _description = "Reject Loan"

    loan_id = fields.Many2one('account.loan')
    reason = fields.Text()

    def reject_loan(self):
        for rec in self.loan_id:
            group = False
            users_in_group = False
            admin = rec.env['res.users'].search([('id', '=', 2)])
            
            # Define time zone for Curacao
            curacao_tz = pytz.timezone('America/Curacao')
            curacao_time = datetime.now(tz=curacao_tz)  # Get the current time in Curacao
            
            # Format the date and time to display date, hours, minutes, and seconds
            formatted_datetime = curacao_time.strftime('%Y-%m-%d %H:%M:%S')
            
            if rec.laf_state == 'cam_approve':
                group = self.env.ref('smart_loan_system.group_loan_cao')
                users_in_group = self.env['res.users'].search([('groups_id', 'in', group.id)])
            elif rec.laf_state == 'review_edit':
                group = self.env.ref('smart_loan_system.group_loan_cam')
                users_in_group = self.env['res.users'].search([('groups_id', 'in', group.id)])
            elif rec.laf_state == 'commitment_pa_letter' and rec.bod_to_commitment == False:
                group3 = self.env.ref('smart_loan_system.group_loan_sb')
                group = self.env.ref('smart_loan_system.group_loan_bod')
                group2 = self.env.ref('smart_loan_system.group_loan_second_bod')
                users_in_group = self.env['res.users'].search([('groups_id', 'in', [group.id, group2.id, group3.id])])
            elif rec.laf_state == 'commitment_pa_letter' and rec.bod_to_commitment == True:
                group = self.env.ref('smart_loan_system.group_loan_bod')
                group2 = self.env.ref('smart_loan_system.group_loan_second_bod')
                users_in_group = self.env['res.users'].search([('groups_id', 'in', [group.id, group2.id])])
            elif rec.laf_state == 'sb_approve':
                group = self.env.ref('smart_loan_system.group_loan_bod')
                group2 = self.env.ref('smart_loan_system.group_loan_second_bod')
                users_in_group = self.env['res.users'].search([('groups_id', 'in', [group.id, group2.id])])
            elif rec.laf_state == 'bod' and rec.is_bod_approve:
                group = self.env.ref('smart_loan_system.group_loan_bod')
                users_in_group = self.env['res.users'].search([('groups_id', 'in', group.id)])
            elif rec.laf_state == 'bod' and not rec.is_bod_approve and rec.kyc_type == 'retail':
                group = self.env.ref('smart_loan_system.group_loan_corp_manager')
                users_in_group = self.env['res.users'].search([('groups_id', 'in', group.id)])
            elif rec.laf_state == 'bod' and not rec.is_bod_approve and rec.kyc_type != 'retail':
                group = self.env.ref('smart_loan_system.group_loan_retail_manager')
                users_in_group = self.env['res.users'].search([('groups_id', 'in', group.id)])
            elif rec.laf_state == 'cross_manager' and rec.kyc_type != 'retail':
                group = self.env.ref('smart_loan_system.group_loan_corp_manager')
                users_in_group = self.env['res.users'].search([('groups_id', 'in', group.id)])
            elif rec.laf_state == 'cross_manager' and rec.kyc_type == 'retail':
                group = self.env.ref('smart_loan_system.group_loan_retail_manager')
                users_in_group = self.env['res.users'].search([('groups_id', 'in', group.id)])
            elif rec.laf_state == 'retail_manager' and rec.account_officer_approver:
                users_in_group = self.env['res.users'].search([('id', '=', rec.account_officer_approver.id)])
            
            for user in users_in_group:
                self.env['mail.message'].create({
                    'message_type': "notification",
                    'body': "The Loan" + ' ' + rec.name + ' is rejected and has been sent to you for further action-',
                    'subject': "Stage Rejected Action Required",
                    'partner_ids': [(4, user.partner_id.id)],
                    'model': 'account.loan',
                    'res_id': rec.id,
                    'notification_ids': [(0, 0,
                                          {
                                              'res_partner_id': user.partner_id.id,
                                              'notification_type': 'inbox'
                                          }
                                          )],
                    'author_id': rec.env.user.partner_id and rec.env.user.partner_id.id
                })
                template_id = self.env.ref('smart_loan_system.stage_rejection_action_mail_template')
                template = self.env['mail.template'].browse(template_id.id)
                if template:
                    template.write({'email_to': user.email or user.partner_id.email,
                                    'email_from': admin.email if admin else False})
                    template.send_mail(rec.id, True)

            rec.sudo().write({'comment': rec.comment + '\n' + formatted_datetime + ' @ ' + self.env.user.name + ' Rejected the LAf: ' + self.reason if rec.comment else formatted_datetime + ' @ ' + self.env.user.name + ' Rejected the LAf: ' + self.reason,
                              'laf_state': 'review_edit' if rec.laf_state == 'cam_approve' else (
                                  'commitment_pa_letter' if rec.laf_state == 'review_edit' else (
                                          'bod' if rec.laf_state == 'commitment_pa_letter' else (
                                              'bod' if rec.laf_state == 'sb_approve' else (
                                                  'cross_manager' if rec.laf_state == 'bod' and rec.is_bod_approve == False else (
                                                      'bod' if rec.laf_state == 'bod' and rec.is_bod_approve == True else (
                                                          'retail_manager' if rec.laf_state == 'cross_manager' else (
                                                              'pre_draft' if rec.laf_state == 'retail_manager' else False))))))),
                              'is_compute_items': False if rec.laf_state == 'retail_manager' and rec.env.user.has_group(
                                  'smart_loan_system.group_loan_account_officer') else (
                                  False if rec.laf_state in ('review_edit', 'cam_approve') and rec.env.user.has_group(
                                      'smart_loan_system.group_loan_cao') else True),
                              'is_bod_approve': False if rec.laf_state in (
                                  'sb_approve', 'bod', 'cross_manager', 'retail_manager', 'pre_draft') else (
                                  False if rec.laf_state == 'commitment_pa_letter'  else (
                                          True if rec.laf_state in ('review_edit', 'cam_approve') else False)),
                              'bod_to_commitment': False,
                              'is_laf_posted': False
                              })
