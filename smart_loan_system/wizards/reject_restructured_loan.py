from odoo import api, fields, models, _


class RejectRestructuredLoan(models.TransientModel):
    _name = 'reject.restructured.loan'
    _description = "Reject Restructured Loan"

    loan_id = fields.Many2one('account.loan')
    reason = fields.Text()

    def reject_restructured_loan(self):
        for rec in self:
            if rec.loan_id.old_loan_name:
                old_loan = rec.loan_id.restructure_id.parent_loan_id
                old_loan.write({'is_restructure_cancelled': True})
                if old_loan:
                    restructure_record = rec.loan_id.restructure_id
                    if restructure_record.selection_wizard_id.line_ids:
                        restructure_record.selection_wizard_id.line_ids.unlink()
                        self.env['loan.restructuring.lines'].search([('restructured_id', 'in', restructure_record.ids)])
                    restructured_history_lines = self.env['loan.restructuring.lines'].search([('restructured_id', 'in', restructure_record.ids)])
                    for line in restructured_history_lines:
                        line.write({'state': 'rejected',
                                    'reject_reason': rec.reason})
                    for rest in restructure_record:
                        rest.write({'state': 'rejected',
                                    'reject_reason': rec.reason})
            rec.loan_id.write({'state': 'rejected'})
