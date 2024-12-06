from odoo import api, fields, models, _


class SelectRestructureLoan(models.Model):
    _name = 'select.restructure.loan'
    _description = "Select Restructure Loan"

    parent_loan_id = fields.Many2one('account.loan')
    name = fields.Char(related='parent_loan_id.name')
    partner_id = fields.Many2one('res.partner', string='Customer', related='parent_loan_id.partner_id')
    line_ids = fields.One2many('select.restructure.loan.lines', 'select_restructure_loan_id')

    def select_loans(self):
        for rec in self:
            if rec.line_ids:
                loan_list = []
                for line in rec.line_ids:
                    loan_list.append(line.loan_id.id)

                restructure_loan = self.env['restructure.loan.wizard']
                existing_restructure_loan = restructure_loan.search(
                    [('loan_ids', 'in', loan_list), ('state', '!=', 'rejected')],
                    limit=1)
                if existing_restructure_loan:
                    restructure_loan = existing_restructure_loan
                    existing_restructure_loan.write({'loan_ids': loan_list,
                                                     'parent_loan_id': rec.parent_loan_id.id,
                                                      'date': fields.Date.today(),
                                                      'currency_id': rec.parent_loan_id.currency_id.id,
                                                      'selection_wizard_id': rec.id})
                else:
                    restructure_loan = restructure_loan.create({'loan_ids': loan_list,
                                                                'parent_loan_id': rec.parent_loan_id.id,
                                                                'date': fields.Date.today(),
                                                                'currency_id': rec.parent_loan_id.currency_id.id,
                                                                'selection_wizard_id': rec.id})
                restructure_loan.writeoff_line_ids = [(5, 0, 0)]
                for line in rec.line_ids:
                    restructure_loan.writeoff_line_ids = [
                        (0, 0, {'loan_id': line.loan_id.id, "restructure_id": restructure_loan.id})]
                rec.parent_loan_id.write({'is_select': True,
                                          'selected_loan_ids': loan_list,
                                          'is_restructure_cancelled': False})

                return {
                    'name': _('Restructure Loan'),
                    'res_model': 'restructure.loan.wizard',
                    'res_id': restructure_loan.id,
                    'type': 'ir.actions.act_window',
                    'view_mode': 'form',
                    'view_id': False,
                    'target': 'new',
                }
            print(self.id)


class SelectRestructureLoanLines(models.Model):
    _name = 'select.restructure.loan.lines'
    _description = "Select Restructure Loan Lines"

    select_restructure_loan_id = fields.Many2one('select.restructure.loan')
    is_select = fields.Boolean(default=False, string='Select')
    loan_id = fields.Many2one('account.loan', string='Loan')
    old_loan_name = fields.Char('Old Loan Name', related='loan_id.old_loan_name')
    type = fields.Selection(related='loan_id.type')
    product_id = fields.Many2one('loan.products', string='Loan Product', related='loan_id.product_id')
    currency_id = fields.Many2one(
        'res.currency',
        related='loan_id.currency_id',
        readonly=True
    )
    country_id = fields.Many2one('res.country', 'Country', related='loan_id.country_id')
    partner_id = fields.Many2one('res.partner', string='Customer', related='loan_id.partner_id')
    outstanding_principal_amount = fields.Float(string="Outstanding Principal", related='loan_id.outstanding_bal')
    remaining_principal_amount = fields.Monetary(string="Remaining Principal", related='loan_id.total_unpaid_principal')
    remaining_interest_amount = fields.Monetary(string="Remaining Interest", related='loan_id.total_unpaid_interest')
    remaining_life_insurance_amount = fields.Monetary(string="Remaining Life Insurance",
                                                      related='loan_id.total_unpaid_life_insurance')
    remaining_fire_insurance_amount = fields.Monetary(string="Remaining Fire Insurance",
                                                      related='loan_id.total_unpaid_fire_insurance')
    remaining_penalties_amount = fields.Monetary(string="Remaining Penalties", related='loan_id.total_penalties')
    remaining_ground_lease = fields.Monetary(string="Remaining Ground Lease",
                                             related='loan_id.total_unpaid_ground_lease')
