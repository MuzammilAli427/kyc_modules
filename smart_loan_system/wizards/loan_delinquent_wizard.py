from odoo import models, fields, api, _
import base64
from odoo.exceptions import UserError, Warning


class LoanDelinquentWizard(models.TransientModel):
    _name = 'loan.delinquent.wizard'
    _description = "Loan Delinquent Wizard"

    def _default_interest_prod(self):
        config_obj = self.env['ir.config_parameter']
        interest_prod_id = config_obj.sudo().get_param('ae_loan_manag.interest_prod_id')
        interest_prod = self.env['product.product'].search([('id', '=', interest_prod_id)])
        return interest_prod

    loan_ids = fields.Many2many('account.loan')
    from_date = fields.Date('From')
    to_date = fields.Date('To')
    currency_id = fields.Many2one('res.currency')
    template = fields.Selection([('temp_1', 'Loan Interest Letter'),
                                 ('temp_2', 'Mortgage Interest Letter')], string='Report')
    interest_prod_id = fields.Many2one('product.product', default=_default_interest_prod)
    interest_amount = fields.Float()
    principal_amount = fields.Float()
    send_button_visibility = fields.Boolean(compute='_compute_send_button_visibility')

    @api.depends('loan_ids')
    def _compute_send_button_visibility(self):
        for rec in self:
            if rec.loan_ids and len(rec.loan_ids) == 1:
                rec.send_button_visibility = False
            else:
                rec.send_button_visibility = True

    def print_pdf(self):
        for rec in self:
            report = rec.env.ref('smart_loan_system.report_loan_interest_action').report_action(rec)
            return report

    def make_attachment_report(self, report_id):
        for rec in self:
            report_template = rec.env.ref('smart_loan_system.report_loan_interest_action')
            filename = "Interest Letter Report" + '.pdf'
            ir_actions_report_sudo = self.env['ir.actions.report'].sudo()
            report_template_id = ir_actions_report_sudo._render_qweb_pdf(report_template, res_ids=report_id)
            data_record = base64.b64encode(report_template_id[0])
            ir_values = {
                'name': filename,
                'type': 'binary',
                'datas': data_record,
                'store_fname': 'data_record',
                'mimetype': 'application/x-pdf',
            }
            data_id = self.env['ir.attachment'].create(ir_values)
            return data_id

    def send_print_pdf(self):
        for rec in self:
            config_obj = self.env['ir.config_parameter']
            delinquent_days = config_obj.sudo().get_param('ae_loan_manag.max_delinquent_period')
            if len(rec.loan_ids) == 1 and int(rec.loan_ids[0].days_past_due) <= int(delinquent_days):
                if rec.loan_ids[0].partner_id.email:
                    interest_prod_id = config_obj.sudo().get_param('ae_loan_manag.interest_prod_id')
                    interest_lines = self.env['account.move.line'].search(
                        [('move_id.loan_id', '=', rec.loan_ids[0].id), ('move_id.state', '=', 'posted'),
                         ('move_id.move_type', '=', 'out_invoice'), ('move_id.date', '>=', rec.from_date),
                         ('move_id.date', '<=', rec.to_date), ('product_id', '=', int(interest_prod_id))])
                    if interest_lines:
                        rec.interest_amount = sum(interest_lines.mapped('paid_amount'))
                    else:
                        rec.interest_amount = 0.0
                    report = self.make_attachment_report(rec.ids)
                    template_id = self.env.ref('smart_loan_system.email_template_interest_letter')
                    template = self.env['mail.template'].browse(template_id.id)
                    if template:
                        template.attachment_ids = [(6, 0, [report.id])]
                        subj = 'Interest Letter Report'
                        template.write(
                            {'email_to': rec.loan_ids[0].partner_id.email, 'email_from': self.env.user.email,
                             'subject': subj})
                        template.send_mail(rec.id, True)
                    report = rec.env.ref('smart_loan_system.report_loan_interest_action').report_action(rec)
                    return report
                else:
                    raise UserError(_("Please add email address on the partner"))
