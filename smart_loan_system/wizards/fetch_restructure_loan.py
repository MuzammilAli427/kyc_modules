from odoo import api, fields, models, _
from odoo.exceptions import UserError, Warning

class FetchRestructureLoan(models.Model):
    _name = 'fetch.restructure.loan'
    _description = "Fetch Restructure Loan"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    loan_id = fields.Many2one(
        'account.loan',
        required=True,
    )
    parent_loan_id = fields.Many2one('account.loan')
    name = fields.Char(related='loan_id.name')

    currency_id = fields.Many2one(
        'res.currency')
    company_currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    date = fields.Date(required=True, default=fields.Date.today(), string="Date")
    amount = fields.Monetary(
        currency_field='company_currency_id',
        string='Closing Amount', tracking=True, compute='compute_closing_amount')
    restructure_type = fields.Selection([('without_writeoff', 'Restructure Without Write Off'),
                                         ('with_writeoff', 'Restructure With Write Off')], string='Restructure Type',
                                        default='without_writeoff')
    write_off_amount = fields.Float(string="Principal Write-Off Amount", tracking=True,
                                    compute='_compute_write_off_amount')
    outstanding_principal_amount = fields.Float(string="Outstanding Principal", tracking=True)
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
    remaining_ground_lease = fields.Monetary(string="Remaining Ground Lease", tracking=True,
                                             currency_field='company_currency_id')
    balance_amount = fields.Monetary(string='Balancing Amount', currency_field='company_currency_id',
                                     compute='_compute_balance_amount')
    pay_by_customer = fields.Boolean(default=False)
    is_restructuring_fee = fields.Boolean(default=False)
    restructure_fee = fields.Float(compute='compute_restructuring_fee', store=True,
                                   tracking=True)
    tax_amount = fields.Float('OB', compute='compute_ob_tax', tracking=True, store=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submit_approval', 'Submit For Approval'),
        ('approved', 'Approved'),
    ], default='draft')
    reject_reason = fields.Text()
    edit_allow = fields.Boolean(compute='_compute_edit_allow')
    new_loan_amount = fields.Monetary(string="New Loan Amount", tracking=True, compute='_compute_new_loan_amount')
    difference_amount = fields.Monetary(string="Difference Amount", tracking=True, currency_field='company_currency_id')
    writeoff_line_ids = fields.One2many('fetch.restructure.writeoff', 'fetch_restructure_id')
    selection_wizard_id = fields.Many2one('select.restructure.loan')

    @api.depends('state')
    def _compute_edit_allow(self):
        for rec in self:
            if rec.state == 'draft' and self.env.user.has_group(
                    'smart_loan_system.group_loan_cao') and not self.env.user.has_group(
                'smart_loan_system.group_loan_cam'):
                rec.edit_allow = True
            else:
                rec.edit_allow = False

    @api.depends('outstanding_principal_amount', 'remaining_principal_amount', 'write_off_amount')
    def _compute_balance_amount(self):
        for rec in self:
            rec.balance_amount = rec.outstanding_principal_amount - rec.remaining_principal_amount - rec.write_off_amount

    @api.depends('outstanding_principal_amount', 'write_off_amount')
    def _compute_outstanding_without_writeoff(self):
        for rec in self:
            if rec.restructure_type == 'with_writeoff':
                rec.outstanding_without_writoff = rec.outstanding_principal_amount - rec.write_off_amount
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

    @api.depends('amount', 'parent_loan_id', 'currency_id', 'is_restructuring_fee')
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
                elif rec.parent_loan_id:
                    total = 0.0
                    if rec.parent_loan_id.product_id.entry_fee:
                        total = total + (rec.amount / 100 * float(rec.parent_loan_id.product_id.entry_fee.replace('%', '')))
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

            if not rec.pay_by_customer:
                rec.new_loan_amount = rec.amount + rec.restructure_fee + rec.tax_amount
            else:
                rec.new_loan_amount = rec.amount

    def submit_for_approval(self):
        for rec in self:
            rec.write({'state': 'submit_approval'})

    def process_fetching_restructuring_loan(self):
        for rec in self:
            rec.write({'state': 'approved'})
            ir_config_param_obj = self.env['ir.config_parameter'].sudo()
            loan_suspense_acc_id = ir_config_param_obj.sudo().get_param('ae_loan_manag.loan_suspense_acc_id')
            if not loan_suspense_acc_id:
                raise UserError(_("Please Configure Loan Suspense Account from Loans -> Configurations -> Settings!"))
            loan_suspense_acc = self.env['account.account'].browse(int(loan_suspense_acc_id))

            difference_acc_id = ir_config_param_obj.sudo().get_param('ae_loan_manag.difference_acc_id')
            if not difference_acc_id:
                raise UserError(_("Please Configure Difference Account from Loans -> Configurations -> Settings!"))
            difference_account = self.env['account.account'].browse(int(difference_acc_id))
            lines = [{
                'account_id': difference_account.id,
                'partner_id': rec.parent_loan_id.partner_id.id or False,
                'debit': 0,
                'credit': rec.difference_amount,
                'amount_currency': -1 * rec.difference_amount,
                'name': rec.parent_loan_id.name,
                'date': fields.Date.today(),
                'ref': 'Difference Credit Entry',
                'currency_id': self.env.company.currency_id.id,
            }, {
                'account_id': loan_suspense_acc.id or False,
                'partner_id': rec.parent_loan_id.partner_id.id or False,
                'debit': rec.difference_amount,
                'credit': 0,
                'amount_currency': rec.difference_amount,
                'name': rec.parent_loan_id.name,
                'date': fields.Date.today(),
                'ref': 'Difference Debit Entry',
                'currency_id': self.env.company.currency_id.id,
            }]

            if rec.loan_id.difference_entry_id:
                entry = rec.loan_id.difference_entry_id
                entry.line_ids.unlink()
                entry.line_ids = [(0, 0, val) for val in lines]

            rec.loan_id.write({
                'loan_amount': round(rec.amount + rec.restructure_fee + rec.tax_amount,
                                     2) if not rec.pay_by_customer else round(rec.amount, 2),
                'restructure_type': rec.restructure_type,
                'restructure_closing_amount': round(rec.amount, 2),
                'restructure_fee': round(rec.restructure_fee, 2),
                'restructure_tax_amount': round(rec.tax_amount, 2),
                'restructuring_write_off_amount': round(rec.write_off_amount, 2),
                'pay_by_customer': rec.pay_by_customer,
            })
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
                                      'restructure_fee': rec.restructure_fee,
                                      'tax_amount': rec.tax_amount,
                                      'state': rec.state,
                                      'restructured_id': rec.id,
                                      'write_off_line_ids': write_off_lines
                                  }))
            rec.parent_loan_id.write({'restructuring_ids': history_lines})


class FetchRestructureWriteoff(models.Model):
    _name = 'fetch.restructure.writeoff'
    _description = "Fetch Restructure Writeoff"

    fetch_restructure_id = fields.Many2one('fetch.restructure.loan')
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
