from odoo import api, fields, models, _
from odoo.exceptions import UserError, Warning


class RestructureLoanWizard(models.Model):
    _name = 'restructure.loan.wizard'
    _description = "Restructure Loan Wizard"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    loan_ids = fields.Many2many(
        'account.loan',
        required=True, store=True
    )
    parent_loan_id = fields.Many2one('account.loan', store=True)

    name = fields.Char(related='parent_loan_id.name')

    currency_id = fields.Many2one(
        'res.currency'
    )
    company_currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    date = fields.Date(required=True, default=fields.Date.today(), string="Restructuring Date")
    amount = fields.Monetary(
        currency_field='company_currency_id',
        string='Closing Amount', compute='compute_closing_amount', tracking=True)
    restructure_type = fields.Selection([('without_writeoff', 'Restructure Without Write Off'),
                                         ('with_writeoff', 'Restructure With Write Off')], string='Restructure Type',
                                        default='without_writeoff', store=True)
    write_off_amount = fields.Float(string="Principal Write-Off Amount", compute='_compute_write_off_amount')

    outstanding_principal_amount = fields.Float(string="Outstanding Principal", tracking=True,
                                                compute='_compute_balances')
    outstanding_without_writoff = fields.Float(string="Outstanding Principal After Write-Off", tracking=True,
                                               compute='_compute_outstanding_without_writeoff')
    remaining_principal_amount = fields.Monetary(string="Remaining Principal", tracking=True,
                                                 currency_field='company_currency_id')
    remaining_interest_amount = fields.Monetary(string="Remaining Interest", tracking=True,
                                                currency_field='company_currency_id')
    remaining_life_insurance_amount = fields.Monetary(string="Remaining Life Insurance",
                                                      tracking=True, currency_field='company_currency_id')
    remaining_fire_insurance_amount = fields.Monetary(string="Remaining Fire Insurance",
                                                      tracking=True, currency_field='company_currency_id')
    remaining_penalties_amount = fields.Monetary(string="Remaining Penalties", tracking=True,
                                                 currency_field='company_currency_id')
    remaining_ground_lease = fields.Monetary(string="Remaining Long Lease", tracking=True,
                                             currency_field='company_currency_id')
    balance_amount = fields.Monetary(string='Balancing Amount', compute='_compute_balance_amount',
                                     currency_field='company_currency_id')
    pay_by_customer = fields.Boolean(default=False)
    is_restructuring_fee = fields.Boolean(default=False)
    restructure_fee = fields.Float(compute='compute_restructuring_fee', store=True,
                                   tracking=True)
    tax_amount = fields.Float('OB', compute='compute_ob_tax', tracking=True, )

    state = fields.Selection([
        ('draft', 'Draft'),
        ('submit_approval', 'Submit For Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], default='draft')
    reject_reason = fields.Text()
    edit_allow = fields.Boolean(compute='_compute_edit_allow')
    new_loan_amount = fields.Monetary(string="New Loan Amount", tracking=True, compute='_compute_new_loan_amount')
    difference_amount = fields.Monetary(string="Difference Amount", tracking=True, compute='_compute_difference_amount',
                                        currency_field='company_currency_id')
    writeoff_line_ids = fields.One2many('restructure.loan.writeoff', 'restructure_id')
    selection_wizard_id = fields.Many2one('select.restructure.loan')
    is_draft = fields.Boolean(default=False)

    @api.depends('state')
    def _compute_edit_allow(self):
        for rec in self:
            if rec.state == 'draft' and self.env.user.has_group(
                    'smart_loan_system.group_loan_account_officer') and not self.env.user.has_group(
                'smart_loan_system.group_loan_cam'):
                rec.edit_allow = True
            else:
                rec.edit_allow = False

    @api.depends('loan_ids')
    def _compute_balances(self):
        for rec in self:
            outstanding_principal_amount = 0.0
            remaining_principal_amount = 0.0
            remaining_interest_amount = 0.0
            remaining_life_insurance_amount = 0.0
            remaining_fire_insurance_amount = 0.0
            remaining_penalties_amount = 0.0
            remaining_ground_lease = 0.0
            if rec.loan_ids:
                for loan in rec.loan_ids:
                    company_currency = self.env.company.currency_id
                    rate = 1.0
                    if loan.currency_id != company_currency:
                        rate_line = self.env['res.currency.rate'].search(
                            [('currency_id', '=', loan.currency_id.id)],
                            order='name desc', limit=1)
                        rate = rate_line.inverse_company_rate
                    outstanding_principal_amount = outstanding_principal_amount + (loan.outstanding_bal * rate)
                    remaining_principal_amount = remaining_principal_amount + (loan.total_unpaid_principal * rate)
                    remaining_interest_amount = remaining_interest_amount + (loan.total_unpaid_interest * rate)
                    remaining_life_insurance_amount = remaining_life_insurance_amount + (
                                loan.total_unpaid_life_insurance * rate)
                    remaining_fire_insurance_amount = remaining_fire_insurance_amount + (
                                loan.total_unpaid_fire_insurance * rate)
                    remaining_penalties_amount = remaining_penalties_amount + (loan.total_penalties * rate)
                    remaining_ground_lease = remaining_ground_lease + (loan.total_unpaid_ground_lease * rate)

            rec.remaining_principal_amount = remaining_principal_amount
            rec.outstanding_principal_amount = outstanding_principal_amount - rec.remaining_principal_amount
            rec.remaining_interest_amount = remaining_interest_amount
            rec.remaining_life_insurance_amount = remaining_life_insurance_amount
            rec.remaining_fire_insurance_amount = remaining_fire_insurance_amount
            rec.remaining_penalties_amount = remaining_penalties_amount
            rec.remaining_ground_lease = remaining_ground_lease

    @api.depends('outstanding_principal_amount', 'remaining_principal_amount', 'write_off_amount')
    def _compute_balance_amount(self):
        for rec in self:
            # if rec.outstanding_principal_amount and rec.remaining_principal_amount and rec.write_off_amount:
            rec.balance_amount = rec.outstanding_principal_amount - rec.remaining_principal_amount - rec.write_off_amount
            # else:
            #     rec.balance_amount = 0.0

    @api.depends('loan_ids', 'write_off_amount')
    def _compute_outstanding_without_writeoff(self):
        for rec in self:
            outstanding_principal_amount = 0.0
            if rec.loan_ids:
                for loan in rec.loan_ids:
                    loan_name = self.env['account.loan'].search([('name', '=', loan.name)])
                    company_currency = self.env.company.currency_id
                    rate = 1.0
                    if loan_name.currency_id != company_currency:
                        rate_line = self.env['res.currency.rate'].search(
                            [('currency_id', '=', loan_name.currency_id.id)],
                            order='name desc', limit=1)
                        rate = rate_line.inverse_company_rate
                    outstanding_principal_amount = outstanding_principal_amount + (loan_name.outstanding_bal * rate)
            if rec.restructure_type == 'with_writeoff':
                rec.outstanding_without_writoff = outstanding_principal_amount - rec.write_off_amount
            else:
                rec.outstanding_without_writoff = 0.0

    @api.depends('outstanding_principal_amount', 'remaining_principal_amount', 'remaining_interest_amount',
                 'remaining_life_insurance_amount',
                 'remaining_fire_insurance_amount', 'remaining_penalties_amount', 'restructure_type',
                 'remaining_ground_lease',
                 'write_off_amount')
    def compute_closing_amount(self):
        for rec in self:
            if rec.restructure_type == 'without_writeoff':
                rec.amount = rec.outstanding_principal_amount + rec.remaining_principal_amount + rec.remaining_interest_amount + rec.remaining_life_insurance_amount + rec.remaining_fire_insurance_amount + rec.remaining_penalties_amount + rec.remaining_ground_lease

            elif rec.restructure_type == 'with_writeoff':
                rec.amount = (
                                     rec.outstanding_principal_amount + rec.remaining_principal_amount + rec.remaining_interest_amount + rec.remaining_life_insurance_amount + rec.remaining_fire_insurance_amount + rec.remaining_penalties_amount + rec.remaining_ground_lease) - rec.write_off_amount
            else:
                rec.amount = 0.00

    @api.depends('amount', 'loan_ids', 'currency_id', 'is_restructuring_fee')
    def compute_restructuring_fee(self):
        for rec in self:
            company_currency = self.env.company.currency_id
            rate = 1.0
            if rec.currency_id != company_currency:
                rate_line = self.env['res.currency.rate'].search([('currency_id', '=', rec.currency_id.id)],
                                                                 order='name desc', limit=1)
                rate = rate_line.company_rate
            if rec.is_restructuring_fee:
                if rec.restructure_fee:
                    rec.restructure_fee = rec.restructure_fee
                elif rec.loan_ids:
                    total = 0.0
                    for loan in rec.loan_ids:
                        if loan.product_id.entry_fee:
                            total = total + (rec.amount / 100 * float(loan.product_id.entry_fee.replace('%', '')))
                    rec.restructure_fee = total
            else:
                rec.restructure_fee = 0.0

    @api.depends('restructure_fee', 'currency_id', 'is_restructuring_fee')
    def compute_ob_tax(self):
        for rec in self:
            if rec.is_restructuring_fee:
                rec.tax_amount = (rec.restructure_fee / 100 * 6)
            else:
                rec.tax_amount = 0.0

    @api.depends('writeoff_line_ids')
    def _compute_write_off_amount(self):
        for rec in self:
            if rec.writeoff_line_ids:
                total = 0.0
                for line in rec.writeoff_line_ids:
                    total = total + line.company_currency_amount
                rec.write_off_amount = total
            else:
                rec.write_off_amount = 0.0

    @api.depends('pay_by_customer', 'amount', 'restructure_fee', 'tax_amount')
    def _compute_new_loan_amount(self):
        for rec in self:
            company_currency = self.env.company.currency_id
            rate = 1.0
            if rec.currency_id != company_currency:
                rate_line = self.env['res.currency.rate'].search([('currency_id', '=', rec.currency_id.id)],
                                                                 order='name desc', limit=1)
                rate = rate_line.company_rate
            if not rec.pay_by_customer:
                rec.new_loan_amount = (rec.amount * rate) + rec.restructure_fee + rec.tax_amount
            else:
                rec.new_loan_amount = rec.amount * rate

    @api.depends('loan_ids')
    def _compute_difference_amount(self):
        for rec in self:
            if rec.loan_ids:
                total_diff = 0.0
                for loan in rec.loan_ids:
                    loan_obj = self.env['account.loan'].search([('name', '=', loan.name)])
                    company_currency = self.env.company.currency_id
                    rate = 1.0
                    if loan_obj.currency_id != company_currency:
                        rate_line = self.env['res.currency.rate'].search(
                            [('currency_id', '=', loan_obj.currency_id.id)],
                            order='name desc', limit=1)
                        rate = rate_line.inverse_company_rate
                    total_diff = total_diff + (loan_obj.total_unpaid_interest * rate) + (
                                loan_obj.total_penalties * rate)
                rec.difference_amount = total_diff
            else:
                rec.difference_amount = 0.0

    def submit_for_approval(self):
        for rec in self:
            rec.write({'state': 'submit_approval',
                       'is_draft': True})

    def process_restructuring_loan(self):
        for rec in self:
            ir_config_param_obj = self.env['ir.config_parameter'].sudo()

            loan_jou_id = ir_config_param_obj.sudo().get_param('ae_loan_manag.loan_jou_id')
            if not loan_jou_id:
                raise UserError(_("Please Configure Loan Journal from Loans -> Configurations -> Settings!"))
            loan_jou = self.env['account.journal'].browse(int(loan_jou_id))

            loan_suspense_acc_id = ir_config_param_obj.sudo().get_param('ae_loan_manag.loan_suspense_acc_id')
            if not loan_suspense_acc_id:
                raise UserError(_("Please Configure Loan Suspense Account from Loans -> Configurations -> Settings!"))
            loan_suspense_acc = self.env['account.account'].browse(int(loan_suspense_acc_id))

            difference_acc_id = ir_config_param_obj.sudo().get_param('ae_loan_manag.difference_acc_id')
            if not difference_acc_id:
                raise UserError(_("Please Configure Difference Account from Loans -> Configurations -> Settings!"))
            difference_account = self.env['account.account'].browse(int(difference_acc_id))

            prod_obj = self.env['product.product']
            penalty_prod_id = ir_config_param_obj.sudo().get_param('ae_loan_manag.penalty_prod_id')
            penalty_prod = prod_obj.browse(int(penalty_prod_id))

            rate = 1.0
            company_currency = self.env.company.currency_id
            if rec.currency_id != company_currency:
                rate_line = self.env['res.currency.rate'].search([('currency_id', '=', rec.currency_id.id)],
                                                                 order='name desc', limit=1)
                rate = rate_line.company_rate

            restructure_fees = 0.0
            tax_amount = 0.0
            loan_amount = 0.0
            if rec.loan_ids and rec.is_restructuring_fee:
                total = 0.0
                for loan in rec.loan_ids:
                    if loan.product_id.entry_fee:
                        total = total + (rec.amount / 100 * float(loan.product_id.entry_fee.replace('%', '')))
                if rec.restructure_fee:
                    restructure_fees = rec.restructure_fee
                else:
                    restructure_fees = total * rate
                tax_amount = (restructure_fees / 100 * 6)
            else:
                restructure_fees = 0.0
                tax_amount = 0.0


            if rec.pay_by_customer:
                loan_amount = rec.new_loan_amount * rate
            else:
                loan_amount = rec.new_loan_amount + tax_amount + restructure_fees * rate

            if rec.amount:
                new_loan = self.env['account.loan'].create({'partner_id': rec.parent_loan_id.partner_id.id,
                                                            'product_id': rec.parent_loan_id.product_id.id,
                                                            'currency_id': rec.currency_id.id,
                                                            'country_id': rec.parent_loan_id.country_id.id,
                                                            'loan_amount': rec.new_loan_amount,
                                                            'type': rec.parent_loan_id.type,
                                                            'rate': rec.parent_loan_id.rate,
                                                            'start_date': rec.parent_loan_id.start_date,
                                                            'first_payment_due': rec.parent_loan_id.first_payment_due,
                                                            'monthly_payment': rec.parent_loan_id.monthly_payment,
                                                            'is_restructure_loan': True,
                                                            'is_leasing': False,
                                                            'is_collaterals': rec.parent_loan_id.is_collaterals,
                                                            'is_penalty': rec.parent_loan_id.is_penalty,
                                                            'old_loan_name': ', '.join(
                                                                [loan.name for loan in rec.loan_ids]),
                                                            'user_id': rec.parent_loan_id.user_id.id,
                                                            'loan_type': rec.parent_loan_id.loan_type,
                                                            'down_payment': rec.parent_loan_id.down_payment,
                                                            'method_period': rec.parent_loan_id.method_period,
                                                            'insurance_product_id': rec.parent_loan_id.insurance_product_id.id,
                                                            'insurance_sale_price': rec.parent_loan_id.insurance_sale_price,
                                                            'tax_product_id': rec.parent_loan_id.tax_product_id.id,
                                                            'tax_sale_price': rec.parent_loan_id.tax_sale_price,
                                                            'bonaire_principal_prod_id': rec.parent_loan_id.bonaire_principal_prod_id.id,
                                                            'bonaire_interest_prod_id': rec.parent_loan_id.bonaire_interest_prod_id.id,
                                                            'bonaire_principal_amount': rec.parent_loan_id.bonaire_principal_amount,
                                                            'bonaire_interest_amount': rec.parent_loan_id.bonaire_interest_amount,
                                                            'restructure_type': rec.restructure_type,
                                                            'restructure_closing_amount': round(
                                                                rec.new_loan_amount - tax_amount - restructure_fees, 2),
                                                            'restructure_fee': round(restructure_fees, 2),
                                                            'restructure_tax_amount': round(tax_amount, 2),
                                                            'restructuring_write_off_amount': rec.write_off_amount,
                                                            'pay_by_customer': rec.pay_by_customer,
                                                            'penalty_product_id': penalty_prod.id
                                                            })

                new_loan.write({'restructure_id': rec.id})

                write_off_lines = []
                for line in rec.writeoff_line_ids:
                    write_off_lines.append((0, 0,
                                            {
                                                'loan_id': line.loan_id.id,
                                                'write_off_amount': line.write_off_amount,
                                                'company_currency_amount': line.company_currency_amount,
                                            }))

                history_lines = []
                history_lines.append((0, 0,
                                      {
                                          'loan_id': rec.parent_loan_id.id,
                                          'name': rec.parent_loan_id.name,
                                          'currency_id': rec.currency_id.id,
                                          'date': rec.date,
                                          'amount': rec.amount,
                                          'restructure_type': rec.restructure_type,
                                          'balance_amount': rec.balance_amount,
                                          'write_off_amount': rec.write_off_amount,
                                          'outstanding_without_writoff': rec.outstanding_without_writoff,
                                          'outstanding_principal_amount': rec.outstanding_principal_amount,
                                          'remaining_principal_amount': rec.remaining_principal_amount,
                                          'remaining_interest_amount': rec.remaining_interest_amount,
                                          'remaining_life_insurance_amount': rec.remaining_life_insurance_amount,
                                          'remaining_fire_insurance_amount': rec.remaining_fire_insurance_amount,
                                          'remaining_penalties_amount': rec.remaining_penalties_amount,
                                          'remaining_ground_lease': rec.remaining_ground_lease,
                                          'new_loan_amount': rec.new_loan_amount,
                                          'difference_amount': rec.difference_amount,
                                          'new_loan_currency_id': rec.currency_id.id,
                                          'selection_wizard_id': rec.selection_wizard_id.id,
                                          'pay_by_customer': rec.pay_by_customer,
                                          'restructure_fee': round(restructure_fees, 2),
                                          'tax_amount': round(tax_amount, 2),
                                          'state': rec.state,
                                          'restructured_id': rec.id,
                                          'write_off_line_ids': write_off_lines
                                      }))

                rec.parent_loan_id.write({'restructured_loan_id': new_loan.id,
                                          'restructuring_ids': history_lines})

                # Difference Entry Total of All Unpaid Old Loan
                total_unpaid = 0.0
                if rec.difference_amount:
                    total_unpaid = rec.difference_amount
                else:
                    total_unpaid = 0.0
                if total_unpaid > 0.0 and new_loan:
                    difference_move = self.env['account.move'].create({
                        'journal_id': loan_jou and loan_jou.id or False,
                        'loan_id': new_loan.id or False,
                        'ref': 'Difference Balancing Entry' + ' ' + rec.name,
                        'date': fields.Date.today(),
                        'move_type': 'entry',
                        'currency_id': self.env.company.currency_id.id,
                        'partner_id': new_loan.partner_id.id or False,
                        'is_restructuring_inv': True

                    })
                    lines = [{
                        'account_id': difference_account.id,
                        'partner_id': new_loan.partner_id.id or False,
                        'debit': 0,
                        'credit': total_unpaid,
                        'amount_currency': -1 * total_unpaid,
                        'name': new_loan.name,
                        'date': fields.Date.today(),
                        'ref': 'Difference Credit Entry',
                        'currency_id': self.env.company.currency_id.id,
                    }, {
                        'account_id': loan_suspense_acc.id or False,
                        'partner_id': new_loan.partner_id.id or False,
                        'debit': total_unpaid,
                        'credit': 0,
                        'amount_currency': total_unpaid,
                        'name': new_loan.name,
                        'date': fields.Date.today(),
                        'ref': 'Difference Debit Entry',
                        'currency_id': self.env.company.currency_id.id,
                    }]
                    difference_move.line_ids = [(0, 0, val) for val in lines]
                    new_loan.write({'difference_entry_id': difference_move.id})


                rec.write({'state': 'approved'})

                return {
                    'name': _('Customer Loan'),
                    'res_model': 'account.loan',
                    'res_id': new_loan.id,
                    'type': 'ir.actions.act_window',
                    'view_mode': 'form',
                    'view_id': False,
                    'target': 'current'
                }

    def cancel_restructure_loan(self):
        for rec in self:
            if not rec.is_draft:
                rec.selection_wizard_id.parent_loan_id.is_select = False
                return {
                    'name': _('Select Loans To Restructure'),
                    'res_model': 'select.restructure.loan',
                    'res_id': rec.selection_wizard_id.id,
                    'type': 'ir.actions.act_window',
                    'view_mode': 'form',
                    'view_id': False,
                    'target': 'new',
                }
            else:
                rec.write({'amount': False,
                           'restructure_type': False,
                           'write_off_amount': False,
                           'restructure_fee': False,
                           'tax_amount': False,
                           'state': 'draft'})
                rec.parent_loan_id.write({'is_select': False,
                                          'selected_loan_ids': False})


class RestructureLoanWriteoff(models.Model):
    _name = 'restructure.loan.writeoff'
    _description = "Restructure Loan Writeoff"

    restructure_id = fields.Many2one('restructure.loan.wizard')
    loan_id = fields.Many2one('account.loan')
    currency_id = fields.Many2one('res.currency', related='loan_id.currency_id')
    company_currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    write_off_amount = fields.Float()
    company_currency_amount = fields.Monetary(compute='_compute_writeoff_in_company_currency', store=True,
                                              currency_field='company_currency_id')

    @api.depends('currency_id', 'write_off_amount', 'company_currency_id')
    def _compute_writeoff_in_company_currency(self):
        for rec in self:
            rate = 1.0
            if rec.currency_id != rec.company_currency_id:
                rate_line = self.env['res.currency.rate'].search([('currency_id', '=', rec.currency_id.id)],
                                                                 order='name desc', limit=1)
                rate = rate_line.inverse_company_rate
            rec.company_currency_amount = rec.write_off_amount * rate
