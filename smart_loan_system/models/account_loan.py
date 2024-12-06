from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from datetime import datetime, date, timedelta
from odoo.exceptions import UserError, Warning
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT, ustr
import logging
import calendar
import pytz
import base64
import time
import psycopg2
from psycopg2 import InterfaceError, OperationalError
import xlsxwriter
import base64
from io import BytesIO


_logger = logging.getLogger(__name__)
try:
    import numpy
    import numpy_financial as npf
except (ImportError, IOError) as err:
    _logger.debug(err)

try:
    import numpy_financial
except (ImportError, IOError) as err:
    _logger.debug(err)


class AccountLoan(models.Model):
    _name = 'account.loan'
    _description = 'Loan'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    def _default_company(self):
        force_company = self._context.get('force_company')
        if not force_company:
            return self.env.user.company_id.id
        return force_company

    def _default_partners(self):
        partners = []
        kyc_retail_partner = self.env['kyc.retail'].search([('status', '=', 'active')])
        kyc_corp_partner = self.env['kyc.corporate'].search([('status', '=', 'active')])
        kyc_group_partner = self.env['kyc.groups'].search([('status', '=', 'active')])
        for retail in kyc_retail_partner:
            partners.append(retail.partner_id.id)
        for corp in kyc_corp_partner:
            partners.append(corp.partner_id.id)
        for group in kyc_group_partner:
            partners.append(group.partner_id.id)
        return partners

    name = fields.Char(copy=False, required=True, string='Name', default='New', tracking=False)
    partner_id = fields.Many2one('res.partner', string='Customer',
                                 help='Name of Customer that borrows the money at an interest rate.', tracking=True)
    kyc_type = fields.Selection(related='partner_id.kyc_type', string='Industry')
    old_loan_name = fields.Char('Old Loan Name', tracking=True)
    compute_partners = fields.Many2many('res.partner', default=_default_partners)

    company_id = fields.Many2one('res.company', default=_default_company)
    type = fields.Selection([
        ('loan', 'Loan'),
        ('laf', 'LAF'),
    ], copy=False, tracking=True, default='loan')
    state = fields.Selection([
        ('draft', 'IN PROGRESS'),
        ('posted', 'ACTIVE'),
        ('cancelled', 'WRITTEN-OFF'),
        ('rejected', 'Rejected'),
        ('closed', 'CLOSED'),
    ], required=True, copy=False, default='draft', tracking=True)
    laf_state = fields.Selection([
        ('pre_draft', 'Pre Draft'),
        ('retail_manager', 'Retail Manager/Corp'),
        ('cross_manager', 'Cross Manager'),
        ('bod', 'BOD'),
        ('sb_approve', 'SB Approve'),
        ('commitment_pa_letter', 'Create Commitment or payment arrangement letter'),
        ('review_edit', 'Review/Edit and Approve LAF'),
        ('cam_approve', 'CAM Approve and Disbursed'),
    ], required=True, copy=False, default='pre_draft', tracking=True)
    line_ids = fields.One2many('account.loan.line', 'loan_id', copy=False)
    periods = fields.Integer(string='No. of Installments',
                             help='Number of periods (months) that the loan will last', tracking=True)
    method_period = fields.Integer(string='Time between two installments(In Month)', default=1,
                                   help="State here the time between 2 installments, in months", required=True,
                                   tracking=True)
    start_date = fields.Date(copy=False,
                             help='Initial date of the loan/first period as given in contract', tracking=True)
    expected_end_date = fields.Date(string="Maturity Date", compute="_get_expected_end_date",
                                    help='Expected end date of closing loan', copy=False, tracking=True, store=True)
    close_date = fields.Date(help='Close Date', readonly=True, copy=False, tracking=True)
    interest_type = fields.Selection([('simple', 'Simple Interest'), ('compound', 'Compound Interest')],
                                     default='compound', tracking=True)
    rate = fields.Float('Rate(%)', required=True, default=0.0, help='Currently applied rate', tracking=True)
    rate_period = fields.Float(string='Rate per month', compute='_compute_rate_period',
                               help='Real rate that will be applied on each period')
    fixed_amount = fields.Monetary(
        currency_field='currency_id',
        compute='_compute_fixed_amount'
    )
    fixed_loan_amount = fields.Monetary(
        currency_field='currency_id',
        readonly=True,
        copy=False,
        default=0, tracking=True
    )
    fixed_periods = fields.Integer(
        readonly=True,
        copy=False,
        default=0, tracking=True
    )
    loan_amount = fields.Monetary(currency_field='currency_id', required=True, tracking=True)
    round_on_end = fields.Boolean(default=True,
                                  help='When checked, the differences will be applied on the last period'
                                       ', if it is unchecked, the annuity will be recalculated on each '
                                       'period (i.e. amount won\'t be the same every month).', tracking=True
                                  )
    payment_on_first_period = fields.Boolean(default=True,
                                             help='When checked, the first payment will be expected on Start Date,'
                                                  'otherwise 1 period (month) after the Start Date.', tracking=True)
    currency_id = fields.Many2one('res.currency', tracking=True, store=True)
    product_id = fields.Many2one('loan.products', string='Loan Product', tracking=True)
    is_leasing = fields.Boolean(default=True, string='Insurance', tracking=True)

    down_payment = fields.Monetary(currency_field='currency_id', string="Down Payment", required=True, tracking=True)
    residual_amount = fields.Monetary(
        currency_field='currency_id',
        default=0.,
        required=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
        help='Residual amount of the land contract that must be paid at the end '
             ' in order to acquire the property', tracking=True
    )
    is_down_payment = fields.Boolean(string="Any Down Payment?", default=True, tracking=True)
    insurance_product_id = fields.Many2one('product.product', string='Life Insurance', tracking=True)
    tax_product_id = fields.Many2one('product.product', string='Fire Insurance', tracking=True)
    invoice_count = fields.Integer(compute='_compute_invoices')
    reverse_entries_count = fields.Integer(compute='_compute_reverse_entries')
    is_compute_items = fields.Boolean(string='Compute Items', copy=False, compute='_compute_items_visibility')
    insurance_balance = fields.Monetary(string='Insurance', compute='cal_ins_tax', currency_field='currency_id')
    tax_balance = fields.Monetary(string='Tax', compute='cal_ins_tax', currency_field='currency_id')
    insurance_sale_price = fields.Monetary(store=True,
                                           string="Life Insurance Amount", readonly=False, tracking=True,
                                           currency_field='currency_id')
    tax_sale_price = fields.Monetary(store=True, string="Fire Insurance Amount", readonly=False, tracking=True,
                                     currency_field='currency_id')
    loan_inv_ids = fields.One2many('loan.invoice', inverse_name='loan_id', string="Loan Invoices")
    total_invoice_amount = fields.Monetary("Upcomming Invoice Amount", compute='get_total_invoice_amount',
                                           tracking=True, currency_field='currency_id')
    total_insurance_amount = fields.Monetary("Monthly Life Insurance Amount", compute='get_total_insurance_amount',
                                             tracking=True, currency_field='currency_id')
    total_fire_insurance_amount = fields.Monetary("Monthly Fire Insurance Amount",
                                                  compute='get_total_fire_insurance_amount',
                                                  tracking=True, currency_field='currency_id')
    total_principal_balance = fields.Monetary('Principal Balance', compute='cal_princi_inter',
                                              currency_field='currency_id')
    total_interest_balance = fields.Monetary('Interest Paid', compute='cal_princi_inter', currency_field='currency_id')
    total_residual_paid = fields.Float('Total Residual Paid', compute='cal_princi_inter')
    total_principal_migration = fields.Monetary('Interest Paid', compute='_cal_principal_migration',
                                                currency_field='currency_id')
    total_paid_penalties = fields.Monetary('Penalties Paid', compute='_compute_paid_penalties',
                                           currency_field='currency_id')
    first_payment_due = fields.Date(string="Installment Due Date", copy=False, tracking=True)
    loan_payment_change_ids = fields.One2many('loan.changes', inverse_name='loan_id', string="Loan Changes", readonly=1)
    comment = fields.Text("Internal Notes", tracking=False)
    stage_comment = fields.Text("Stage Comments", tracking=False)
    transaction_balance = fields.Monetary('Transaction Balance', compute='_compute_transcation_balance',
                                          currency_field='currency_id')
    payment_day = fields.Integer('Payment Day', tracking=True)
    total_payments = fields.Monetary("Total Paid Payments", compute="compute_total_payments",
                                     currency_field='currency_id')
    line_inv_ids = fields.Many2many('account.move')
    days_past_due = fields.Float('Days Due', compute='compute_amount_and_days_due')
    amount_due = fields.Monetary('Total Amount Due', compute='compute_amount_and_days_due')

    processing_fee_inv_id = fields.Many2one('account.move', string="Open items before migration", tracking=True)
    outstanding_bal = fields.Float("Outstanding Balance", compute='compute_outstanding_bal', tracking=True)
    move_by_keep_tax_ins = fields.Boolean("Moved by Keep Tax and Insurance")
    is_collaterals = fields.Boolean('Collaterals', default=False, tracking=True)
    loan_collateral_ids = fields.Many2many('loan.collateral', tracking=True)
    total_collaterals = fields.Integer(compute="_compute_total_collaterals")
    total_documents = fields.Integer(compute="_compute_total_documents")
    loan_type = fields.Selection([('amortizing_loan', 'Amortizing Loan'), ('interest_loan', 'Interest Only Loan')],
                                 required=True, default='amortizing_loan', tracking=True)
    user_id = fields.Many2one('res.users', 'Officer', tracking=True, domain=[('is_officer', '=', True)])
    country_id = fields.Many2one('res.country', 'Country', tracking=True, related='product_id.country_id', store=True)
    country_name = fields.Char(related='country_id.name')
    is_penalty = fields.Boolean(default=False)
    penalty_product_id = fields.Many2one('product.product', string='Penalty Fee', tracking=True, store=True)
    penalty_percent = fields.Float('Penalty Percent(%)', compute='_compute_penalty_percent', store=True, readonly=False,
                                   tracking=True)
    monthly_payment = fields.Monetary(tracking=True, currency_field='currency_id')
    period_or_monthly = fields.Boolean(default=False)
    bonaire_principal_prod_id = fields.Many2one('product.product', string='Life Insurance', tracking=True)
    bonaire_interest_prod_id = fields.Many2one('product.product', string='Fire Insurance', tracking=True)
    bonaire_principal_amount = fields.Monetary(store=True,
                                               string="Life Insurance Amount", readonly=False, tracking=True,
                                               currency_field='currency_id')
    bonaire_interest_amount = fields.Monetary(store=True,
                                              string="Fire Insurance Amount", readonly=False, tracking=True,
                                              currency_field='currency_id')
    is_bod_approve = fields.Boolean(string='First BOD Approve', default=False, tracking=True)
    first_bod_done = fields.Boolean(default=False)
    first_bod_rejection = fields.Boolean(default=False)
    is_laf_posted = fields.Boolean(default=False)
    reject_allow = fields.Boolean(compute='_compute_reject_allow')
    bod_to_commitment = fields.Boolean(default=False)
    total_unpaid_principal = fields.Monetary(compute='calculate_unpaid_amount', tracking=True,
                                             currency_field='currency_id')
    total_unpaid_interest = fields.Monetary(compute='calculate_unpaid_amount', tracking=True,
                                            currency_field='currency_id')
    total_unpaid_life_insurance = fields.Monetary(compute='calculate_unpaid_amount', tracking=True,
                                                  currency_field='currency_id')
    total_unpaid_fire_insurance = fields.Monetary(compute='calculate_unpaid_amount', tracking=True,
                                                  currency_field='currency_id')
    total_penalties = fields.Monetary(compute='calculate_unpaid_amount', tracking=True, currency_field='currency_id')
    only_cao_edit = fields.Boolean(compute='_compute_only_cao_edit')
    only_cam_edit = fields.Boolean(compute='_compute_only_cam_edit')
    cam_date_edit = fields.Boolean(compute='_compute_only_cam_edit')
    is_collateral_group = fields.Boolean(compute='_compute_is_collateral_group')
    write_off_invoice = fields.Boolean(default=True)
    is_restructure_loan = fields.Boolean(default=False)
    restructuring_ids = fields.One2many('loan.restructuring.lines', 'loan_id')
    restructure_type = fields.Selection([('without_writeoff', 'Restructure Without Write Off'),
                                         ('with_writeoff', 'Restructure With Write Off')], string='Restructure Type')
    restructure_closing_amount = fields.Monetary(
        currency_field='currency_id',
        string='Closing Amount')
    restructure_fee = fields.Float()
    restructure_tax_amount = fields.Float('OB')
    restructuring_write_off_amount = fields.Float()
    pay_by_customer = fields.Boolean(default=False)
    restructuring_invoice_count = fields.Integer(compute='_compute_invoices')
    automatic_transfer_entries_count = fields.Integer(compute='_compute_invoices')
    kyc_customer_number = fields.Char(related="partner_id.kyc_customer_number")
    restructured_loan_id = fields.Many2one('account.loan')
    review_edit_text = fields.Char(store=True)
    monthly_interest_accrue = fields.Monetary(string='MTD', currency_field='currency_id')
    yearly_interest_accrue = fields.Monetary(string='YTD', currency_field='currency_id')
    is_accrual = fields.Boolean(default=False)
    loan_migration_group = fields.Char()
    is_ground_lease = fields.Boolean(default=False)
    ground_lease_product_id = fields.Many2one('product.product', string='Ground Lease Product', tracking=True,
                                              store=True)
    ground_lease_amount = fields.Float('Ground Lease Amount', store=True, tracking=True)
    total_paid_ground_lease = fields.Monetary('Paid Ground Lease', compute='_compute_paid_ground_lease',
                                              currency_field='currency_id')
    total_unpaid_ground_lease = fields.Monetary(compute='calculate_unpaid_amount', tracking=True,
                                                currency_field='currency_id')
    redirect_url = fields.Char(compute='_compute_redirect_url')
    tz_datetime = fields.Datetime()
    is_select = fields.Boolean()
    selected_loan_ids = fields.Many2many('account.loan', string='Selected Loans',
                                         relation='account_loan_selected_loan_rel', column1='id',
                                         column2='selected_loan_id')
    restructure_id = fields.Many2one('restructure.loan.wizard')
    is_straight_through = fields.Boolean(default=False, tracking=True)
    payment_journal_id = fields.Many2one('account.journal', domain=[('type', 'in', ('bank', 'cash'))])
    approver_ids = fields.Many2many('res.users')
    report_type = fields.Selection([('interest_report', 'Interest Report'),
                                    ('mortgage_report', 'Mortgage Report')], string='Interest Report')
    is_restructure_cancelled = fields.Boolean(default=False)
    is_cao_edit = fields.Boolean(default=False)
    difference_entry_id = fields.Many2one('account.move')
    account_officer_approver = fields.Many2one('res.users')
    is_accrual_created = fields.Boolean(default=False)


    def _compute_redirect_url(self):
        for rec in self:
            if rec.name and rec.id:
                base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                rec.redirect_url = base_url + '/web?debug=0#id=%s&model=account.loan&view_type=form' % (rec.id)
            else:
                rec.redirect_url = False

    @api.onchange('currency_id')
    def _onchange_currency(self):
        return {
            'domain': {
                'product_id': [('currency_id', '=', self.currency_id.id)]
            }
        }

    @api.depends('type', 'laf_state', 'state')
    def _compute_items_visibility(self):
        for rec in self:
            if rec.type == 'laf':
                if rec.laf_state == 'review_edit' and rec.env.user.has_group('smart_loan_system.group_loan_cao'):
                    rec.is_compute_items = False
                elif rec.laf_state == 'pre_draft':
                    rec.is_compute_items = False
                elif rec.state == 'posted' and rec.env.user.has_group('smart_loan_system.group_loan_cao') or rec.env.user.has_group('smart_loan_system.group_loan_cam'):
                    rec.is_compute_items = False
                else:
                    rec.is_compute_items = True
            elif rec.type == 'loan':
                if rec.state == 'draft':
                    rec.is_compute_items = False
                elif rec.state == 'posted' and rec.env.user.has_group('smart_loan_system.group_loan_cao') or rec.env.user.has_group('smart_loan_system.group_loan_cam'):
                    rec.is_compute_items = False
                else:
                    rec.is_compute_items = True
            else:
                rec.is_compute_items = True

    def calculate_unpaid_amount(self):
        for rec in self:
            config_obj = self.env['ir.config_parameter']

            principal_prod_id = config_obj.sudo().get_param('ae_loan_manag.principal_prod_id')
            interest_prod_id = config_obj.sudo().get_param('ae_loan_manag.interest_prod_id')
            rec.total_unpaid_principal = sum(self.env['account.move.line'].search(
                [('move_id.loan_id', '=', rec.id), ('product_id', '=', int(principal_prod_id)),
                 ('fully_paid', '=', False)]).mapped('unpaid_amount'))
            rec.total_unpaid_interest = sum(self.env['account.move.line'].search(
                [('move_id.loan_id', '=', rec.id), ('product_id', '=', int(interest_prod_id)),
                 ('fully_paid', '=', False)]).mapped('unpaid_amount'))

            rec.total_penalties = sum(self.env['account.move.line'].search(
                [('move_id.loan_id', '=', rec.id), ('product_id', '=', rec.penalty_product_id.id),
                 ('fully_paid', '=', False)]).mapped('unpaid_amount'))

            rec.total_unpaid_life_insurance = sum(self.env['account.move.line'].search(
                [('move_id.loan_id', '=', rec.id), ('product_id', '=', rec.bonaire_principal_prod_id.id),
                 ('fully_paid', '=', False)]).mapped('unpaid_amount'))
            rec.total_unpaid_fire_insurance = sum(self.env['account.move.line'].search(
                [('move_id.loan_id', '=', rec.id), ('product_id', '=', rec.bonaire_interest_prod_id.id),
                 ('fully_paid', '=', False)]).mapped('unpaid_amount'))
            rec.total_unpaid_ground_lease = sum(self.env['account.move.line'].search(
                [('move_id.loan_id', '=', rec.id), ('product_id', '=', rec.ground_lease_product_id.id),
                 ('fully_paid', '=', False)]).mapped('unpaid_amount'))

    def view_unpaid_principal(self):
        self.ensure_one()
        config_obj = self.env['ir.config_parameter']

        principal_prod_id = config_obj.sudo().get_param('ae_loan_manag.principal_prod_id')

        domain = [('move_id.loan_id', '=', self.id), ('product_id', '=', int(principal_prod_id)),
                  ('fully_paid', '=', False)]

        invoice_lines = self.env['account.move.line'].search(domain).ids

        action = self.env.ref('smart_loan_system.loan_invoice_line_action')
        result = action.read()[0]
        result['domain'] = [('id', 'in', invoice_lines)]
        return result

    def view_unpaid_interest(self):
        self.ensure_one()
        config_obj = self.env['ir.config_parameter']

        interest_prod_id = config_obj.sudo().get_param('ae_loan_manag.interest_prod_id')

        domain = [('move_id.loan_id', '=', self.id), ('product_id', '=', int(interest_prod_id)),
                  ('fully_paid', '=', False)]

        invoice_lines = self.env['account.move.line'].search(domain).ids
        action = self.env.ref('smart_loan_system.loan_invoice_line_action')
        result = action.read()[0]
        result['domain'] = [('id', 'in', invoice_lines)]
        return result

    def view_unpaid_life_insurance(self):
        self.ensure_one()
        domain = [('move_id.loan_id', '=', self.id), ('fully_paid', '=', False),
                  ('product_id', '=', self.bonaire_principal_prod_id.id)]

        invoice_lines = self.env['account.move.line'].search(domain).ids
        action = self.env.ref('smart_loan_system.loan_invoice_line_action')
        result = action.read()[0]
        result['domain'] = [('id', 'in', invoice_lines)]
        return result

    def view_unpaid_fire_insurance(self):
        self.ensure_one()
        domain = [('move_id.loan_id', '=', self.id), ('fully_paid', '=', False),
                  ('product_id', '=', self.bonaire_interest_prod_id.id)]

        invoice_lines = self.env['account.move.line'].search(domain).ids
        action = self.env.ref('smart_loan_system.loan_invoice_line_action')
        result = action.read()[0]
        result['domain'] = [('id', 'in', invoice_lines)]
        return result

    def view_unpaid_ground_lease(self):
        self.ensure_one()
        domain = [('move_id.loan_id', '=', self.id), ('fully_paid', '=', False),
                  ('product_id', '=', self.ground_lease_product_id.id)]

        invoice_lines = self.env['account.move.line'].search(domain).ids
        action = self.env.ref('smart_loan_system.loan_invoice_line_action')
        result = action.read()[0]
        result['domain'] = [('id', 'in', invoice_lines)]
        return result

    def view_penalties(self):
        self.ensure_one()
        domain = [('move_id.loan_id', '=', self.id), ('fully_paid', '=', False),
                  ('product_id', '=', self.penalty_product_id.id)]

        invoice_lines = self.env['account.move.line'].search(domain).ids
        action = self.env.ref('smart_loan_system.loan_invoice_line_action')
        result = action.read()[0]
        result['domain'] = [('id', 'in', invoice_lines)]
        return result

    def fetch_restructured_loan(self):
        for rec in self:
            fetch_restructure_loan = self.env['fetch.restructure.loan']
            existing_fetch_restructure_loan = fetch_restructure_loan.search(
                [('loan_id', '=', rec.id), ('state', '!=', 'draft')],
                limit=1)
            if existing_fetch_restructure_loan:
                fetch_restructure_loan = existing_fetch_restructure_loan
            else:
                write_off_lines = []
                for line in rec.restructure_id.writeoff_line_ids:
                    write_off_lines.append((0, 0,
                                            {
                                                'loan_id': line.loan_id.id,
                                                'write_off_amount': line.write_off_amount,
                                                'company_currency_amount': line.company_currency_amount,
                                            }))
                fetch_restructure_loan = fetch_restructure_loan.create({'loan_id': rec.id,
                                                                        'parent_loan_id': rec.restructure_id.parent_loan_id.id,
                                                                        'restructure_type': rec.restructure_id.restructure_type,
                                                                        'outstanding_principal_amount': rec.restructure_id.parent_loan_id.outstanding_bal - rec.restructure_id.parent_loan_id.total_unpaid_principal,
                                                                        'remaining_principal_amount': rec.restructure_id.parent_loan_id.total_unpaid_principal,
                                                                        'remaining_interest_amount': rec.restructure_id.parent_loan_id.total_unpaid_interest,
                                                                        'remaining_life_insurance_amount': rec.restructure_id.parent_loan_id.total_unpaid_life_insurance,
                                                                        'remaining_fire_insurance_amount': rec.restructure_id.parent_loan_id.total_unpaid_fire_insurance,
                                                                        'remaining_penalties_amount': rec.restructure_id.parent_loan_id.total_penalties,
                                                                        'remaining_ground_lease': rec.restructure_id.parent_loan_id.total_unpaid_ground_lease,
                                                                        'difference_amount': rec.restructure_id.parent_loan_id.total_penalties + rec.restructure_id.parent_loan_id.total_unpaid_interest,
                                                                        'pay_by_customer': rec.restructure_id.pay_by_customer,
                                                                        'reject_reason': rec.restructure_id.reject_reason,
                                                                        'writeoff_line_ids': write_off_lines,
                                                                        'state': 'draft'})

            return {
                'name': _('Fetch Restructure Loan'),
                'res_model': 'fetch.restructure.loan',
                'res_id': existing_fetch_restructure_loan.id or fetch_restructure_loan.id,
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'view_id': False,
                'target': 'new'
            }

    def restructure_loan(self):
        for rec in self:
            if rec.is_select and rec.selected_loan_ids and not rec.is_restructure_cancelled:
                restructure_loan = self.env['restructure.loan.wizard'].search(
                    [('loan_ids', 'in', rec.selected_loan_ids.ids), ('state', 'not in', ('rejected', 'approved'))],
                    limit=1)

                return {
                    'name': _('Restructure Loan'),
                    'res_model': 'restructure.loan.wizard',
                    'res_id': restructure_loan.id,
                    'type': 'ir.actions.act_window',
                    'view_mode': 'form',
                    'view_id': False,
                    'target': 'new'
                }
            else:
                select_restructure_loan = self.env['select.restructure.loan']
                existing_select_restructure_loan = select_restructure_loan.search([('parent_loan_id', '=', rec.id)],
                                                                                  limit=1)
                if existing_select_restructure_loan:
                    select_restructure_loan = existing_select_restructure_loan
                else:
                    select_restructure_loan = select_restructure_loan.create({'parent_loan_id': rec.id,
                                                                              })
                if not select_restructure_loan.line_ids.filtered(lambda l: l.loan_id.id == rec.id):
                    select_restructure_loan.write({'line_ids': [(0, 0, {'loan_id': rec.id,
                                                                        })]})

                return {
                    'name': _('Select Loans To Restructure'),
                    'res_model': 'select.restructure.loan',
                    'res_id': existing_select_restructure_loan.id or select_restructure_loan.id,
                    'type': 'ir.actions.act_window',
                    'view_mode': 'form',
                    'view_id': False,
                    'target': 'new'
                }

    def extra_payment_loan(self):
        for rec in self:
            extra_payment_loan = self.env['account.loan.pay.amount']
            existing_extra_payment_loan = extra_payment_loan.search(
                [('loan_id', '=', rec.id), ('state', '!=', 'approved')], limit=1)
            if existing_extra_payment_loan:
                extra_payment_loan = existing_extra_payment_loan
            else:
                extra_payment_loan = extra_payment_loan.create({'loan_id': rec.id,
                                                                'date': fields.Date.today()})

            return {
                'name': _('Extra Payment'),
                'res_model': 'account.loan.pay.amount',
                'res_id': existing_extra_payment_loan.id or extra_payment_loan.id,
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'view_id': False,
                'target': 'new'
            }

    def loan_delinquent(self):
        return {
            'name': _('Loan Delinquent'),
            'domain': [('loan_ids', '=', self.ids)],
            'res_model': 'loan.delinquent.wizard',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_loan_ids': self.ids}
        }

    def view_restructuring_invoices(self):
        """
        This method is called from Invoices widget to display all the invoice related to loan
        :return: Invoices tree view
        """
        self.ensure_one()
        action = self.env.ref('account.action_move_journal_line')
        result = action.read()[0]
        result['domain'] = [
            ('loan_id', '=', self.id), ('move_type', '=', 'entry'), ('is_restructuring_inv', '=', True)
        ]
        return result

    def view_automatic_transfer_entries(self):
        """
        This method is called from Invoices widget to display all the invoice related to loan
        :return: Invoices tree view
        """
        self.ensure_one()
        action = self.env.ref('account.action_move_journal_line')
        result = action.read()[0]
        result['domain'] = [
            ('loan_id', '=', self.id), ('move_type', '=', 'entry'), ('is_automatic_entry', '=', True)
        ]
        result['context'] = {'search_default_posted': 0}

        return result

    @api.depends('type', 'laf_state')
    def _compute_only_cao_edit(self):
        for rec in self:
            if rec.type == 'laf':
                if rec.laf_state == 'review_edit' and rec.env.user.has_group('smart_loan_system.group_loan_cao'):
                    rec.only_cao_edit = True
                elif rec.laf_state == 'pre_draft' and rec.env.user.has_group('smart_loan_system.group_loan_account_officer'):
                    rec.only_cao_edit = True
                elif rec.state == 'posted' and rec.env.user.has_group('smart_loan_system.group_loan_cao'):
                    rec.only_cao_edit = True
                else:
                    rec.only_cao_edit = False
            elif rec.type == 'loan':
                if rec.state == 'draft':
                    rec.only_cao_edit = True
                elif rec.state == 'posted' and rec.env.user.has_group('smart_loan_system.group_loan_cao'):
                    rec.only_cao_edit = True
                else:
                    rec.only_cao_edit = False
            else:
                rec.only_cao_edit = False

    @api.depends('type', 'laf_state')
    def _compute_only_cam_edit(self):
        for rec in self:
            if rec.type == 'laf':
                if rec.state == 'posted' and rec.env.user.has_group('smart_loan_system.group_loan_cam'):
                    rec.only_cam_edit = True
                    rec.cam_date_edit = True
                if rec.laf_state == 'review_edit' and rec.env.user.has_group('smart_loan_system.group_loan_cam'):
                    rec.only_cam_edit = False
                    rec.cam_date_edit = True
                else:
                    rec.only_cam_edit = False
                    rec.cam_date_edit = False
            elif rec.type == 'loan':
                if rec.state == 'posted' and rec.env.user.has_group('smart_loan_system.group_loan_cam'):
                    rec.only_cam_edit = True
                    rec.cam_date_edit = False
                elif rec.state == 'draft':
                    rec.only_cam_edit = True
                    rec.cam_date_edit = False
                else:
                    rec.only_cam_edit = False
                    rec.cam_date_edit = True
            else:
                rec.only_cam_edit = False
                rec.cam_date_edit = False

    @api.depends('type')
    def _compute_is_collateral_group(self):
        for rec in self:
            if rec.type in ('loan', 'laf'):
                if rec.env.user.has_group('smart_loan_system.group_loan_cao') or rec.env.user.has_group(
                        'smart_loan_system.group_loan_cam'):
                    rec.is_collateral_group = True
                else:
                    rec.is_collateral_group = False
            else:
                rec.is_collateral_group = False

    @api.depends('type', 'laf_state', 'kyc_type')
    def _compute_reject_allow(self):
        for rec in self:
            if rec.type == 'laf':
                if rec.laf_state == 'pre_draft':
                    rec.reject_allow = False
                elif rec.laf_state == 'retail_manager' and rec.kyc_type == 'retail' and (self.env.user.has_group(
                        'smart_loan_system.group_loan_retail_manager')):
                    rec.reject_allow = True
                elif rec.laf_state == 'retail_manager' and rec.kyc_type in ('corporate', 'group') and (
                        self.env.user.has_group(
                            'smart_loan_system.group_loan_corp_manager')):
                    rec.reject_allow = True
                elif rec.laf_state == 'cross_manager' and rec.kyc_type == 'retail' and (self.env.user.has_group(
                        'smart_loan_system.group_loan_retail_manager')):
                    rec.reject_allow = False
                elif rec.laf_state == 'cross_manager' and rec.kyc_type in ('corporate', 'group') and (
                        self.env.user.has_group(
                            'smart_loan_system.group_loan_corp_manager')):
                    rec.reject_allow = False
                elif rec.laf_state == 'cross_manager' and rec.kyc_type == 'retail' and self.env.user.has_group(
                        'smart_loan_system.group_loan_corp_manager'):
                    rec.reject_allow = True
                elif rec.laf_state == 'cross_manager' and rec.kyc_type in (
                        'corporate', 'group') and self.env.user.has_group(
                    'smart_loan_system.group_loan_retail_manager'):
                    rec.reject_allow = True
                elif rec.laf_state == 'bod' and rec.kyc_type == 'retail' and self.env.user.has_group(
                        'smart_loan_system.group_loan_corp_manager'):
                    rec.reject_allow = False
                elif rec.laf_state == 'bod' and rec.kyc_type in ('corporate', 'group') and self.env.user.has_group(
                        'smart_loan_system.group_loan_retail_manager'):
                    rec.reject_allow = False
                elif rec.laf_state == 'bod' and self.env.user.has_group(
                        'smart_loan_system.group_loan_bod') and rec.is_bod_approve == False:
                    rec.reject_allow = True
                elif rec.laf_state == 'bod' and self.env.user.has_group(
                        'smart_loan_system.group_loan_bod') and rec.is_bod_approve == True:
                    rec.reject_allow = False
                elif rec.laf_state == 'bod' and self.env.user.has_group(
                        'smart_loan_system.group_loan_second_bod') and rec.is_bod_approve == True:
                    rec.reject_allow = True
                elif rec.laf_state == 'sb_approve' and self.env.user.has_group(
                        'smart_loan_system.group_loan_bod') or self.env.user.has_group(
                    'smart_loan_system.group_loan_second_bod'):
                    rec.reject_allow = False
                elif rec.laf_state == 'sb_approve' and self.env.user.has_group('smart_loan_system.group_loan_sb'):
                    rec.reject_allow = True
                elif rec.laf_state == 'commitment_pa_letter' and self.env.user.has_group(
                        'smart_loan_system.group_loan_sb'):
                    rec.reject_allow = False
                elif rec.laf_state == 'commitment_pa_letter':
                    rec.reject_allow = True
                elif rec.laf_state == 'review_edit' and self.env.user.has_group('smart_loan_system.group_loan_cao'):
                    rec.reject_allow = True
                elif rec.laf_state == 'cam_approve' and self.env.user.has_group('smart_loan_system.group_loan_cam'):
                    rec.reject_allow = True
                else:
                    rec.reject_allow = False
            elif rec.type == 'loan':
                rec.reject_allow = False
            else:
                rec.reject_allow = False

    def account_officer_confirm_loan(self):
        for rec in self:
            rec.write({'laf_state': 'retail_manager',
                       'period_or_monthly': True,
                       'approver_ids': [(4, self.env.user.id)],
                       'account_officer_approver': self.env.user.id
                       })
            group = False
            users_in_group = False
            admin = rec.env['res.users'].search([('id', '=', 2)])
            if rec.kyc_type == 'retail':
                group = self.env.ref('smart_loan_system.group_loan_retail_manager')
                users_in_group = self.env['res.users'].search([('groups_id', 'in', group.id)])
            if rec.kyc_type in ('corporate', 'group'):
                group = self.env.ref('smart_loan_system.group_loan_corp_manager')
                users_in_group = self.env['res.users'].search([('groups_id', 'in', group.id)])
            for user in users_in_group:
                self.env['mail.message'].create({
                    'message_type': "notification",
                    'body': "The Loan" + ' ' + rec.name + ' has been sent to you for further action-',
                    'subject': "Action Required",
                    'partner_ids': [(4, user.partner_id.id)],
                    'model': rec._name,
                    'res_id': rec.id,
                    'notification_ids': [(0, 0,
                                          {
                                              'res_partner_id': user.partner_id.id,
                                              'notification_type': 'inbox'
                                          }
                                          )],
                    'author_id': rec.env.user.partner_id and rec.env.user.partner_id.id
                })
                template_id = self.env.ref('smart_loan_system.stage_action_required_mail_template')
                template = self.env['mail.template'].browse(template_id.id)
                if template:
                    template.write({'email_to': user.email or user.partner_id.email,
                                    'email_from': admin.email if admin else False})
                    template.send_mail(rec.id, True)

            return {
                'name': _('LAF Stage Comment'),
                'domain': [('loan_id', '=', self.id)],
                'res_model': 'laf.stage.comment',
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'target': 'new',
                'context': {'default_loan_id': self.id}
            }

    def retail_manager_approve_loan(self):
        for rec in self:
            rec.write({'laf_state': 'cross_manager',
                       'approver_ids': [(4, self.env.user.id)]})
            group = False
            users_in_group = False
            admin = rec.env['res.users'].search([('id', '=', 2)])
            if rec.kyc_type == 'retail':
                group = self.env.ref('smart_loan_system.group_loan_corp_manager')
                users_in_group = self.env['res.users'].search([('groups_id', 'in', group.id)])
            if rec.kyc_type in ('corporate', 'group'):
                group = self.env.ref('smart_loan_system.group_loan_retail_manager')
                users_in_group = self.env['res.users'].search([('groups_id', 'in', group.id)])
            for user in users_in_group:
                self.env['mail.message'].create({
                    'message_type': "notification",
                    'body': "The Loan" + ' ' + rec.name + ' has been sent to you for further action-',
                    'subject': "Action Required",
                    'partner_ids': [(4, user.partner_id.id)],
                    'model': rec._name,
                    'res_id': rec.id,
                    'notification_ids': [(0, 0,
                                          {
                                              'res_partner_id': user.partner_id.id,
                                              'notification_type': 'inbox'
                                          }
                                          )],
                    'author_id': rec.env.user.partner_id and rec.env.user.partner_id.id
                })
                template_id = self.env.ref('smart_loan_system.stage_action_required_mail_template')
                template = self.env['mail.template'].browse(template_id.id)
                if template:
                    template.write({'email_to': user.email or user.partner_id.email,
                                    'email_from': admin.email if admin else False})
                    template.send_mail(rec.id, True)

            return {
                'name': _('LAF Stage Comment'),
                'domain': [('loan_id', '=', self.id)],
                'res_model': 'laf.stage.comment',
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'target': 'new',
                'context': {'default_loan_id': self.id}
            }

    def cross_manager_approve_loan(self):
        for rec in self:
            rec.write({'laf_state': 'bod',
                       'approver_ids': [(4, self.env.user.id)]})
            admin = rec.env['res.users'].search([('id', '=', 2)])
            group = self.env.ref('smart_loan_system.group_loan_bod')
            users_in_group = self.env['res.users'].search([('groups_id', 'in', group.id)])
            for user in users_in_group:
                self.env['mail.message'].create({
                    'message_type': "notification",
                    'body': "The Loan" + ' ' + rec.name + ' has been sent to you for further action-',
                    'subject': "Action Required",
                    'partner_ids': [(4, user.partner_id.id)],
                    'model': rec._name,
                    'res_id': rec.id,
                    'notification_ids': [(0, 0,
                                          {
                                              'res_partner_id': user.partner_id.id,
                                              'notification_type': 'inbox'
                                          }
                                          )],
                    'author_id': rec.env.user.partner_id and rec.env.user.partner_id.id
                })
                template_id = self.env.ref('smart_loan_system.stage_action_required_mail_template')
                template = self.env['mail.template'].browse(template_id.id)
                if template:
                    template.write({'email_to': user.email or user.partner_id.email,
                                    'email_from': admin.email if admin else False})
                    template.send_mail(rec.id, True)

            return {
                'name': _('LAF Stage Comment'),
                'domain': [('loan_id', '=', self.id)],
                'res_model': 'laf.stage.comment',
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'target': 'new',
                'context': {'default_loan_id': self.id}
            }

    def bod_approve_loan(self):
        return {
            'name': _('Send to SB?'),
            'domain': [('loan_id', '=', self.id)],
            'res_model': 'sb.approval.wizard',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_loan_id': self.id}
        }

    def approve1_loan(self):
        return {
            'name': _('Send to SB?'),
            'domain': [('loan_id', '=', self.id)],
            'res_model': 'sb.approval.wizard',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_loan_id': self.id}
        }

    def sb_approve_loan(self):
        for rec in self:
            rec.write({'laf_state': 'commitment_pa_letter',
                       'approver_ids': [(4, self.env.user.id)]})
            admin = rec.env['res.users'].search([('id', '=', 2)])
            group = self.env.ref('smart_loan_system.group_loan_cam')
            users_in_group = self.env['res.users'].search([('groups_id', 'in', group.id)])
            for user in users_in_group:
                self.env['mail.message'].create({
                    'message_type': "notification",
                    'body': "The Loan" + ' ' + rec.name + ' has been sent to you for further action-',
                    'subject': "Action Required",
                    'partner_ids': [(4, user.partner_id.id)],
                    'model': rec._name,
                    'res_id': rec.id,
                    'notification_ids': [(0, 0,
                                          {
                                              'res_partner_id': user.partner_id.id,
                                              'notification_type': 'inbox'
                                          }
                                          )],
                    'author_id': rec.env.user.partner_id and rec.env.user.partner_id.id
                })
                template_id = self.env.ref('smart_loan_system.stage_action_required_mail_template')
                template = self.env['mail.template'].browse(template_id.id)
                if template:
                    template.write({'email_to': user.email or user.partner_id.email,
                                    'email_from': admin.email if admin else False})
                    template.send_mail(rec.id, True)

            return {
                'name': _('LAF Stage Comment'),
                'domain': [('loan_id', '=', self.id)],
                'res_model': 'laf.stage.comment',
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'target': 'new',
                'context': {'default_loan_id': self.id}
            }

    def create_commitment_loan(self):
        for rec in self:
            rec.write({'laf_state': 'review_edit',
                       'period_or_monthly': False,
                       'approver_ids': [(4, self.env.user.id)]})
            admin = rec.env['res.users'].search([('id', '=', 2)])
            group = self.env.ref('smart_loan_system.group_loan_cao')
            users_in_group = self.env['res.users'].search([('groups_id', 'in', group.id)])
            for user in users_in_group:
                self.env['mail.message'].create({
                    'message_type': "notification",
                    'body': "The Loan" + ' ' + rec.name + ' has been sent to you for further action-',
                    'subject': "Action Required",
                    'partner_ids': [(4, user.partner_id.id)],
                    'model': rec._name,
                    'res_id': rec.id,
                    'notification_ids': [(0, 0,
                                          {
                                              'res_partner_id': user.partner_id.id,
                                              'notification_type': 'inbox'
                                          }
                                          )],
                    'author_id': rec.env.user.partner_id and rec.env.user.partner_id.id
                })
                template_id = self.env.ref('smart_loan_system.stage_action_required_mail_template')
                template = self.env['mail.template'].browse(template_id.id)
                if template:
                    template.write({'email_to': user.email or user.partner_id.email,
                                    'email_from': admin.email if admin else False})
                    template.send_mail(rec.id, True)

            return {
                'name': _('LAF Stage Comment'),
                'domain': [('loan_id', '=', self.id)],
                'res_model': 'laf.stage.comment',
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'target': 'new',
                'context': {'default_loan_id': self.id}
            }

    def cao_approve_loan(self):
        for rec in self:
            rec.write({'laf_state': 'cam_approve',
                       'period_or_monthly': True})
            admin = rec.env['res.users'].search([('id', '=', 2)])
            if rec.is_cao_edit:
                curacao_tz = pytz.timezone('America/Curacao')
                tz_aware_datetime = datetime.now(curacao_tz)
                rec.tz_datetime = tz_aware_datetime.replace(tzinfo=None)
                for user in rec.approver_ids:
                    self.env['mail.message'].create({
                        'message_type': "notification",
                        'body': "The Loan" + ' ' + rec.name + ' has been modified by-' + ' ' + rec.env.user.name,
                        'subject': "Loan Modified",
                        'partner_ids': [(4, user.partner_id.id)],
                        'model': rec._name,
                        'res_id': rec.id,
                        'notification_ids': [(0, 0,
                                              {
                                                  'res_partner_id': user.partner_id.id,
                                                  'notification_type': 'inbox'
                                              }
                                              )],
                        'author_id': rec.env.user.partner_id and rec.env.user.partner_id.id
                    })

                    template_id = self.env.ref('smart_loan_system.credit_committee_mail_template')
                    template = self.env['mail.template'].browse(template_id.id)
                    if template:
                        template.write({'email_to': user.email or user.partner_id.email,
                                        'email_from': admin.email if admin else False})
                        template.send_mail(rec.id, True)
            group = self.env.ref('smart_loan_system.group_loan_cam')
            users_in_group = self.env['res.users'].search([('groups_id', 'in', group.id)])
            for user in users_in_group:
                self.env['mail.message'].create({
                    'message_type': "notification",
                    'body': "The Loan" + ' ' + rec.name + ' has been sent to you for further action-',
                    'subject': "Action Required",
                    'partner_ids': [(4, user.partner_id.id)],
                    'model': rec._name,
                    'res_id': rec.id,
                    'notification_ids': [(0, 0,
                                          {
                                              'res_partner_id': user.partner_id.id,
                                              'notification_type': 'inbox'
                                          }
                                          )],
                    'author_id': rec.env.user.partner_id and rec.env.user.partner_id.id
                })
                template_id = self.env.ref('smart_loan_system.stage_action_required_mail_template')
                template = self.env['mail.template'].browse(template_id.id)
                if template:
                    template.write({'email_to': user.email or user.partner_id.email,
                                    'email_from': admin.email if admin else False})
                    template.send_mail(rec.id, True)
            return {
                'name': _('LAF Stage Comment'),
                'domain': [('loan_id', '=', self.id)],
                'res_model': 'laf.stage.comment',
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'target': 'new',
                'context': {'default_loan_id': self.id}
            }

    def validate_loan(self):
        for rec in self:
            rec.is_laf_posted = True
            rec.post_loan()
            rec.write({"type": "loan"})

    def reject_loan(self):
        return {
            'name': _('Reject Loan'),
            'domain': [('loan_id', '=', self.id)],
            'res_model': 'reject.loan',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_loan_id': self.id}
        }

    def reject_restructured_loan(self):
        return {
            'name': _('Reject Restructured Loan'),
            'domain': [('loan_id', '=', self.id)],
            'res_model': 'reject.restructured.loan',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_loan_id': self.id}
        }

    @api.model
    def assign_state_to_histories(self):
        transaction_histories = self.env['loan.transaction.history'].search([])
        payment_histories = self.env['account.payment.history'].search([])
        for trans in transaction_histories:
            if not trans.state:
                trans.state = 'running'
        for pay in payment_histories:
            if not pay.state:
                pay.state = 'running'

    def reset_loan_accruals(self):
        for rec in self:
            if rec.line_ids and rec.is_accrual:
                for line in rec.line_ids:
                    accrual_interest_lines = self.env['loan.accrual.interest'].search(
                        ['|', ('loan_id', '=', rec.id), ('loan_line_id', '=', line.id)])
                    accrual_penalty_lines = self.env['loan.accrual.penalty'].search(
                        ['|', ('loan_id', '=', rec.id), ('loan_line_id', '=', line.id)])
                    accrual = self.env['loan.accrual']
                    if accrual_interest_lines:
                        accrual_interest_lines.unlink()
                    if accrual_penalty_lines:
                        accrual_penalty_lines.unlink()
                    if line.interest_accrue or line.penalty_accrue:
                        line.interest_accrue = 0.0
                        line.penalty_accrue = 0.0
                    else:
                        pass
            else:
                pass

    @api.onchange('is_penalty')
    def _default_penalty_product(self):
        for rec in self:
            if rec.is_penalty:
                result = self.env['ir.config_parameter'].sudo().get_param('ae_loan_manag.penalty_prod_id')
                if result:
                    rec.penalty_product_id = self.env['product.product'].search([('id', '=', result)])
                else:
                    raise UserError(_("Please add Penalty Product in  Loans -> Configurations -> Settings!"))

    @api.onchange('is_ground_lease')
    def _default_ground_lease_product(self):
        for rec in self:
            if rec.is_ground_lease:
                result = self.env['ir.config_parameter'].sudo().get_param('ae_loan_manag.ground_lease_product_id')
                if result:
                    rec.ground_lease_product_id = self.env['product.product'].search([('id', '=', result)])
                else:
                    raise UserError(_("Please add Ground Lease Product in  Loans -> Configurations -> Settings!"))

    @api.onchange('is_leasing')
    def _default_products(self):
        for rec in self:
            principal_prod = self.env['ir.config_parameter'].sudo().get_param(
                'ae_loan_manag.bonaire_principal_prod_id')
            if principal_prod:
                rec.bonaire_principal_prod_id = self.env['product.product'].search([('id', '=', principal_prod)])
            else:
                raise UserError(_("Please add Bonaire Principal Product in  Loans -> Configurations -> Settings!"))
            interest_prod = self.env['ir.config_parameter'].sudo().get_param(
                'ae_loan_manag.bonaire_interest_prod_id')
            if interest_prod:
                rec.bonaire_interest_prod_id = self.env['product.product'].search([('id', '=', interest_prod)])
            else:
                raise UserError(_("Please add Bonaire Interest Product in  Loans -> Configurations -> Settings!"))

    @api.depends('country_id', 'rate', 'is_penalty', 'product_id')
    def _compute_penalty_percent(self):
        bonaire_country = self.env['res.country'].search([('name', '=', 'Bonaire, Sint Eustatius and Saba')])
        curacao_country = self.env['res.country'].search([('name', '=', 'Curaçao')])
        for rec in self:
            if rec.is_penalty and rec.country_id == bonaire_country:
                rec.penalty_percent = rec.rate
            elif rec.is_penalty and rec.country_id == curacao_country and rec.product_id.penalties_rate:
                rec.penalty_percent = float(rec.product_id.penalties_rate.replace('%', ''))
            else:
                rec.penalty_percent = 0.0

    @api.constrains('penalty_percent', 'product_id', 'rate', 'country_id')
    def _check_penalty_percent(self):
        bonaire_country = self.env['res.country'].search([('name', '=', 'Bonaire, Sint Eustatius and Saba')])
        curacao_country = self.env['res.country'].search([('name', '=', 'Curaçao')])
        for rec in self:
            if rec.country_id == bonaire_country and rec.penalty_percent > rec.rate:
                raise UserError(_("You cannot add penalty percent greater than rate"))
            elif rec.country_id == curacao_country and rec.penalty_percent > float(
                    rec.product_id.penalties_rate.replace('%', '')):
                raise UserError(_("You cannot add rate greater than penalty rate on product"))

    def view_collaterals(self):
        return {
            'name': _('Collaterals'),
            'domain': [('customer_id', '=', self.partner_id.id),
                       ('id', 'in', self.loan_collateral_ids.ids)],
            'res_model': 'loan.collateral',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'context': {'default_customer_id': self.partner_id.id}
        }

    def view_documents(self):
        return {
            'name': _('Documents'),
            'domain': [('res_model', '=', 'account.loan'), ('res_id', '=', self.id)],
            'res_model': 'documents.document',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,kanban',
            'context': {
                'default_res_model': 'account.loan', 'default_res_id': self.id, "searchpanel_default_folder_id": False,
                'default_legal_name': self.name,
            },
        }

    def _compute_total_documents(self):
        read_group_var = self.env['documents.document'].search_count(
            [('res_model', '=', 'account.loan'), ('res_id', '=', self.id)])
        for record in self:
            record.total_documents = read_group_var

    @api.depends('partner_id')
    def _compute_total_collaterals(self):
        for rec in self:
            if rec.loan_collateral_ids:
                rec.total_collaterals = len(rec.loan_collateral_ids)
            else:
                rec.total_collaterals = 0

    @api.constrains('rate', 'product_id')
    def _check_rate(self):
        for rec in self:
            if rec.rate < float(rec.product_id.interest_min.replace('%', '').replace('.', '')):
                raise UserError(_("You cannot add rate less than interest rate"))
            elif rec.rate > float(rec.product_id.interest_max.replace('%', '').replace('.', '')) and float(
                    rec.product_id.interest_max.replace('%', '').replace('.', '')) != 0.0:
                raise UserError(_("You cannot add rate greater than interest rate"))

    @api.constrains('loan_amount', 'product_id')
    def _check_loan_amount(self):
        for rec in self:
            if rec.loan_amount < float(rec.product_id.amount_minimum):
                raise UserError(_("You cannot add loan amount less than amount minimum"))
            elif rec.loan_amount > float(rec.product_id.amount_maximum) and float(rec.product_id.amount_maximum) != 0.0:
                raise UserError(_("You cannot add loan amount greater than amount maximum"))

    @api.constrains('first_payment_due', 'start_date', 'product_id')
    def _check_installment_due_date(self):
        for rec in self:
            difference = relativedelta(rec.first_payment_due, rec.start_date)
            total_months = difference.years * 12 + difference.months
            if total_months < rec.product_id.grace_period_min:
                raise UserError(_("You cannot add installment due date less than minimum grace period months"))
            elif total_months > rec.product_id.grace_period_max:
                raise UserError(_("You cannot add installment due date greater than maximum grace period months"))

    # @api.depends('line_inv_ids.amount_residual', 'line_inv_ids.invoice_date_due')
    def compute_amount_and_days_due(self):
        inv_obj = self.env['account.move']
        for loan in self:
            if loan.partner_id:
                invoice_ids = inv_obj.search([('partner_id', '=', loan.partner_id.id),
                                              ('move_type', '=', 'out_invoice'), ('state', '=', 'posted'),
                                              ('loan_id', '=', loan.id), ('invoice_date_due', '<', fields.Date.today()), ('payment_state', 'in', ('not_paid', 'partial'))])
                residual = days = 0.0
                format_str = '%Y-%m-%d'
                for inv in invoice_ids:
                    residual += inv.amount_residual
                    if inv.invoice_date_due:
                        datetime_obj = datetime.strptime(str(inv.invoice_date_due), format_str)
                        today_date = datetime.strptime(str(fields.Date.today()), format_str)
                        if today_date > datetime_obj:
                            day_count = (today_date - datetime_obj).days
                            if day_count > days:
                                days = day_count
                loan.amount_due = residual
                loan.days_past_due = days
                refund_invoice_ids = inv_obj.search([('partner_id', '=', loan.partner_id.id),
                                                     ('move_type', '=', 'out_refund'), ('state', '=', 'posted')])
                refund_amount = 0.0
                for refund in refund_invoice_ids:
                    refund_amount += refund.amount_residual
                if residual and refund_amount > 0.0:
                    loan.amount_due = residual - refund_amount

            else:
                loan.amount_due = 0.0
                loan.days_past_due = False

    def compute_total_payments(self):
        """
        Calculate total payment of this customer for this loan
        :return: Total Payment Amount
        """
        pay_his = self.env['account.payment.history']
        for loan in self:
            payment_history_rec = pay_his.search([('loan_id', '=', loan.id), ('state', '=', 'running')])
            total = sum(rec.amount for rec in payment_history_rec)
            loan.total_payments = total

    @api.onchange('first_payment_due')
    def set_payment_day(self):
        """
        Calculate Payment day using First Payment Date
        :return:  Payment Day
        """
        if self.first_payment_due:
            first_payment_due = self.first_payment_due
            if not isinstance(first_payment_due, str):
                first_payment_due = str(first_payment_due)
            day = datetime.strptime(first_payment_due, DF).day
            self.payment_day = day

    @api.onchange('down_payment')
    def _onchange_down_payment(self):
        """
        Update is_down_payment flag if there is any downpayment for this loan
        :return: is_down_payment
        """
        if self.down_payment > 0:
            self.is_down_payment = True
        else:
            self.is_down_payment = False

    def _get_total_invoice_amount(self, loan, emi_ids):
        current_month = datetime.today().strftime("%m")
        ins_price = tax_price = 0
        if loan.insurance_product_id:
            ins_price = loan.insurance_sale_price if loan.insurance_sale_price else loan.insurance_product_id.lst_price
        if loan.tax_product_id:
            tax_price = loan.tax_sale_price if loan.tax_sale_price else loan.tax_product_id.lst_price
        for emi in emi_ids:
            if loan.loan_amount != emi.pending_principal_amount:
                if not isinstance(emi.date, str):
                    loan_month = datetime.strptime(str(emi.date), DF).strftime("%m")
                else:
                    loan_month = datetime.strptime(str(emi.date), DF).strftime("%m")
                if current_month == loan_month:
                    if loan.is_leasing:
                        return emi.payment_amount + ins_price + tax_price
                    else:
                        return emi.payment_amount

    # @api.multi
    def get_total_invoice_amount(self):
        """
        Calculate Total Invoice Amount of EMI
        :return: Total invoice amount
        """
        for loan in self:
            total_amount = self._get_total_invoice_amount(loan, loan.line_ids)
            loan.total_invoice_amount = total_amount

    @api.depends('is_leasing', 'bonaire_principal_amount')
    def get_total_insurance_amount(self):
        for rec in self:
            if rec.is_leasing:
                rec.total_insurance_amount = rec.bonaire_principal_amount if rec.bonaire_principal_amount else 0.0
            else:
                rec.total_insurance_amount = 0.0

    @api.depends('is_leasing', 'bonaire_interest_amount')
    def get_total_fire_insurance_amount(self):
        for rec in self:
            if rec.is_leasing:
                rec.total_fire_insurance_amount = rec.bonaire_interest_amount if rec.bonaire_interest_amount else 0.0
            else:
                rec.total_fire_insurance_amount = 0.0

    # @api.multi
    def view_disbursement_entries(self):
        self.ensure_one()
        disbursement_acc_id = self.env['ir.config_parameter'].sudo().get_param('ae_loan_manag.disbursement_acc_id')
        if disbursement_acc_id:
            action = self.env.ref('account.action_account_moves_all_a')
            result = action.read()[0]
            result['domain'] = [('move_id.loan_id', '=', self.id), ('account_id', '=', int(disbursement_acc_id))]
            return result

    def compute_outstanding_bal(self):
        income_acc_id = self.env['ir.config_parameter'].sudo().get_param('ae_loan_manag.income_acc_id')
        move_line_obj = self.env['account.move.line']
        if income_acc_id:
            for loan in self:
                lines = move_line_obj.search([('move_id.loan_id', '=', loan.id),
                                              ('account_id', '=', int(income_acc_id))])
                debit = sum(line.debit for line in lines)
                credit = sum(line.credit for line in lines)
                company_currency = self.env.company.currency_id
                rate = 1
                if loan.currency_id != company_currency:
                    rate_line = self.env['res.currency.rate'].search([('currency_id', '=', loan.currency_id.id)],
                                                                     order='name desc', limit=1)
                    rate = rate_line.company_rate
                loan.outstanding_bal = rate * (debit - credit)

    @api.model
    def default_get(self, fields):
        res = super(AccountLoan, self).default_get(fields)
        loan_jou_id = self.env['ir.config_parameter'].sudo().get_param('ae_loan_manag.loan_jou_id')
        loan_jou = self.env['account.journal'].browse(int(loan_jou_id))
        company = self.env['res.company'].browse(res.get('company_id', ''))

        if company:
            res.update({
                'currency_id': company.currency_id.id or False
            })

        elif loan_jou:
            res.update({
                'currency_id': loan_jou.currency_id.id or \
                               loan_jou.company_id.currency_id.id or False
            })
        else:
            raise UserError(
                _("Please configure 'Loan Journal' from Loans -> Configurations -> Settings! or add currency on company"))
        return res

    # @api.multi
    def cal_ins_tax(self):
        """
        This function returns the insurance and tax balance.
        :return: Insurance and Tax Balance
        """
        invoice_line_obj = self.env['account.move.line']
        for loan in self:
            loan.insurance_balance = 0
            loan.tax_balance = 0

            # for loan in self.search([('is_leasing', '=', True), '|', ('bonaire_principal_prod_id', '!=', False),
            #                          ('bonaire_interest_prod_id', '!=', False)]):
            if loan.is_leasing:
                insurance_product = tax_product = False

                if loan.bonaire_principal_prod_id:
                    insurance_product = loan.bonaire_principal_prod_id
                if loan.bonaire_interest_prod_id:
                    tax_product = loan.bonaire_interest_prod_id

                fam_inv_ins = fam_inv_tax = 0

                domain = [('move_id.loan_id', '=', loan.id), ('move_id.state', '=', 'posted'),
                          ('move_id.move_type', '=', 'out_invoice')]
                if insurance_product and tax_product:
                    domain.append('|', )
                    domain.append(('product_id', '=', insurance_product.id), )
                    domain.append(('product_id', '=', tax_product.id))
                elif tax_product and not insurance_product:
                    domain.append(('product_id', '=', tax_product.id))
                elif insurance_product and not tax_product:
                    domain.append(('product_id', '=', insurance_product.id))

                for invoice_line in invoice_line_obj.search(domain):
                    product_id = invoice_line.product_id.id

                    if insurance_product and product_id == insurance_product.id:
                        fam_inv_ins = fam_inv_ins + invoice_line.paid_amount
                    if tax_product and product_id == tax_product.id:
                        fam_inv_tax = fam_inv_tax + invoice_line.paid_amount
                # Calculate total balance
                loan.insurance_balance = fam_inv_ins
                loan.tax_balance = fam_inv_tax
            else:
                loan.insurance_balance = 0.0
                loan.tax_balance = 0.0

    # @api.multi
    def cal_ins_tax_from_report(self, loan):
        """
        This function returns the insurance and tax balance.
        :return: Insurance and Tax Balance
        """
        invoice_line_obj = self.env['account.move.line']
        insurance_product = tax_product = False
        if loan.insurance_product_id and loan.country_name == 'Curaçao':
            insurance_product = loan.insurance_product_id
        if loan.tax_product_id and loan.country_name == 'Curaçao':
            tax_product = loan.tax_product_id
        if loan.bonaire_principal_prod_id and loan.country_name == 'Bonaire, Sint Eustatius and Saba':
            insurance_product = loan.bonaire_principal_prod_id
        if loan.bonaire_interest_prod_id and loan.country_name == 'Bonaire, Sint Eustatius and Saba':
            tax_product = loan.bonaire_interest_prod_id

        fam_inv_ins = fam_inv_tax = 0

        domain = [('move_id.loan_id', '=', loan.id), ('move_id.state', '=', 'paid')]
        if insurance_product and tax_product:
            domain.append('|', )
            domain.append(('product_id', '=', insurance_product.id), )
            domain.append(('product_id', '=', tax_product.id))
        elif tax_product and not insurance_product:
            domain.append(('product_id', '=', tax_product.id))
        elif insurance_product and not tax_product:
            domain.append(('product_id', '=', insurance_product.id))

        for invoice_line in invoice_line_obj.search(domain):
            product_id = invoice_line.product_id.id

            if insurance_product and product_id == insurance_product.id:
                fam_inv_ins += invoice_line.price_total
            elif tax_product and product_id == tax_product.id:
                fam_inv_tax += invoice_line.price_total

        # Calculate total balance
        return [fam_inv_ins, fam_inv_tax]

    # @api.multi
    def cal_princi_inter_form_report(self, loan):
        """
        This function returns the insurance and tax balance.
        :return: Insurance and Tax Balance
        """
        config_obj = self.env['ir.config_parameter']
        invoice_line_obj = self.env['account.move.line']

        principal_prod_id = config_obj.sudo().get_param('ae_loan_manag.principal_prod_id')
        interest_prod_id = config_obj.sudo().get_param('ae_loan_manag.interest_prod_id')

        total_princi = total_inter = 0

        domain = [('move_id.loan_id', '=', loan.id), ('move_id.state', '=', 'paid')]
        if principal_prod_id and interest_prod_id:
            domain.append('|', )
            domain.append(('product_id', '=', int(principal_prod_id)), )
            domain.append(('product_id', '=', int(interest_prod_id)))
        elif interest_prod_id and not principal_prod_id:
            domain.append(('product_id', '=', int(interest_prod_id)))
        elif principal_prod_id and not interest_prod_id:
            domain.append(('product_id', '=', int(principal_prod_id)))

        for invoice_line in invoice_line_obj.search(domain):
            product_id = invoice_line.product_id.id

            if principal_prod_id and product_id == int(principal_prod_id):
                total_princi += invoice_line.price_total
            elif interest_prod_id and product_id == int(interest_prod_id):
                total_inter += invoice_line.price_total

        # Calculate total balance
        return [total_princi, total_inter]

    def cal_princi_inter(self):
        config_obj = self.env['ir.config_parameter']
        invoice_line_obj = self.env['account.move.line']

        principal_prod_id = config_obj.sudo().get_param('ae_loan_manag.principal_prod_id')
        interest_prod_id = config_obj.sudo().get_param('ae_loan_manag.interest_prod_id')

        for loan in self:
            total_princi = total_inter = 0.0
            total_resi_paid = 0.0
            domain = [('move_id.loan_id', '=', loan.id), ('move_id.state', '=', 'posted'),
                      ('move_id.move_type', '=', 'out_invoice')]
            if principal_prod_id and interest_prod_id:
                domain.append('|', )
                domain.append(('product_id', '=', int(principal_prod_id)), )
                domain.append(('product_id', '=', int(interest_prod_id)))
            elif interest_prod_id and not principal_prod_id:
                domain.append(('product_id', '=', int(interest_prod_id)))
            elif principal_prod_id and not interest_prod_id:
                domain.append(('product_id', '=', int(principal_prod_id)))

            for invoice_line in invoice_line_obj.search(domain):
                product_id = invoice_line.product_id.id

                if principal_prod_id and product_id == int(principal_prod_id):
                    total_princi = total_princi + invoice_line.paid_amount
                    total_resi_paid = total_resi_paid + invoice_line.residual_amount_paid
                    # if invoice_line.partial_paid else total_princi + (
                    # invoice_line.price_total - invoice_line.paid_amount)
                elif interest_prod_id and product_id == int(interest_prod_id):
                    total_inter = total_inter + invoice_line.paid_amount
                    # if invoice_line.partial_paid else total_inter + (
                    # invoice_line.price_total - invoice_line.paid_amount)

            # Calculate total balance
            loan.total_principal_balance = total_princi
            loan.total_interest_balance = total_inter
            loan.total_residual_paid = total_resi_paid

    def _cal_principal_migration(self):
        for rec in self:
            principal_migration_prod = self.env['product.product'].search([('name', '=', 'Principal Migration')])
            if principal_migration_prod:
                invoices = self.env['account.move.line'].search(
                    [('move_id.loan_id', '=', rec.id), ('move_id.state', '=', 'posted'),
                     ('move_id.move_type', '=', 'out_invoice'), ('product_id', '=', principal_migration_prod.id)])
                total_principal_migration = 0.0
                for invoice_line in invoices:
                    total_principal_migration = total_principal_migration + invoice_line.paid_amount
                rec.total_principal_migration = total_principal_migration
            else:
                rec.total_principal_migration = 0.0

    def _compute_paid_penalties(self):
        for rec in self:
            if rec.is_penalty:
                penalty_prod_id = self.env['ir.config_parameter'].sudo().get_param('ae_loan_manag.penalty_prod_id')
                penalty_prod = rec.penalty_product_id if rec.penalty_product_id else self.env['product.product'].browse(
                    int(penalty_prod_id))
                invoices = self.env['account.move.line'].search(
                    [('move_id.loan_id', '=', rec.id), ('move_id.state', '=', 'posted'),
                     ('move_id.move_type', '=', 'out_invoice'), ('product_id', '=', penalty_prod.id)])
                total_paid_penalty = 0.0
                for invoice_line in invoices:
                    total_paid_penalty = total_paid_penalty + invoice_line.paid_amount
                    # if invoice_line.partial_paid else total_paid_penalty + (
                    # invoice_line.price_total - invoice_line.paid_amount)
                rec.total_paid_penalties = total_paid_penalty
            else:
                rec.total_paid_penalties = 0.0

    def _compute_paid_ground_lease(self):
        for rec in self:
            if rec.is_ground_lease:
                ground_lease_prod_id = self.env['ir.config_parameter'].sudo().get_param(
                    'ae_loan_manag.ground_lease_product_id')
                ground_lease_prod = rec.ground_lease_product_id if rec.penalty_product_id else self.env[
                    'product.product'].browse(
                    int(ground_lease_prod_id))
                invoices = self.env['account.move.line'].search(
                    [('move_id.loan_id', '=', rec.id), ('move_id.state', '=', 'posted'),
                     ('move_id.move_type', '=', 'out_invoice'), ('product_id', '=', ground_lease_prod.id)])
                total_paid_ground_lease = 0.0
                for invoice_line in invoices:
                    total_paid_ground_lease = total_paid_ground_lease + invoice_line.paid_amount
                    # if invoice_line.partial_paid else total_paid_penalty + (
                    # invoice_line.price_total - invoice_line.paid_amount)
                rec.total_paid_ground_lease = total_paid_ground_lease
            else:
                rec.total_paid_ground_lease = 0.0

    # @api.multi
    @api.depends('line_ids')
    def _get_expected_end_date(self):
        """
        This method is defined to update expected end date based on last installment due date.
        :return: Expected loan ending date will be updated.
        """
        for record in self:
            if record.line_ids:
                # inv_obj = self.env['account.move']
                # for loan in record:
                #     invoice = inv_obj.search([('loan_id', '=', loan.id),
                #                               ('emi', '=', True)], order='invoice_date_due desc', limit=1)
                #
                #     if invoice:
                #         date = invoice.invoice_date_due
                #         loan.expected_end_date = date
                #         if loan.line_ids:
                #             last_installment = loan.line_ids[-1]
                #             end_date = last_installment.date
                #             if end_date > date:
                #                 loan.expected_end_date = end_date
                #     else:
                #         if loan.line_ids:
                last_installment = record.line_ids[-1]
                if last_installment:
                    record.expected_end_date = last_installment.date
            else:
                expected_end_date = False

    def _compute_invoices(self):
        """
        Computes the total invoices of loan.
        :return: invoice_count
        """
        for loan in self:
            invoice_ids = self.env['account.move'].search(
                [('loan_id', '=', loan.id), ('move_type', '=', 'out_invoice')])
            loan.invoice_count += len(invoice_ids)
            if loan.is_restructure_loan:
                loan.restructuring_invoice_count = len(self.env['account.move'].search(
                    [('loan_id', '=', loan.id), ('move_type', '=', 'entry'), ('is_restructuring_inv', '=', True)]))
            else:
                loan.restructuring_invoice_count = 0
            loan.automatic_transfer_entries_count = len(self.env['account.move'].search(
                [('loan_id', '=', loan.id), ('move_type', '=', 'entry'), ('is_automatic_entry', '=', True)]))

    def _compute_reverse_entries(self):
        """
        Computes the total invoices of loan.
        :return: invoice_count
        """
        for loan in self:
            name = 'Reversal Entry Of' + ' ' + loan.name,
            invoice_ids = self.env['account.move'].search(
                [('loan_id', '=', loan.id), ('move_type', '=', 'entry'), ('ref', '=', name)])
            loan.reverse_entries_count += len(invoice_ids)

    def _compute_transcation_balance(self):
        history_obj = self.env['loan.transaction.history']
        for loan in self:
            pay_transactions = history_obj.search(
                [('loan_id', '=', loan.id), ('description', '=', 'Payment Received'), ('state', '=', 'running')])
            inv_transactions = history_obj.search(
                [('loan_id', '=', loan.id), ('description', '!=', 'Payment Received'), ('state', '=', 'running'),
                 ('date', '<', date.today())])
            debit = sum(inv_trans.debit for inv_trans in inv_transactions)
            credit = sum(pay_trans.credit for pay_trans in pay_transactions)
            loan.transaction_balance = debit - credit

    @api.onchange('product_id')
    def get_loan_amount(self):
        """
        Set default loan amount from product if loan amount is Zero
        :return: Loan Amount
        """
        for loan in self:
            if loan.product_id and loan.loan_amount <= 0:
                loan.loan_amount = loan.product_id.list_price

    @api.depends('rate_period', 'fixed_loan_amount', 'fixed_periods',
                 'currency_id', 'loan_type', 'rate')
    def _compute_fixed_amount(self):
        """
        Computes the fixed amount in order to be used if round_on_end is
        checked. On fix-annuity interests are included and on fixed-principal
        and interests it isn't.
        :return:
        """
        for record in self:
            if record.interest_type == 'simple' and record.loan_type == 'amortizing_loan':
                f_rate = record.fixed_loan_amount * record.rate_period / 100
                f_rate = f_rate * record.fixed_periods
                f_rate = record.fixed_loan_amount + f_rate
                if record.fixed_periods:
                    f_rate = f_rate / record.fixed_periods
                record.fixed_amount = f_rate
            elif record.interest_type in ('simple', 'compound') and record.loan_type == 'interest_loan':
                r_rate = record.rate / 100
                r_rate = r_rate / 12
                record.fixed_amount = r_rate * record.fixed_loan_amount
            elif record.interest_type in (
                    'simple', 'compound') and record.loan_type == 'amortizing_loan' and record.monthly_payment > 0.0:
                record.fixed_amount = record.monthly_payment

            else:
                record.fixed_amount = - record.currency_id.round(npf.pmt(
                    record.rate_period / 100,
                    record.fixed_periods or record.periods,
                    record.fixed_loan_amount,
                    -record.residual_amount
                ))

    @api.depends('rate', 'method_period')
    def _compute_rate_period(self):
        """
        Calculate rate period based on period method and rate.
        :return:
        """
        for record in self:
            record.rate_period = self.rate / 12 * self.method_period

    @api.onchange('is_leasing')
    def _onchange_is_leasing(self):
        self.residual_amount = 0.0

    @api.onchange('company_id')
    def _onchange_company(self):
        self._onchange_is_leasing()

    @api.model
    def create(self, vals_list):
        if isinstance(vals_list, dict):
            vals_list = [vals_list]

        config_obj = self.env['ir.config_parameter']
        sequence_obj = self.env['ir.sequence']

        principal_prod_id = config_obj.sudo().get_param('ae_loan_manag.principal_prod_id')
        interest_prod_id = config_obj.sudo().get_param('ae_loan_manag.interest_prod_id')

        loan_jou_id = config_obj.sudo().get_param('ae_loan_manag.loan_jou_id')
        loan_jou = self.env['account.journal'].browse(int(loan_jou_id))

        if not principal_prod_id or not interest_prod_id:
            raise UserError(
                _('Please configure Principal and Interest product from Loan -> Configurations -> Settings!'))

        if not loan_jou:
            raise UserError(_('Please configure Loan Journal from Loan -> Configurations -> Settings!'))

        for vals in vals_list:
            company = self.env['res.company'].browse(vals.get('company_id', ''))

            if vals.get('name', 'New') == 'New':
                vals['name'] = sequence_obj.next_by_code('account.loan') or 'New'

        res = super(AccountLoan, self).create(vals_list)

        return res

    def write(self, vals):
        old_ids = self.loan_collateral_ids.ids
        for rec in self:
            new_ids = False
            if vals.get('loan_collateral_ids'):
                new_ids = vals.get('loan_collateral_ids')[0][2]
                if new_ids != old_ids:
                    new_tags = str(self.env['loan.collateral'].browse(new_ids).mapped('collateral_type')).replace('[',
                                                                                                                  '').replace(
                        ']',
                        '').replace(
                        "'", "")
                    old_tags = str(self.env['loan.collateral'].browse(old_ids).mapped('collateral_type')).replace('[',
                                                                                                                  '').replace(
                        ']',
                        '').replace(
                        "'", "")
                    new_description = str(self.env['loan.collateral'].browse(new_ids).mapped('any_info')).replace('[',
                                                                                                                  '').replace(
                        ']',
                        '').replace(
                        "'", "")
                    old_description = str(self.env['loan.collateral'].browse(old_ids).mapped('any_info')).replace('[',
                                                                                                                  '').replace(
                        ']',
                        '').replace(
                        "'", "")
                    self.message_post(
                        body="<b>OLD Collaterals:</b> %s <i class='fa fa-long-arrow-right mx-1 text-600' title='Changed' role='img' aria-label='Changed'></i> %s <br> <b>NEW Collaterals:</b> %s <i class='fa fa-long-arrow-right mx-1 text-600' title='Changed' role='img' aria-label='Changed'></i> %s" % (
                            old_tags, old_description, new_tags, new_description))
            if rec.type == 'laf' and rec.laf_state == 'review_edit' and not vals.get('laf_state', '') == 'review_edit':
                vals['review_edit_text'] = rec.review_edit_text + ' ' + ','.join(
                    list(vals)) if rec.review_edit_text else ','.join(list(vals))
            if vals.get('loan_collateral_ids') and vals.get('loan_collateral_ids')[0][2]:
                for collateral in vals.get('loan_collateral_ids')[0][2]:
                    col_obj = self.env['loan.collateral'].search([('id', '=', collateral)])
                    if col_obj:
                        col_obj.write({'loan_id': rec.id})
            if vals.get('loan_collateral_ids') and vals.get('loan_collateral_ids')[0] == [6, False, []]:
                for collateral in old_ids:
                    col_obj = self.env['loan.collateral'].search([('id', '=', collateral)])
                    if col_obj and col_obj.loan_id:
                        col_obj.write({'loan_id': False})
            if old_ids and new_ids:
                different_values = [
                    value for value in old_ids + new_ids
                    if (value in old_ids and value not in new_ids) or (value in new_ids and value not in old_ids)
                ]
                if old_ids and different_values and len(vals.get('loan_collateral_ids')[0][2]) < len(old_ids):
                    for collateral in different_values:
                        col_obj = self.env['loan.collateral'].search([('id', '=', collateral)])
                        if col_obj:
                            col_obj.write({'loan_id': False})


            if vals and not vals.get('laf_state', None) == 'cam_approve' and not vals.get('period_or_monthly', None) and rec.type == 'laf' and rec.laf_state == 'review_edit' and rec.env.user.has_group('smart_loan_system.group_loan_cao') and not rec.is_cao_edit:
                vals.update({'is_cao_edit': True})

            return super(AccountLoan, rec).write(vals)

    def post(self):
        self.ensure_one()
        if not self.start_date:
            self.start_date = fields.Datetime.now()
        if not self.first_payment_due:
            self.first_payment_due = fields.Datetime.now()
        if not self.is_down_payment and self.down_payment != 0:
            self.compute_draft_lines()
            self.write({'state': 'posted'})
        else:
            self.write({'state': 'posted'})

    # @api.multi
    def close(self):
        self.close_date = date.today()
        self.write({'state': 'closed'})

    # @api.multi
    def compute_lines(self):
        print("Inside compute lines =-=-===============================")
        self.ensure_one()
        if self.state == 'draft':
            return self.compute_draft_lines()
        return self.compute_posted_lines()

    def reset_loan_calculations(self):
        for rec in self:
            if rec.state == 'posted':
                rec.line_ids.filtered(lambda l: not l.invoice_ids).unlink()
            else:
                rec.line_ids = [(5, 0, 0)]
            rec.periods = 0
            rec.monthly_payment = 0.0

    def compute_posted_lines(self):
        """
        Recompute the amounts of not finished lines. Useful if rate is changed
        """
        print("Inside compute posted lines =-=-===============================")
        amount = self.loan_amount
        next_line = False
        previous_line = False
        if next((line for line in self.line_ids if not line.invoice_ids), None):
            next_line = next((line for line in self.line_ids if not line.invoice_ids), None)
        else:
            previous_line = max(self.line_ids.filtered(lambda line: line.invoice_ids), key=lambda line: line.sequence,
                                default=None)
        if next_line:
            amount = next_line.pending_principal_amount
        elif previous_line:
            amount = previous_line.pending_principal_amount - previous_line.principal_amount

        if next_line:
            if not isinstance(next_line.date, str):
                date = datetime.strptime(str(next_line.date),
                                         DF).date()
            else:
                date = datetime.strptime(next_line.date,
                                         DF).date()
        elif previous_line:
            date = previous_line.date + relativedelta(months=1)
        else:
            date = datetime.today().date()
        delta = relativedelta(months=self.method_period)

        if self.line_ids.filtered(lambda l: not l.invoice_ids):
            self.line_ids.filtered(lambda l: not l.invoice_ids).unlink()
        if self.periods > 0:
            for i in range(len(self.line_ids.filtered(lambda l: l.invoice_ids)) + 1, self.periods + 1):
                is_last_payment = False
                if i == self.periods:
                    is_last_payment = True
                line = self.env['account.loan.line'].create(
                    self.new_line_vals(i, date, amount, is_last_payment)
                )
                line.check_amount()
                date += delta
                if date.day in range(1, (calendar.monthrange(date.year, date.month)[1])):
                    date = date.replace(day=self.first_payment_due.day)

                amount -= line.payment_amount - line.interests_amount
        elif self.loan_type == 'amortizing_loan' and self.monthly_payment > 0.0 and amount > 0.0:
            self.periods = len(self.line_ids.filtered(lambda l: l.invoice_ids))
            while amount >= 0.0:
                threshold = max(1e-9 * amount, 1e-12)
                self.periods = self.periods + 1
                is_last_payment = False
                if amount < self.monthly_payment:
                    is_last_payment = True
                line = self.env['account.loan.line'].create(
                    self.new_line_vals(self.periods, date, amount, is_last_payment)
                )
                line.check_amount()
                date += delta
                if date.day in range(1, (calendar.monthrange(date.year, date.month)[1])):
                    date = date.replace(day=self.first_payment_due.day)
                if line.payment_amount < line.interests_amount:
                    amount = amount - line.interests_amount
                else:
                    amount = amount - (line.payment_amount - line.interests_amount)
                if amount < threshold:
                    break

    def new_line_vals(self, sequence, date, amount, is_last_payment):
        return {
            'loan_id': self.id,
            'sequence': sequence,
            'date': date,
            'pending_principal_amount': amount,
            'emi': True,
            'is_last_payment': is_last_payment
        }

    # @api.multi
    def compute_draft_lines(self):
        print("Compute drft lines =-=-===========")
        self.ensure_one()
        self.fixed_periods = self.periods
        self.fixed_loan_amount = self.loan_amount
        amount = self.loan_amount
        restricted_rate = self.rate / 100 / 360 * self.loan_amount * (
            (self.first_payment_due - self.start_date).days)
        if self.monthly_payment and restricted_rate >= self.monthly_payment:
            raise UserError(
                _('You are not allowed to keep monthly payment with the amount of %s, since the interest amount is more than %s',
                  '{:.2f}'.format(self.monthly_payment), '{:.2f}'.format(restricted_rate)))

        else:
            if self.is_down_payment and self.state == 'posted':
                amount -= self.down_payment
                self.fixed_loan_amount = self.loan_amount - self.down_payment
            if self.first_payment_due:
                if not isinstance(self.first_payment_due, str):
                    date = datetime.strptime(str(self.first_payment_due), DF).date()
                else:
                    date = datetime.strptime(self.first_payment_due, DF).date()
            else:
                date = datetime.today().date()
            delta = relativedelta(months=self.method_period)
            if not self.payment_on_first_period:
                date += delta

            if self.line_ids:
                self._cr.execute("delete from account_loan_line WHERE loan_id=%s", (self.id,))
            inv_lines = self.env['account.move'].search(
                [('is_down_payment', '=', True), ('loan_id', '=', self.id), ('move_type', '=', 'out_invoice',)])
            print("Inv lines -=-=-=", inv_lines)
            if inv_lines:
                print("dfssgfgfd======")
                pass
            elif self.periods > 0:
                print("inside else =-=-=-")
                for i in range(1, self.periods + 1):
                    is_last_payment = False
                    if i == self.periods:
                        is_last_payment = True
                    line = self.env['account.loan.line'].create(
                        self.new_line_vals(i, date, amount, is_last_payment)
                    )
                    line.check_amount()
                    date += delta
                    if date.day in range(1, (calendar.monthrange(date.year, date.month)[1])):
                        date = date.replace(day=self.first_payment_due.day)

                    amount -= line.payment_amount - line.interests_amount
            elif self.loan_type == 'amortizing_loan' and self.monthly_payment > 0.0 and amount > 0.0:
                while amount >= 0.0:
                    threshold = max(1e-9 * amount, 1e-12)
                    self.periods = self.periods + 1

                    is_last_payment = False
                    if amount < self.monthly_payment:
                        is_last_payment = True
                    line = self.env['account.loan.line'].create(
                        self.new_line_vals(self.periods, date, amount, is_last_payment)
                    )
                    print(amount)
                    line.check_amount()
                    date += delta
                    if date.day in range(1, (calendar.monthrange(date.year, date.month)[1])):
                        date = date.replace(day=self.first_payment_due.day)

                    if line.payment_amount < line.interests_amount:
                        amount = amount - line.interests_amount
                    else:
                        amount = amount - (line.payment_amount - line.interests_amount)
                    if amount < threshold:
                        break

    def view_insurance_balance(self):
        """
        This method is called from Insurance widget to display all invoice line of Insurance Product for loan
        :return:  Invoice line tree view
        """
        self.ensure_one()
        if self.insurance_product_id:
            action = self.env.ref('smart_loan_system.loan_invoice_line_action')
            result = action.read()[0]
            result['domain'] = [('product_id', '=', self.bonaire_principal_prod_id.id),
                                ('move_id.loan_id', '=', self.id), ('move_id.state', '=', 'posted'),
                                ('move_id.move_type', '=', 'out_invoice')]
            return result

    def view_paid_penalties(self):
        for rec in self:
            penalty_prod_id = self.env['ir.config_parameter'].sudo().get_param('ae_loan_manag.penalty_prod_id')
            penalty_prod = rec.penalty_product_id if rec.penalty_product_id else self.env['product.product'].browse(
                int(penalty_prod_id))
            if penalty_prod:
                action = self.env.ref('smart_loan_system.loan_invoice_line_action')
                result = action.read()[0]
                result['domain'] = [('product_id', '=', penalty_prod.id),
                                    ('move_id.loan_id', '=', self.id), ('move_id.state', '=', 'posted'),
                                    ('move_id.move_type', '=', 'out_invoice')]
                return result

    def view_paid_ground_lease(self):
        for rec in self:
            ground_lease_prod_id = self.env['ir.config_parameter'].sudo().get_param(
                'ae_loan_manag.ground_lease_product_id')
            ground_lease_prod = rec.ground_lease_product_id if rec.ground_lease_product_id else self.env[
                'product.product'].browse(
                int(ground_lease_prod_id))
            if ground_lease_prod:
                action = self.env.ref('smart_loan_system.loan_invoice_line_action')
                result = action.read()[0]
                result['domain'] = [('product_id', '=', ground_lease_prod.id),
                                    ('move_id.loan_id', '=', self.id), ('move_id.state', '=', 'posted'),
                                    ('move_id.move_type', '=', 'out_invoice')]
                return result

    def view_tax_balance(self):
        """
        This method is called from Tax widget to display all invoice line of Tax Product for loan
        :return:  Invoice line tree view
        """
        self.ensure_one()
        if self.tax_product_id:
            action = self.env.ref('smart_loan_system.loan_invoice_line_action')
            result = action.read()[0]
            result['domain'] = [('product_id', '=', self.bonaire_interest_prod_id.id),
                                ('move_id.loan_id', '=', self.id), ('move_id.state', '=', 'posted'),
                                ('move_id.move_type', '=', 'out_invoice')]
            return result

    # @api.multi
    def view_principal_balance(self):
        """
        This method is called from Pricipal widget to display all invoice line of Pricipal Product for loan
        :return: Invoice line tree view
        """
        self.ensure_one()
        config_obj = self.env['ir.config_parameter']

        principal_prod_id = config_obj.sudo().get_param('ae_loan_manag.principal_prod_id')

        domain = [('move_id.loan_id', '=', self.id), ('product_id', '=', int(principal_prod_id)),
                  ('move_id.state', '=', 'posted'), ('move_id.move_type', '=', 'out_invoice')]

        invoice_lines = self.env['account.move.line'].search(domain).ids
        action = self.env.ref('smart_loan_system.loan_invoice_line_action')
        result = action.read()[0]
        result['domain'] = [('id', 'in', invoice_lines)]
        return result

    def view_interest_balance(self):
        """
        This method is called from Interest widget to display all invoice line of Interest Product for loan
        :return: Invoice line tree view
        """
        self.ensure_one()
        config_obj = self.env['ir.config_parameter']

        interest_prod_id = config_obj.sudo().get_param('ae_loan_manag.interest_prod_id')

        domain = [('move_id.loan_id', '=', self.id), ('product_id', '=', int(interest_prod_id)),
                  ('move_id.state', '=', 'posted'), ('move_id.move_type', '=', 'out_invoice')]

        invoice_lines = self.env['account.move.line'].search(domain).ids
        action = self.env.ref('smart_loan_system.loan_invoice_line_action')
        result = action.read()[0]
        result['domain'] = [('id', 'in', invoice_lines)]
        return result

    def view_principal_migration(self):
        self.ensure_one()
        migration_prod_id = self.env['product.product'].search([('name', '=', 'Principal Migration')])

        domain = [('move_id.loan_id', '=', self.id), ('product_id', '=', int(migration_prod_id)),
                  ('move_id.state', '=', 'posted'), ('move_id.move_type', '=', 'out_invoice')]

        invoice_lines = self.env['account.move.line'].search(domain).ids
        action = self.env.ref('smart_loan_system.loan_invoice_line_action')
        result = action.read()[0]
        result['domain'] = [('id', 'in', invoice_lines)]
        return result

    # @api.multi
    def view_loan_transactions(self):
        """
        This method id called from Transaction widget to display all the transactions
        :return: Transaction tree view
        """
        self.ensure_one()
        transactions = self.env['loan.transaction.history'].search(
            [('loan_id', '=', self.id), ('state', '=', 'running')]).ids
        action = self.env.ref('smart_loan_system.action_loan_transaction')
        result = action.read()[0]
        result['domain'] = [('id', 'in', transactions), ('state', '=', 'running')]
        return result

    # @api.multi
    def view_account_invoices(self):
        """
        This method is called from Invoices widget to display all the invoice related to loan
        :return: Invoices tree view
        """
        self.ensure_one()
        action = self.env.ref('account.action_move_out_invoice_type')
        result = action.read()[0]
        result['domain'] = [
            ('loan_id', '=', self.id), ('move_type', '=', 'out_invoice')
        ]
        return result

    def view_reverse_entries(self):
        """
        This method is called from Invoices widget to display all the invoice related to loan
        :return: Invoices tree view
        """
        self.ensure_one()
        action = self.env.ref('account.action_move_out_invoice_type')
        result = action.read()[0]
        name = 'Reversal Entry Of' + ' ' + self.name
        result['domain'] = [
            ('loan_id', '=', self.id), ('move_type', '=', 'entry'), ('ref', '=', name)
        ]
        return result

    # @api.multi
    def view_payments(self):
        """
        This method is called from Payment widget to diplay all the payment history of loan
        :return: Payment History tree view
        """
        self.ensure_one()
        action = self.env.ref('smart_loan_system.view_payments')
        result = action.read()[0]
        return result

    def _get_loan_invoices(self, loan):
        loan_invoices = self.env['account.move'].search([('loan_id', '=', loan.id), ('splitted_invoice', '=', False),
                                                         ('state', 'not in', ('draft', 'cancel'))],
                                                        order='invoice_date_due')
        if loan_invoices:
            return loan_invoices
        else:
            return []

    def get_code_with_zeros(self, code, sequence):
        padding = sequence.padding
        missing_len = padding - len(code)
        prepare_zeros = ''
        for x in range(0, missing_len):
            prepare_zeros += '0'
        return prepare_zeros + code

    def _get_month_or_year(self, month=None, year=None, date=None):
        date_format_string = ["%m", "%y", "%Y"]
        if month in date_format_string:
            month = datetime.strftime(datetime.strptime(str(date), '%Y-%m-%d'), month)
        else:
            month = ""
        if year in date_format_string:
            year = datetime.strftime(datetime.strptime(str(date), '%Y-%m-%d'), year)
        else:
            year = ""
        return month, year

    def _get_period_info(self, sequence, date_invoice):
        if sequence.prefix:
            if '%(y)s/%(range_month)s' == sequence.prefix:
                month, year = self._get_month_or_year(month="%m", year="%y", date=date_invoice)
                prepared_range = year + '/' + month
                return prepared_range
            elif '%(range_year)s' == sequence.prefix:
                month, year = self._get_month_or_year(month=None, year="%y", date=date_invoice)
                prepared_range = year
                return prepared_range
            elif '%(range_month)s' == sequence.prefix:
                month, year = self._get_month_or_year(month="%m", year=None, date=date_invoice)
                prepared_range = month
                return prepared_range
            elif '%(year)s' == sequence.prefix:
                month, year = self._get_month_or_year(month=None, year="%Y", date=date_invoice)
                prepared_range = year
                return prepared_range
            elif '%(range_month)s/%(y)s' == sequence.prefix:
                month, year = self._get_month_or_year(month="%m", year="%y", date=date_invoice)
                prepared_range = month + '/' + year
                return prepared_range
            elif '%(year)s/%(range_month)s' == sequence.prefix:
                month, year = self._get_month_or_year(month="%m", year="%Y", date=date_invoice)
                prepared_range = year + '/' + month
                return prepared_range
            elif '%(y)s' == sequence.prefix:
                month, year = self._get_month_or_year(month=None, year="%y", date=date_invoice)
                prepared_range = year
                return prepared_range
            elif '%(range_y)s' == sequence.prefix:
                month, year = self._get_month_or_year(month=None, year="%y", date=date_invoice)
                prepared_range = year
                return prepared_range
            elif '%(range_year)s' == sequence.prefix:
                month, year = self._get_month_or_year(month=None, year="%Y", date=date_invoice)
                prepared_range = year
                return prepared_range
            else:
                return ''

    # @api.multi
    def reset_old_loan_invoices_sequence(self):
        """
        Remove old invoice history and reset old loan invoices.
        :return:
        """
        loan_inv_obj = self.env['loan.invoice']
        inv_obj = self.env['account.move']
        loan_tran_his_obj = self.env['loan.transaction.history']
        for loan in self:
            if loan.state == 'posted':
                # Removing old invoice history
                loan.loan_inv_ids = [(5, 0, 0)]
                if not loan.loan_inv_ids:
                    invoice_ids = loan.processing_fee_inv_id
                    invoice_ids += self._get_loan_invoices(loan)
                    print("invoice ids-=-=", invoice_ids)
                    # assiging temp number to existin invoice to avoid duplicate error!
                    temp = 1
                    for inv in invoice_ids:
                        inv.move_id.name = chr(temp)
                        temp += 1
                    for inv in invoice_ids:
                        # new_number = inv.journal_id.code or ''
                        # new_number += '/'
                        new_number = loan.name
                        new_number += '/'
                        # prepareing period data for sequence
                        period_data = self._get_period_info(inv.journal_id.sequence_id, inv.invoice_date)
                        if period_data:
                            new_number += period_data

                        year = datetime.strptime(str(inv.invoice_date), DEFAULT_SERVER_DATE_FORMAT).year
                        month = datetime.strptime(str(inv.invoice_date), DEFAULT_SERVER_DATE_FORMAT).month
                        last_invoice = self.env['loan.invoice'].search([('year', '=', year),
                                                                        ('loan_id', '=', loan.id),
                                                                        ('move_id', '!=', inv.id)],
                                                                       )
                        print("Laast invoice =-=", last_invoice)
                        if last_invoice:
                            exist_invoice = len(last_invoice)
                            sequence = exist_invoice + 1
                        else:
                            sequence = 1
                        new_number += '/'
                        number = self.get_code_with_zeros(str(sequence), inv.journal_id.sequence_id)
                        new_number += str(number)
                        inv.move_id.name = new_number

                        histories = loan_tran_his_obj.search([('move_id', '=', inv.id), ('state', '=', 'running')])
                        for his in histories:
                            his.reference = inv.number

                        # creating reference for sequence under loan
                        loan_inv_obj.create({
                            'name': new_number,
                            'loan_id': loan.id,
                            'move_id': inv.id,
                            'month': month,
                            'year': year,
                            'date_invoice': inv.invoice_date,
                            'sequence_number': sequence,
                        })
                    splitted_invs = inv_obj.search([('loan_id', '=', loan.id), ('splitted_invoice', '=', True)])
                    for splitted_inv in splitted_invs:
                        if splitted_inv.loan_line_id:
                            main_inv = splitted_inv.move_id if \
                                splitted_inv.main_invoice_id else False
                            if main_inv and main_inv.number:
                                splitted_inv.number = main_inv.number + 'A'
                                main_loan_inv = loan_inv_obj.search([('move_id', '=', main_inv.id)], limit=1)
                                year = datetime.strptime(str(splitted_inv.invoice_date),
                                                         DEFAULT_SERVER_DATE_FORMAT).year
                                month = datetime.strptime(str(splitted_inv.invoice_date),
                                                          DEFAULT_SERVER_DATE_FORMAT).month
                                loan_inv_obj.create({
                                    'name': splitted_inv.number,
                                    'loan_id': loan.id,
                                    'move_id': splitted_inv.id,
                                    'month': month,
                                    'year': year,
                                    'date_invoice': splitted_inv.invoice_date,
                                    'sequence_number': main_loan_inv.sequence_number,
                                })

    # @api.multi
    def generate_old_loan_invoices(self):
        """
        Generate invoices of all old EMIs.
        :return:
        """
        active_ids = self._context.get('active_ids')
        loans = self.env['account.loan'].browse(active_ids)
        date_now = datetime.now()
        for loan in loans:
            if loan.state == 'posted':
                for line in loan.line_ids:
                    if line.date and line.has_invoices == False:
                        inv_date = date_now + timedelta(days=12)
                        if datetime.strptime(str(line.date),
                                             DF) <= inv_date and line.payment_amount != loan.down_payment:
                            line.view_process_values()

    def compute_lines_existing_loans(self):
        active_ids = self._context.get('active_ids')
        loans = self.env['account.loan'].browse(active_ids)
        for loan in loans:
            if loan.state == 'draft':
                loan.compute_lines()

    def reset_accruals_existing_loans(self):
        active_ids = self._context.get('active_ids')
        loans = self.env['account.loan'].browse(active_ids)
        for loan in loans:
            loan.reset_loan_accruals()

    def send_interest_letter_report(self):
        active_ids = self._context.get('active_ids')
        loans = self.env['account.loan'].browse(active_ids)
        loan_list = []
        for loan in loans:
            loan_list.append(loan.id)
        return {
            'name': _('Loan Delinquent Wizard'),
            'res_model': 'loan.delinquent.wizard',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_loan_ids': loan_list
            },
        }

    def validate_existing_loans(self):
        active_ids = self._context.get('active_ids')
        loans = self.env['account.loan'].browse(active_ids)
        for loan in loans:
            if loan.state == 'draft':
                loan.post_loan()

    def _check_is_invoice_open(self, invoice_ids):
        is_open = False
        for invoice in invoice_ids:
            if invoice.state in ('draft', 'open'):
                return True

        return is_open

    @api.model
    def create_invoice(self):
        """
        This method is called from scheduler to create automatic invoice.
        :return: Create automatic invoice
        """
        curacao_tz = pytz.timezone('America/Curacao')
        utc_now = datetime.now(pytz.utc)
        curacao_now = utc_now.astimezone(curacao_tz)
        today_date = curacao_now.date()
        future_date = today_date + relativedelta(days=10)
        error_messages = []
        loans = self.env['account.loan'].search([('state', '=', 'posted')])
        creation_data = []
        for loan in loans:
            try:
                all_created_moves = []
                due_lines = loan.line_ids.filtered(lambda l: l.date == future_date and not l.has_invoices)
                for line in due_lines:
                    line.view_process_values()

                    if line.invoice_ids:
                        all_created_moves.append(line.invoice_ids[0])
                creation_data.append({
                    'loan_name': loan.name,
                    'new_invoice_name': [move.name for move in all_created_moves],
                })
            except (Exception, OperationalError, InterfaceError, psycopg2.Error, UserError) as e:
                if 'cursor already closed' in str(e):
                    self.env.cr.reset()
                    time.sleep(5)
                    self.env.cr.rollback()
                else:
                    error_message = f"Error in 'Loan Auto Invoice Generation' for Loan {loan.name}: {str(e)}"
                    _logger.error(error_message)
                    error_messages.append(error_message)
                    time.sleep(5)
                    self.env.cr.rollback()
                continue

        if error_messages:
            failure_record = self.env['failure.history'].create({
                'name': 'Loan Robots-->Loan Auto Invoice Generation',
                'error': str(error_messages),
            })
            _logger.info(f"Failure history record created: {failure_record}")
            admins = self.env['res.groups'].search(
                [('category_id', '=', 'Administration'),
                 ('name', '=', 'Access Rights')]).users
            mail_template = self.env.ref(
                'cron_failure_notification.mail_template_cron_error')
            for admin in admins:
                email_values = {'admin_mail': admin.login}
                mail_template.with_context(email_values).send_mail(self.id,
                                                                   force_send=True)


        if creation_data:
            output = BytesIO()
            workbook = xlsxwriter.Workbook(output, {'in_memory': True})
            worksheet = workbook.add_worksheet()

            worksheet.set_column('A:A', 30)
            worksheet.set_column('B:B', 35)

            headers = ['Loan Name', 'Invoice Created Name']
            for col_num, header in enumerate(headers):
                worksheet.write(0, col_num, header)

            # Write data rows
            for row_num, data in enumerate(creation_data, 1):
                worksheet.write(row_num, 0, data['loan_name'])
                worksheet.write(row_num, 1,
                                ', '.join(data['new_invoice_name']) or 'N/A')

            workbook.close()

            # Save XLSX to binary field
            output.seek(0)
            xlsx_data = base64.b64encode(output.read())
            file_name = f'Loan_Auto_Invoice_Generation_Report{today_date}.xlsx'

            # Create an attachment in Odoo
            attachment = self.env['ir.attachment'].create({
                'name': file_name,
                'type': 'binary',
                'datas': xlsx_data,
                'store_fname': file_name,
                'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            })

            folder_id = self.env['documents.folder'].search([('name', '=', 'Loan Auto Invoice Generation Reports')], limit=1)
            if not folder_id:
                folder_id = self.env['documents.folder'].create({'name': 'Loan Auto Invoice Generation Reports'})

            document_defaults = {'folder_id': folder_id.id}
            document = self.env['documents.document'].create(
                {'attachment_id': attachment.id, **document_defaults})

    @api.model
    def action_generate_xlsx_auto(self):
        today_date = fields.Date.today()
        report = self.env.ref('smart_loan_system.account_loan_report').sudo()
        ir_actions_report_sudo = self.env['ir.actions.report'].sudo()
        account_loan = self.env['account.loan'].search([('state', '=', 'posted')])

        max_retries = 3
        retry_count = 0

        while retry_count < max_retries:
            try:
                with self.env.cr.savepoint():
                    _logger.info("Generating report...")
                    generated_report = ir_actions_report_sudo._render_xlsx(report, docids=account_loan.ids, data=None)

                    if not generated_report or not generated_report[0]:
                        raise UserError(_("Failed to generate the report."))

                    data_record = base64.b64encode(generated_report[0])

                    ir_values = {
                        'name': 'EOD Report ' + str(today_date),
                        'type': 'binary',
                        'datas': data_record,
                        'mimetype': 'application/vnd.ms-excel',
                    }
                    attachment = self.env['ir.attachment'].sudo().create(ir_values)

                    folder_id = self.env['documents.folder'].search([('name', '=', 'Smart Loan')], limit=1)
                    if not folder_id:
                        folder_id = self.env['documents.folder'].create({'name': 'Smart Loan'})

                    document_defaults = {'folder_id': folder_id.id}
                    document = self.env['documents.document'].create(
                        {'attachment_id': attachment.id, **document_defaults})

                    _logger.info("Successfully generated and saved report.")
                    break
            except (Exception, OperationalError, InterfaceError, psycopg2.Error, UserError) as e:
                retry_count += 1
                _logger.error(f"Error in 'Loan Auto Xlsx Generation': {str(e)}")
                time.sleep(5)
                _logger.info(f"Retrying report generation after error... (attempt {retry_count}/{max_retries})")
        else:
            _logger.error("Failed to generate report after {} retries.".format(max_retries))


    # @api.multi
    def close_loan(self):
        """
        Don't allow to delete loan if there is any partial or fully paid invoice of EMI, Otherwise cancel the all
        draft and open invoices and add the 'C' at the end of the Loan name.
        :return:
        """
        self.ensure_one()
        for loan_line in self.line_ids:
            for invoice in loan_line.invoice_ids:
                if invoice.state == 'paid':
                    raise UserError(_("Some payments are already registered. You need to cancel them."))

        # Cancel the draft and open invoices
        for loan_line in self.line_ids:
            for invoice in loan_line.invoice_ids:
                if (invoice.state == 'draft' or invoice.state == 'open'):
                    invoice.action_cancel()
        self.write({'state': 'closed'})
        # Rename Loan with loan name + C
        self.name = self.name + 'C'

    # @api.multi
    def cancel_loan(self):
        """
        Cancel all open and draft invoices and mark partial paid invoices as fully paid.
        :return:
        """
        self.ensure_one()
        config_param = self.env['ir.config_parameter'].sudo()
        account_obj = self.env['account.account']
        write_off_account_id = config_param.get_param('ae_loan_manag.write_off_account_id')
        if not write_off_account_id:
            raise UserError(_("Please configure 'Write off Account' from Loan -> "
                              "Configurations -> Settings!"))
        write_off_acc = account_obj.browse(int(write_off_account_id))

        disbursement_account_id = config_param.get_param('ae_loan_manag.disbursement_acc_id')
        if not disbursement_account_id:
            raise UserError(_("Please configure 'Disbursement Account' from Loan -> "
                              "Configurations -> Settings!"))
        disbursement_acc = account_obj.browse(int(disbursement_account_id))

        loan_income_account_id = config_param.get_param('ae_loan_manag.income_acc_id')
        if not loan_income_account_id:
            raise UserError(_("Please configure 'Loan Income Account' from Loan -> "
                              "Configurations -> Settings!"))
        loan_income_acc = account_obj.browse(int(loan_income_account_id))

        loan_receivable_account_id = config_param.get_param('ae_loan_manag.acc_rec_id')
        if not loan_receivable_account_id:
            raise UserError(_("Please configure 'Loan Receivable Account' from Loan -> "
                              "Configurations -> Settings!"))
        loan_receivable_acc = account_obj.browse(int(loan_receivable_account_id))

        loan_jou_id = config_param.sudo().get_param('ae_loan_manag.loan_jou_id')
        if not loan_jou_id:
            raise UserError(_("Please Configure Loan Journal from Loans -> Configurations -> Settings!"))
        loan_jou = self.env['account.journal'].browse(int(loan_jou_id))

        if not loan_jou.default_account_id:
            raise UserError(_("Please Configure Default Credit Account for 'Loan Journal'!"))

        company_currency = self.env.company.currency_id
        rate = 1.0
        if self.currency_id != company_currency:
            rate_line = self.env['res.currency.rate'].search(
                [('currency_id', '=', self.currency_id.id)],
                order='name desc', limit=1)
            rate = rate_line.inverse_company_rate

        date = fields.Date.today()
        move = self.env['account.move'].create({
            'journal_id': loan_jou and loan_jou.id or False,
            'loan_id': self.id or False,
            'ref': 'Write-Off' + ' ' + self.name,
            'date': date,
            'move_type': 'entry',
            'currency_id': self.currency_id.id if self.currency_id else (
                self.company_id.currency_id.id if self.company_id.currency_id else False),
            'partner_id': self.partner_id.id or False
        })
        lines = [{
            'account_id': disbursement_acc.id,
            'partner_id': self.partner_id.id or False,
            'amount_currency': -1 * self.outstanding_bal,
            'name': self.name,
            'date': date,
            'ref': 'Disbursement Entry',
            'currency_id': self.currency_id.id if self.currency_id else (
                self.company_id.currency_id.id if self.company_id.currency_id else False),
        }, {
            'account_id': write_off_acc.id or False,
            'partner_id': self.partner_id.id or False,
            'amount_currency': self.outstanding_bal,
            'name': self.name,
            'date': date,
            'ref': 'Write Off Entry',
            'currency_id': self.currency_id.id if self.currency_id else (
                self.company_id.currency_id.id if self.company_id.currency_id else False),
        }]
        move.line_ids = [(0, 0, val) for val in lines]
        move.post()

        receivable_account = self.env['account.account'].search([('name', '=', 'Account Receivable')])
        unpaid_invoice_lines = self.env['account.move.line'].search(
            [('move_id.loan_id', '=', self.id), ('unpaid_amount', '>', 0.0)])

        for line in unpaid_invoice_lines:
            move = self.env['account.move'].create({
                'journal_id': loan_jou and loan_jou.id or False,
                'loan_id': self.id or False,
                'ref': 'Reversal Entry Of' + ' ' + self.name,
                'date': date,
                'move_type': 'entry',
                'currency_id': self.currency_id.id if self.currency_id else (
                    self.company_id.currency_id.id if self.company_id.currency_id else False),
                'partner_id': self.partner_id.id or False
            })
            lines = [{
                'account_id': loan_receivable_acc.id if loan_receivable_acc else receivable_account.id,
                'partner_id': self.partner_id.id or False,
                'debit': 0,
                'credit': rate * line.unpaid_amount,
                'amount_currency': -1 * line.unpaid_amount,
                'name': self.name,
                'date': date,
                'ref': 'Reversal Entry',
                'currency_id': self.currency_id.id if self.currency_id else (
                    self.company_id.currency_id.id if self.company_id.currency_id else False),
            }, {
                'account_id': line.account_id.id or False,
                'partner_id': self.partner_id.id or False,
                'debit': rate * line.unpaid_amount,
                'credit': 0,
                'amount_currency': line.unpaid_amount,
                'name': self.name,
                'date': date,
                'ref': 'Reversal Entry',
                'currency_id': self.currency_id.id if self.currency_id else (
                    self.company_id.currency_id.id if self.company_id.currency_id else False),
            }]
            move.line_ids = [(0, 0, val) for val in lines]
            move.post()

        self.write({'state': 'cancelled',
                    'outstanding_bal': 0.0})
        print(self.outstanding_bal)

    def invoice_line_vals(self, income_acc_id):
        vals = list()
        config_obj = self.env['ir.config_parameter'].sudo()

        principal_prod_id = config_obj.get_param('ae_loan_manag.principal_prod_id')
        principal_prod = self.env['product.product'].browse(int(principal_prod_id))
        vals.append({
            'name': "Down Payment",
            'product_id': principal_prod and principal_prod.id or False,
            'quantity': 1,
            'price_unit': self.down_payment,
            'unpaid_amount': 1 * self.down_payment,
            'account_id': income_acc_id,
        })
        return vals

    # @api.multi
    def _get_display_price(self, product):
        partner = self.partner_id
        pricelist = partner.property_product_pricelist
        if pricelist.discount_policy == 'with_discount':
            return product.with_context(pricelist=pricelist.id).lst_price
        final_price, rule_id = pricelist.get_product_price_rule(product, 1.0, partner)
        context_partner = dict(self.env.context, partner_id=partner.id, date=fields.Datetime.now)
        base_price, currency_id = self.with_context(context_partner)._get_real_price_currency(product, rule_id, 1.0,
                                                                                              product.uom_id,
                                                                                              pricelist.id)
        return max(base_price, final_price)

    # @api.multi
    def post_loan(self):
        for rec in self:
            ir_config_param_obj = self.env['ir.config_parameter'].sudo()
            if not rec.line_ids:
                raise UserError('Please Compute Loan Items first after that you can post the loan!')
            else:
                inv_obj = self.env['account.move']
                loan_acc_rec_id = ir_config_param_obj.get_param('ae_loan_manag.acc_rec_id')
                if not loan_acc_rec_id:
                    raise UserError(
                        _("Please Configure 'Loan Account Receivable' from Loans -> Configurations -> Settings!"))
                loan_acc_rec = self.env['account.account'].browse(int(loan_acc_rec_id))

                income_acc_id = ir_config_param_obj.sudo().get_param('ae_loan_manag.income_acc_id')
                if not income_acc_id:
                    raise UserError(_("Please Configure Income Account from Loans -> Configurations -> Settings!"))
                income_account = self.env['account.account'].browse(int(income_acc_id))

                difference_acc_id = ir_config_param_obj.sudo().get_param('ae_loan_manag.difference_acc_id')
                if not difference_acc_id:
                    raise UserError(_("Please Configure Difference Account from Loans -> Configurations -> Settings!"))
                difference_account = self.env['account.account'].browse(int(difference_acc_id))

                disbursement_acc_id = ir_config_param_obj.sudo().get_param('ae_loan_manag.disbursement_acc_id')
                if not disbursement_acc_id:
                    raise UserError(
                        _("Please Configure Disbursement Account from Loans -> Configurations -> Settings!"))
                disbursement_acc = self.env['account.account'].browse(int(disbursement_acc_id))

                write_off_acc_id = ir_config_param_obj.sudo().get_param('ae_loan_manag.write_off_account_id')
                if not write_off_acc_id:
                    raise UserError(_("Please Configure Write-Off Account from Loans -> Configurations -> Settings!"))
                write_off_acc = self.env['account.account'].browse(int(write_off_acc_id))

                fee_commission_acc_id = ir_config_param_obj.sudo().get_param('ae_loan_manag.fee_commission_acc_id')
                if not fee_commission_acc_id:
                    raise UserError(
                        _("Please Configure Fee and Commission Account from Loans -> Configurations -> Settings!"))
                fee_commission_acc = self.env['account.account'].browse(int(fee_commission_acc_id))

                loan_suspense_acc_id = ir_config_param_obj.sudo().get_param('ae_loan_manag.loan_suspense_acc_id')
                if not loan_suspense_acc_id:
                    raise UserError(
                        _("Please Loan suspense Account from Loans -> Configurations -> Settings!"))
                loan_suspense_acc = self.env['account.account'].browse(int(loan_suspense_acc_id))

                loan_jou_id = ir_config_param_obj.sudo().get_param('ae_loan_manag.loan_jou_id')
                if not loan_jou_id:
                    raise UserError(_("Please Configure Loan Journal from Loans -> Configurations -> Settings!"))
                loan_jou = self.env['account.journal'].browse(int(loan_jou_id))

                fee_product_id = ir_config_param_obj.sudo().get_param('ae_loan_manag.processing_fee_prod_id')
                if not fee_product_id:
                    raise UserError(
                        _("Please Configure Processing Fee Product from Loans -> Configurations -> Settings!"))
                fee_product = self.env['product.product'].browse(int(fee_product_id))

                prod_obj = self.env['product.product']
                principal_prod_id = ir_config_param_obj.sudo().get_param('ae_loan_manag.principal_prod_id')
                interest_prod_id = ir_config_param_obj.sudo().get_param('ae_loan_manag.interest_prod_id')
                life_ins_prod_id = ir_config_param_obj.sudo().get_param('ae_loan_manag.bonaire_principal_prod_id')
                fire_ins_prod_id = ir_config_param_obj.sudo().get_param('ae_loan_manag.bonaire_interest_prod_id')
                penalty_prod_id = ir_config_param_obj.sudo().get_param('ae_loan_manag.penalty_prod_id')
                ground_lease_prod_id = ir_config_param_obj.sudo().get_param('ae_loan_manag.ground_lease_product_id')
                restructuring_prod_id = ir_config_param_obj.sudo().get_param('ae_loan_manag.restructuring_prod_id')
                ob_tax_prod_id = ir_config_param_obj.sudo().get_param('ae_loan_manag.ob_tax_prod_id')

                principal_prod = prod_obj.browse(int(principal_prod_id))
                interest_prod = prod_obj.browse(int(interest_prod_id))
                life_ins_prod = prod_obj.browse(int(life_ins_prod_id))
                fire_ins_prod = prod_obj.browse(int(fire_ins_prod_id))
                penalty_prod = prod_obj.browse(int(penalty_prod_id))
                ground_lease_prod = prod_obj.browse(int(ground_lease_prod_id))
                restructuring_prod = prod_obj.browse(int(restructuring_prod_id))
                ob_tax_prod = prod_obj.browse(int(ob_tax_prod_id))

                partner = rec.partner_id
                today = datetime.today().date()
                loan_name = False
                if loan_jou:
                    code = loan_jou.code
                    loan_invoices = len(
                        self.env['account.move'].search(['|', ('loan_id', '!=', False), ('loan_line_id', '!=', False)]))
                    loan_name = code + '/' + str(fields.Date.today().month) + str(
                        fields.Date.today().year) + '/000' + str(
                        loan_invoices)
                loan_amt = rec.loan_amount
                company_currency = self.env.company.currency_id
                rate = 1.0
                if rec.currency_id != company_currency:
                    rate_line = self.env['res.currency.rate'].search([('currency_id', '=', rec.currency_id.id)],
                                                                     order='name desc', limit=1)
                    rate = round(rate_line.inverse_company_rate)
                if rec.difference_entry_id:
                    rec.difference_entry_id.write({'date': fields.Date.today(),
                                                   'create_date': fields.Datetime.now()})
                    rec.difference_entry_id.post()
                invoice_lines = list()
                if rec.pay_by_customer:
                    invoice_lines.append({
                        'product_id': restructuring_prod.id or False,
                        'name': restructuring_prod.name or 'Restructuring Fee',
                        'quantity': 1,
                        'price_unit': rec.restructure_fee,
                        'account_id': restructuring_prod.property_account_income_id.id if restructuring_prod.property_account_income_id else (
                            restructuring_prod.categ_id.property_account_income_categ_id.id if restructuring_prod.categ_id.property_account_income_categ_id else False)

                    })
                else:
                    invoice_lines.append({
                        'product_id': fee_product and fee_product.id or False,
                        'name': fee_product.name,
                        'quantity': 1,
                        'price_unit': rec._get_display_price(fee_product),
                        'unpaid_amount': 1 * rec._get_display_price(fee_product)

                    })

                fee_inv_data = {
                    'loan_id': rec.id,
                    # 'account_id': loan_acc_rec and loan_acc_rec.id or False,
                    'company_id': self.env.user.company_id.id,
                    'partner_id': rec.partner_id.id,
                    'currency_id': rec.currency_id.id if rec.currency_id else (
                        rec.company_id.currency_id.id if rec.company_id.currency_id else False),
                    'move_type': 'out_invoice',
                    'journal_id': loan_jou.id,
                    'invoice_date': rec.start_date and rec.start_date or datetime.today().date(),
                    'invoice_line_ids': [(0, 0, vals) for vals in
                                         invoice_lines]
                }
                fee_inv = inv_obj.create(fee_inv_data)
                if fee_inv:
                    rec.processing_fee_inv_id = fee_inv.id
                    fee_inv.loan_id = rec.id
                    fee_inv.with_context(from_validate=True).action_post()
                if rec.is_restructure_loan:
                    old_loan = self.env['account.loan']
                    if rec.old_loan_name:
                        old_loan = old_loan.search([('name', 'in', rec.old_loan_name.split(', '))])
                    if old_loan:
                        invoices = self.env['account.move'].search(
                            [('loan_id', 'in', old_loan.ids), ('move_type', '=', 'out_invoice'),
                             ('payment_state', '!=', 'paid')])
                        for inv in invoices:
                            write_off = inv.write_off_invoice()
                            write_off_obj = self.env['write.off.move'].search([('id', '=', write_off.get('res_id'))])
                            write_off_obj.sudo().submit_for_approval()
                            write_off_obj.write_off_line_ids.filtered(lambda l: l.unpaid_amount > 0.0).sudo().write(
                                {'is_select': True})
                            write_off_obj.process_write_off_move()
                            reversal_entry = self.env['account.move'].search(
                                [('reversed_entry_id', '=', inv.id), ('move_type', '=', 'entry')])
                            if inv and reversal_entry:
                                invoice_lines = inv.line_ids.filtered(
                                    lambda line: line.account_id.account_type in (
                                        'asset_receivable', 'liability_payable'))
                                invoice_lines.remove_move_reconcile()
                                reversal_lines = reversal_entry.mapped('line_ids').filtered(
                                    lambda line: line.account_id.account_type in (
                                        'asset_receivable', 'liability_payable'))
                                reversal_lines.remove_move_reconcile()


                                (invoice_lines + reversal_lines).reconcile()
                    if rec.total_unpaid_principal:
                        # Balancing Unpaid Principal Entry For New Loan
                        remaining_principal_move = self.env['account.move'].create({
                            'journal_id': loan_jou and loan_jou.id or False,
                            'loan_id': rec.id or False,
                            'ref': 'Reversal Entry Of' + ' ' + rec.name,
                            'date': fields.Date.today(),
                            'move_type': 'entry',
                            'currency_id': rec.currency_id.id,
                            'partner_id': rec.partner_id.id or False
                        })
                        lines = [{
                            'account_id': loan_acc_rec.id,
                            'partner_id': rec.partner_id.id or False,
                            # 'debit': 0,
                            # 'credit': (round(rate * rec.total_unpaid_principal, 2)),
                            'amount_currency': (round(-1 * rec.total_unpaid_principal, 2)),
                            'name': rec.name,
                            'date': fields.Date.today(),
                            'ref': 'Remaining Principal Credit Entry',
                            'currency_id': rec.currency_id.id,
                        }, {
                            'account_id': principal_prod.property_account_income_id.id if principal_prod.property_account_income_id else principal_prod.categ_id.property_account_income_categ_id.id,
                            'partner_id': rec.partner_id.id or False,
                            # 'debit': (round(rate * rec.total_unpaid_principal, 2)),
                            # 'credit': 0,
                            'amount_currency': (round(rec.total_unpaid_principal, 2)),
                            'name': rec.name,
                            'date': fields.Date.today(),
                            'ref': 'Remaining Principal Debit Entry',
                            'currency_id': rec.currency_id.id,
                        }]
                        remaining_principal_move.line_ids = [(0, 0, val) for val in lines]
                        remaining_principal_move.post()

                    if rec.total_unpaid_interest:
                        # Balancing Unpaid Interest Entry For New Loan
                        remaining_interest_move = self.env['account.move'].create({
                            'journal_id': loan_jou and loan_jou.id or False,
                            'loan_id': rec.id or False,
                            'ref': 'Reversal Entry Of' + ' ' + rec.name,
                            'date': fields.Date.today(),
                            'move_type': 'entry',
                            'currency_id': rec.currency_id.id,
                            'partner_id': rec.partner_id.id or False
                        })
                        lines = [{
                            'account_id': loan_acc_rec.id,
                            'partner_id': rec.partner_id.id or False,
                            # 'debit': 0,
                            # 'credit': (round(rate * rec.total_unpaid_interest, 2)),
                            'amount_currency': (round(-1 * rec.total_unpaid_interest, 2)),
                            'name': rec.name,
                            'date': fields.Date.today(),
                            'ref': 'Remaining Interest Credit Entry',
                            'currency_id': rec.currency_id.id,
                        }, {
                            'account_id': interest_prod.property_account_income_id.id if interest_prod.property_account_income_id else interest_prod.categ_id.property_account_income_categ_id.id,
                            'partner_id': rec.partner_id.id or False,
                            # 'debit': (round(rate * rec.total_unpaid_interest, 2)),
                            # 'credit': 0,
                            'amount_currency': (round(rec.total_unpaid_interest, 2)),
                            'name': rec.name,
                            'date': fields.Date.today(),
                            'ref': 'Remaining Interest Debit Entry',
                            'currency_id': rec.currency_id.id,
                        }]
                        remaining_interest_move.line_ids = [(0, 0, val) for val in lines]
                        remaining_interest_move.post()

                    if rec.total_unpaid_life_insurance:
                        # Balancing Unpaid Life Insurance Entry For New Loan
                        remaining_life_ins_move = self.env['account.move'].create({
                            'journal_id': loan_jou and loan_jou.id or False,
                            'loan_id': rec.id or False,
                            'ref': 'Reversal Entry Of' + ' ' + rec.name,
                            'date': fields.Date.today(),
                            'move_type': 'entry',
                            'currency_id': rec.currency_id.id,
                            'partner_id': rec.partner_id.id or False
                        })
                        lines = [{
                            'account_id': loan_acc_rec.id,
                            'partner_id': rec.partner_id.id or False,
                            # 'debit': 0,
                            # 'credit': (round(rate * rec.total_unpaid_life_insurance, 2)),
                            'amount_currency': (round(-1 * rec.total_unpaid_life_insurance, 2)),
                            'name': rec.name,
                            'date': fields.Date.today(),
                            'ref': 'Remaining Life Insurance Credit Entry',
                            'currency_id': rec.currency_id.id,
                        }, {
                            'account_id': life_ins_prod.property_account_income_id.id if life_ins_prod.property_account_income_id else life_ins_prod.categ_id.property_account_income_categ_id.id,
                            'partner_id': rec.partner_id.id or False,
                            # 'debit': (round(rate * rec.total_unpaid_life_insurance, 2)),
                            # 'credit': 0,
                            'amount_currency': (round(rec.total_unpaid_life_insurance, 2)),
                            'name': rec.name,
                            'date': fields.Date.today(),
                            'ref': 'Remaining Life Insurance Debit Entry',
                            'currency_id': rec.currency_id.id,
                        }]
                        remaining_life_ins_move.line_ids = [(0, 0, val) for val in lines]
                        remaining_life_ins_move.post()

                    if rec.total_unpaid_fire_insurance:
                        # Balancing Unpaid Fire Entry For New Loan
                        remaining_fire_ins_move = self.env['account.move'].create({
                            'journal_id': loan_jou and loan_jou.id or False,
                            'loan_id': rec.id or False,
                            'ref': 'Reversal Entry Of' + ' ' + rec.name,
                            'date': fields.Date.today(),
                            'move_type': 'entry',
                            'currency_id': rec.currency_id.id,
                            'partner_id': rec.partner_id.id or False
                        })
                        lines = [{
                            'account_id': loan_acc_rec.id,
                            'partner_id': rec.partner_id.id or False,
                            # 'debit': 0,
                            # 'credit': (round(rate * rec.total_unpaid_fire_insurance, 2)),
                            'amount_currency': (round(-1 * rec.total_unpaid_fire_insurance, 2)),
                            'name': rec.name,
                            'date': fields.Date.today(),
                            'ref': 'Remaining Fire Insurance Credit Entry',
                            'currency_id': rec.currency_id.id,
                        }, {
                            'account_id': fire_ins_prod.property_account_income_id.id if fire_ins_prod.property_account_income_id else fire_ins_prod.categ_id.property_account_income_categ_id.id,
                            'partner_id': rec.partner_id.id or False,
                            # 'debit': (round(rate * rec.total_unpaid_fire_insurance, 2)),
                            # 'credit': 0,
                            'amount_currency': (round(rec.total_unpaid_fire_insurance, 2)),
                            'name': rec.name,
                            'date': fields.Date.today(),
                            'ref': 'Remaining Fire Insurance Debit Entry',
                            'currency_id': rec.currency_id.id,
                        }]
                        remaining_fire_ins_move.line_ids = [(0, 0, val) for val in lines]
                        remaining_fire_ins_move.post()

                    if rec.total_penalties:
                        # Balancing Unpaid Penalty Entry For New Loan
                        remaining_penalty_ins_move = self.env['account.move'].create({
                            'journal_id': loan_jou and loan_jou.id or False,
                            'loan_id': rec.id or False,
                            'ref': 'Reversal Entry Of' + ' ' + rec.name,
                            'date': fields.Date.today(),
                            'move_type': 'entry',
                            'currency_id': rec.currency_id.id,
                            'partner_id': rec.partner_id.id or False
                        })
                        lines = [{
                            'account_id': loan_acc_rec.id,
                            'partner_id': rec.partner_id.id or False,
                            # 'debit': 0,
                            # 'credit': (round(rate * rec.total_penalties, 2)),
                            'amount_currency': (round(-1 * rec.total_penalties, 2)),
                            'name': rec.name,
                            'date': fields.Date.today(),
                            'ref': 'Remaining Penalty Credit Entry',
                            'currency_id': rec.currency_id.id,
                        }, {
                            'account_id': penalty_prod.property_account_income_id.id if penalty_prod.property_account_income_id else penalty_prod.categ_id.property_account_income_categ_id.id,
                            'partner_id': rec.partner_id.id or False,
                            # 'debit': (round(rate * rec.total_penalties, 2)),
                            # 'credit': 0,
                            'amount_currency': (round(rec.total_penalties, 2)),
                            'name': rec.name,
                            'date': fields.Date.today(),
                            'ref': 'Remaining Penalty Debit Entry',
                            'currency_id': rec.currency_id.id,
                        }]
                        remaining_penalty_ins_move.line_ids = [(0, 0, val) for val in lines]
                        remaining_penalty_ins_move.post()

                    if rec.total_unpaid_ground_lease:
                        # Balancing Unpaid Ground Lease Entry For New Loan
                        remaining_ground_lease_ins_move = self.env['account.move'].create({
                            'journal_id': loan_jou and loan_jou.id or False,
                            'loan_id': rec.id or False,
                            'ref': 'Reversal Entry Of' + ' ' + rec.name,
                            'date': fields.Date.today(),
                            'move_type': 'entry',
                            'currency_id': rec.currency_id.id,
                            'partner_id': rec.partner_id.id or False
                        })
                        lines = [{
                            'account_id': loan_acc_rec.id,
                            'partner_id': rec.partner_id.id or False,
                            # 'debit': 0,
                            # 'credit': (round(rate * rec.total_unpaid_ground_lease, 2)),
                            'amount_currency': (round(-1 * rec.total_unpaid_ground_lease, 2)),
                            'name': rec.name,
                            'date': fields.Date.today(),
                            'ref': 'Remaining Penalty Credit Entry',
                            'currency_id': rec.currency_id.id,
                        }, {
                            'account_id': ground_lease_prod.property_account_income_id.id if ground_lease_prod.property_account_income_id else ground_lease_prod.categ_id.property_account_income_categ_id.id,
                            'partner_id': rec.partner_id.id or False,
                            # 'debit': (round(rate * rec.total_unpaid_ground_lease, 2)),
                            # 'credit': 0,
                            'amount_currency': (round(rec.total_unpaid_ground_lease, 2)),
                            'name': rec.name,
                            'date': fields.Date.today(),
                            'ref': 'Remaining Penalty Debit Entry',
                            'currency_id': rec.currency_id.id,
                        }]
                        remaining_ground_lease_ins_move.line_ids = [(0, 0, val) for val in lines]
                        remaining_ground_lease_ins_move.post()

                    if old_loan and rec.restructure_id.writeoff_line_ids:
                        for old in rec.restructure_id.writeoff_line_ids:
                            # Outstanding Principal OLD LOAN
                            outstanding_move = self.env['account.move'].create({
                                'journal_id': loan_jou and loan_jou.id or False,
                                'loan_id': old.loan_id.id or False,
                                'ref': 'Balancing Outstanding Principal (OLD Loans)',
                                'date': today,
                                'move_type': 'entry',
                                'currency_id': old.loan_id.currency_id.id,
                                'partner_id': old.loan_id.partner_id.id or False,
                                'is_restructuring_inv': True
                            })
                            lines = [{
                                'account_id': disbursement_acc.id,
                                'partner_id': old.loan_id.partner_id.id or False,
                                # 'debit': 0,
                                # 'credit': (
                                #     round(rate * (old.loan_id.outstanding_bal),
                                #           2)) if rec.restructure_type == 'without_writeoff' else (
                                #     round(rate * (
                                #             old.loan_id.outstanding_bal - old.write_off_amount),
                                #           2)),
                                'amount_currency': (
                                    round(-1 * (old.loan_id.outstanding_bal),
                                          2)) if rec.restructure_type == 'without_writeoff' else (
                                    round(-1 * (
                                            old.loan_id.outstanding_bal - old.write_off_amount),
                                          2)),
                                'name': old.loan_id.name,
                                'date': today,
                                'ref': 'Balancing Outstanding Principal Credit Entry',
                                'currency_id': old.loan_id.currency_id.id,
                            }, {
                                'account_id': loan_suspense_acc_id or False,
                                'partner_id': old.loan_id.partner_id.id or False,
                                # 'debit': (
                                #     round(rate * (old.loan_id.outstanding_bal),
                                #           2)) if rec.restructure_type == 'without_writeoff' else (
                                #     round(rate * (
                                #             old.loan_id.outstanding_bal - old.write_off_amount),
                                #           2)),
                                # 'credit': 0,
                                'amount_currency': (
                                    round((old.loan_id.outstanding_bal),
                                          2)) if rec.restructure_type == 'without_writeoff' else (
                                    round((
                                            old.loan_id.outstanding_bal - old.write_off_amount),
                                        2)),
                                'name': old.loan_id.name,
                                'date': today,
                                'ref': 'Balancing Outstanding Principal Debit Entry',
                                'currency_id': old.loan_id.currency_id.id,
                            }]
                            outstanding_move.line_ids = [(0, 0, val) for val in lines]
                            outstanding_move.post()

                    # if rec.restructure_type == 'without_writeoff':
                    # Disbursement Entry New Loan

                    disbursement_lines = list()
                    tax_account = self.env['account.account'].search([('name', '=', 'Tax Payable')])
                    disbursement_move = self.env['account.move'].with_context(check_move_validity=False).create({
                        'journal_id': loan_jou and loan_jou.id or False,
                        'loan_id': rec.id or False,
                        'ref': 'Disbursement Entry' + ' ' + rec.name,
                        'date': today,
                        'move_type': 'entry',
                        'currency_id': rec.currency_id.id,
                        'partner_id': rec.partner_id.id or False,
                        'is_restructuring_inv': True
                    })
                    disbursement_lines.append({
                        'account_id': disbursement_acc.id or False,
                        'partner_id': rec.partner_id.id or False,
                        'amount_currency': rec.loan_amount,
                        'name': rec.name,
                        'date': today,
                        'ref': 'Disbursement DebitEntry',
                        'currency_id': rec.currency_id.id,

                    })
                    disbursement_lines.append({
                        'account_id': loan_suspense_acc.id,
                        'partner_id': rec.partner_id.id or False,
                        'amount_currency': -1 * rec.loan_amount if not rec.restructure_id.is_restructuring_fee and rec.pay_by_customer else -1 * (rec.loan_amount - rec.restructure_fee - rec.restructure_tax_amount),
                        'name': rec.name,
                        'date': today,
                        'ref': 'Disbursement Credit Entry',
                        'currency_id': rec.currency_id.id,
                    })

                    if rec.restructure_id.is_restructuring_fee and not rec.pay_by_customer:
                        disbursement_lines.append({
                            'account_id': fee_commission_acc.id,
                            'partner_id': rec.partner_id.id or False,
                            'amount_currency': -1 * rec.restructure_fee,
                            'name': rec.name,
                            'date': today,
                            'ref': 'Disbursement Credit Entry',
                            'currency_id': rec.currency_id.id,
                        })
                        disbursement_lines.append({
                            'account_id': tax_account.id if tax_account else fee_commission_acc.id,
                            'partner_id': rec.partner_id.id or False,
                            'amount_currency': -1 * rec.restructure_tax_amount,
                            'name': rec.name,
                            'date': today,
                            'ref': 'Disbursement Credit Entry',
                            'currency_id': rec.currency_id.id,
                        })
                    disbursement_move.with_context(check_move_validity=False).line_ids = [(0, 0, val) for val in disbursement_lines]
                    disbursement_move.post()

                    if rec.restructure_type == 'with_writeoff' and rec.restructure_id.writeoff_line_ids:
                        for old in rec.restructure_id.writeoff_line_ids:
                            # Write Off Entry Old Loan
                            write_off_move = self.env['account.move'].create({
                                'journal_id': loan_jou and loan_jou.id or False,
                                'loan_id': old.loan_id.id or False,
                                'ref': 'Write Off' + ' ' + old.loan_id.name,
                                'date': today,
                                'move_type': 'entry',
                                'currency_id': old.loan_id.currency_id.id,
                                'partner_id': old.loan_id.partner_id.id or False,
                                # 'is_restructuring_inv': True
                            })
                            lines = [{
                                'account_id': disbursement_acc.id or False,
                                'partner_id': old.loan_id.partner_id.id or False,
                                # 'debit': 0,
                                # 'credit': (round(rate * old.write_off_amount, 2)),
                                'amount_currency': (round(-1 * old.write_off_amount, 2)),
                                'name': old.loan_id.name,
                                'date': today,
                                'ref': 'Write Off Credit Entry',
                                'currency_id': old.loan_id.currency_id.id,
                            }, {
                                'account_id': write_off_acc.id or False,
                                'partner_id': old.loan_id.partner_id.id or False,
                                # 'debit': (round(rate * old.write_off_amount, 2)),
                                # 'credit': 0,
                                'amount_currency': (round(old.write_off_amount, 2)),
                                'name': old.loan_id.name,
                                'date': today,
                                'ref': 'Write Off Debit Entry',
                                'currency_id': old.loan_id.currency_id.id,
                            }]
                            write_off_move.line_ids = [(0, 0, val) for val in lines]
                            write_off_move.post()

                    rec.write({'state': 'posted'})

                    if old_loan:
                        for old in old_loan:
                            old.write({'state': 'closed',
                                       'close_date': fields.Date.today(),
                                       'outstanding_bal': 0.0})

                else:
                    move = self.env['account.move'].create({
                        # 'name': loan_name,
                        'journal_id': loan_jou and loan_jou.id or False,
                        'loan_id': rec.id or False,
                        'ref': rec.name,
                        'date': today,
                        'currency_id': rec.currency_id.id if rec.currency_id else (
                            rec.company_id.currency_id.id if rec.company_id.currency_id else False),
                        'partner_id': partner and partner.id or False
                    })
                    lines = [{
                        'account_id': loan_suspense_acc and loan_suspense_acc_id,

                        'partner_id': partner and partner.id or False,
                        'amount_currency': -1 * loan_amt,
                        'name': rec.name,
                        'date': today,
                        'ref': 'Loan Entry',
                        'currency_id': rec.currency_id.id if rec.currency_id else (
                            rec.company_id.currency_id.id if rec.company_id.currency_id else False),
                    }, {
                        'account_id': disbursement_acc and disbursement_acc.id or False,
                        'partner_id': partner and partner.id or False,
                        'amount_currency': loan_amt,
                        'name': rec.name,
                        'date': today,
                        'ref': 'Loan Entry',
                        'currency_id': rec.currency_id.id if rec.currency_id else (
                            rec.company_id.currency_id.id if rec.company_id.currency_id else False),
                    }]
                    move.line_ids = [(0, 0, val) for val in lines]
                    move.post()

                    # self.is_compute_items = True
                    # self.period_or_monthly = True
                    if rec.state != 'draft':
                        raise UserError(_('Only loans in Draft state can be posted'))

                    if rec.is_down_payment and rec.down_payment != 0:
                        if rec.start_date:
                            date = datetime.strptime(str(rec.start_date), DF).date()
                        else:
                            date = datetime.today().date()
                        delta = relativedelta(months=rec.method_period)
                        if not rec.payment_on_first_period:
                            date += delta
                        sequence = 0
                        line_data = {
                            'loan_id': rec.id,
                            'sequence': sequence,
                            'payment_amount': rec.down_payment,
                            'interests_amount': 0,
                            'date': rec.start_date and rec.start_date or datetime.today().date(),
                            'pending_principal_amount': rec.loan_amount,
                            'is_down_payment': True
                        }
                        rec.write({'state': 'posted'})
                        rec.compute_draft_lines()
                        down_payment_line = self.env['account.loan.line'].create(line_data)
                        res = []

                        inv_data = {
                            'loan_id': rec.id,
                            'loan_line_id': down_payment_line and down_payment_line.id if down_payment_line else False,
                            # 'account_id': loan_acc_rec and loan_acc_rec.id or False,
                            'company_id': self.env.user.company_id.id,
                            'partner_id': rec.partner_id.id,
                            'currency_id': rec.currency_id.id if rec.currency_id else (
                                rec.company_id.currency_id.id if rec.company_id.currency_id else False),
                            'move_type': 'out_invoice',
                            'journal_id': loan_jou.id,
                            'invoice_date': rec.start_date and rec.start_date or datetime.today().date(),
                            'invoice_line_ids': [(0, 0, vals) for vals in
                                                 rec.invoice_line_vals(int(income_acc_id))]
                        }
                        inv_id = inv_obj.create(inv_data)
                        if inv_id:
                            res.append(inv_id.id)
                            inv_id.is_down_payment = True
                            inv_id.with_context(from_validate=True).action_post()
                        rec.post()
                        return
                    else:
                        rec.post()

    # @api.multi
    def due_date_selection(self):
        """
        Open popup to move due date of EMIs
        :return:
        """
        for rec in self:
            postpone_loan = self.env['move.due.date']
            existing_postpone_loan = postpone_loan.search([('loan_id', '=', rec.id), ('state', '!=', 'approved')],
                                                          limit=1)
            if existing_postpone_loan:
                postpone_loan = existing_postpone_loan
            else:
                postpone_loan = postpone_loan.create({'loan_id': rec.id})

            return {
                'name': _('Postpone Installments'),
                'res_model': 'move.due.date',
                'res_id': existing_postpone_loan.id or postpone_loan.id,
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'view_id': False,
                'target': 'new'
            }

    # @api.multi
    def action_loan_detail_send(self):
        '''
        This function opens a window to compose an email, with the loan template message loaded by default
        '''
        for loan in self:
            template_id = self.env['ir.model.data']._xmlid_to_res_id('smart_loan_system.email_template_loan_details',
                                                                     raise_if_not_found=False)
            record = loan.sudo()
            ctx = {
                'default_model': 'account.loan',
                'default_res_id': loan.ids[0],
                'default_use_template': bool(template_id),
                'default_template_id': template_id,
                'default_composition_mode': 'comment',
                'mark_so_as_sent': True,
                'custom_layout': "mail.mail_notification_paynow",
                'force_email': True,
                'record': record,
                'user_id': self.env.user
            }

            return {
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'mail.compose.message',
                'views': [(False, 'form')],
                'view_id': False,
                'target': 'new',
                'context': ctx,
            }


class LoanRestructuringLines(models.Model):
    _name = 'loan.restructuring.lines'
    _description = "Loan Restructuring Lines"

    loan_id = fields.Many2one('account.loan', 'Parent Loan')
    restructured_id = fields.Many2one('restructure.loan.wizard')
    name = fields.Char(related='loan_id.name')
    currency_id = fields.Many2one('res.currency')
    company_currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    date = fields.Date(required=True, default=fields.Date.today(), string="Restructuring Date")
    amount = fields.Monetary(
        currency_field='company_currency_id', string='Closing Amount')
    balance_amount = fields.Monetary(string='Balancing Amount', currency_field='company_currency_id')
    restructure_type = fields.Selection([('without_writeoff', 'Restructure Without Write Off'),
                                         ('with_writeoff', 'Restructure With Write Off')], string='Restructure Type')
    write_off_amount = fields.Float(string="Principal Write-Off Amount")
    outstanding_principal_amount = fields.Float(string="Outstanding Principal")
    remaining_principal_amount = fields.Monetary(string="Remaining Principal", currency_field='company_currency_id')
    remaining_interest_amount = fields.Monetary(string="Remaining Interest", currency_field='company_currency_id')
    remaining_life_insurance_amount = fields.Monetary(string="Remaining Life Insurance",
                                                      currency_field='company_currency_id')
    remaining_fire_insurance_amount = fields.Monetary(string="Remaining Fire Insurance",
                                                      currency_field='company_currency_id')
    remaining_penalties_amount = fields.Monetary(string="Remaining Penalties", currency_field='company_currency_id')
    remaining_ground_lease = fields.Monetary(string="Remaining Ground Lease", currency_field='company_currency_id')
    new_loan_amount = fields.Monetary(string="New Loan Amount", currency_field='currency_id')
    difference_amount = fields.Monetary(string="Difference Amount", currency_field='company_currency_id')
    new_loan_currency_id = fields.Many2one(
        'res.currency'
    )
    outstanding_without_writoff = fields.Float(string="Outstanding Principal After Write-Off")
    pay_by_customer = fields.Boolean()
    restructure_fee = fields.Monetary(currency_field='currency_id')
    tax_amount = fields.Monetary('OB', currency_field='currency_id')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submit_approval', 'Submit For Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ])
    reject_reason = fields.Text()
    selection_wizard_id = fields.Many2one('select.restructure.loan')
    write_off_line_ids = fields.One2many('restructure.loan.writeoff.lines', 'loan_restructure_line_id')


class RestructureLoanWriteoffLines(models.Model):
    _name = 'restructure.loan.writeoff.lines'
    _description = "Restructure Loan Writeoff Lines"

    loan_restructure_line_id = fields.Many2one('loan.restructuring.lines')
    loan_id = fields.Many2one('account.loan')
    currency_id = fields.Many2one('res.currency', related='loan_id.currency_id')
    company_currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    write_off_amount = fields.Float()
    company_currency_amount = fields.Monetary(currency_field='company_currency_id')


class AssignLoanCollaterals(models.Model):
    _name = 'assign.loan.collaterals'
    _description = 'Assign Loan Collaterals'

    loan_id = fields.Many2one('account.loan')
    customer_id = fields.Many2one('res.partner', 'Customer', required=True, related='loan_id.partner_id')
    collateral_ids = fields.Many2many('loan.collateral')


class GetLoanRange(models.Model):
    _name = 'loan.invoice'
    _description = "Loan Invoices"

    name = fields.Char("Loan Invoice Range")
    loan_id = fields.Many2one('account.loan', string="Loan")
    move_id = fields.Many2one('account.move', string="Invoice")
    month = fields.Integer("Month")
    year = fields.Integer("year")
    sequence_number = fields.Char("Sequence")
    date_invoice = fields.Date("Invoice Date")


class PaymentHistory(models.Model):
    _name = 'account.payment.history'
    _description = "Payment History"

    partner_id = fields.Many2one('res.partner', "Partner", readonly=True)
    payment_date = fields.Date("Payment Date", readonly=True)
    journal_id = fields.Many2one('account.journal', readonly=True)
    amount = fields.Float("Paid Amount", readonly=True)
    loan_id = fields.Many2one('account.loan')
    payment_ids = fields.Many2many('account.payment', 'rel_payment_history', 'payment_history_id', 'rel_pay_history_id')
    invoice_ids = fields.Many2many('account.move', 'rel_inv_pay_history', 'inv_pay_history_id',
                                   'rel_inv_pay_history_id', string='Invoices')
    description = fields.Char('Description')
    payment_method = fields.Selection([('reg_pay', 'Register Payment (on Invoice)'),
                                       ('pay_1', 'Settle with next due instalment rest with principal'),
                                       ('pay_2', 'Cover all next due installments'),
                                       ('pay_3', 'Cover only principal outstanding')], string='Payment Method')
    state = fields.Selection([('running', 'Running'),
                              ('cancel', 'Cancel')], string='State', default='running')


class LoanTransactionHistory(models.Model):
    _name = 'loan.transaction.history'
    _description = "Transaction History"

    date = fields.Date("Date")
    payment_ids = fields.One2many('account.payment', 'history_id', string="Payment Reference")
    reference = fields.Char('Reference')
    description = fields.Char('Description')
    debit = fields.Float('Debit')
    credit = fields.Float('Credit')
    loan_id = fields.Many2one('account.loan', string="Loan")
    move_id = fields.Many2one('account.move', string="Invoice")
    balance = fields.Float("Balance", compute='_get_transaction_balance')
    state = fields.Selection([('running', 'Running'),
                              ('cancel', 'Cancel')], string='State', default='running')

    # @api.multi
    def _get_transaction_balance(self):
        balance = 0
        for history in self.search([('loan_id', '=', self._context.get('active_id'))],
                                   order="date, id"):
            if history.description == 'Payment Received':
                balance += history.debit
                balance -= history.credit
            elif datetime.strptime(str(history.date), DF).date() < date.today():
                balance += history.debit
                balance -= history.credit
            history.balance = balance


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    # loan_id = fields.Many2one(related='invoice_ids.loan_id')
    history_id = fields.Many2one('loan.transaction.history')
    transfer_entry_ids = fields.Many2many('account.move')
    loan_id = fields.Many2one('account.loan')

    # Create Payment History and Disbursement Move when paying invoice

    def create_payment_history_and_disbursement_move(self, payment_ids, invoice_id):

        payment_his_obj = self.env['account.payment.history']

        today = datetime.today().date()
        ir_config_param_obj = self.env['ir.config_parameter'].sudo()
        move_obj = self.env['account.move'].sudo()
        loan_jou_id = ir_config_param_obj.sudo().get_param('ae_loan_manag.loan_jou_id')
        loan_jou = self.env['account.journal'].browse(int(loan_jou_id))
        disbursement_acc_id = ir_config_param_obj.sudo().get_param('ae_loan_manag.disbursement_acc_id')

        for invoice in invoice_id:
            if invoice.loan_id:
                if not loan_jou_id:
                    raise UserError(_("Please Configure Loan Journal from Loans -> Configurations -> Settings!"))
                for payment in payment_ids:
                    pay_histories = payment_his_obj.search([('payment_ids', 'in', payment.id),
                                                            ('loan_id', '=', invoice.loan_id.id),
                                                            ('state', '=', 'running')])
                    for history in pay_histories:
                        if (history.invoice_ids and invoice.id not in history.invoice_ids.ids) or not \
                                history.invoice_ids:
                            history.invoice_ids = [(4, invoice.id)]

    def action_post(self):
        res = super(AccountPayment, self).action_post()
        context = self._context
        if self._context.get('active_model') == 'account.move':
            invoice = self.env['account.move'].search([('id', '=', context.get('active_id'))], limit=1)
        else:
            invoice = self.reconciled_invoice_ids[0]

        self.create_payment_history_and_disbursement_move(self, invoice)
        if invoice and invoice.loan_id and not context.get('paid_amount_from_loan'):
            loan = invoice.loan_id
            # Create Payment History
            loan_payment_history_obj = self.env['account.payment.history']
            loan_payment_history_obj.create({
                'payment_ids': [(4, self.id)],
                'description': 'Payment Received',
                'amount': self.amount,
                'loan_id': loan and loan.id or False,
                'partner_id': loan.partner_id and loan.partner_id.id or False,
                'payment_date': self.date,
                'journal_id': self.journal_id and self.journal_id.id or False,
                'invoice_ids': [(4, invoice.id)],
                'payment_method': 'reg_pay',
                'state': 'running'
            })
            # Create Transaction History
            loan_transaction_history_obj = self.env['loan.transaction.history']
            loan_transaction_history_obj.create({
                'date': self.date,
                'loan_id': loan and loan.id or False,
                'reference': self.name,
                'description': 'Payment Received',
                'credit': self.amount,
                'payment_ids': [(4, self.id)],
                'state': 'running'
            })

        return res

    def action_draft(self):
        # res =
        # Unlink Payment reference from loan payment history
        pay_his_obj = self.env['account.payment.history']
        trans_his_obj = self.env['loan.transaction.history']
        for payment in self:
            transactions = trans_his_obj.search([('reference', '=', payment.name)])
            if transactions:
                for trans in transactions:
                    trans.write({'state': 'cancel'})
                transactions.unlink()
            histories = pay_his_obj.search([('payment_ids', 'in', payment.id), ('partner_id', '=', self.partner_id.id)])
            for history in histories:
                if len(history.payment_ids.ids) == 1 and history.payment_ids.id == payment.id:
                    history.write({'state': 'cancel'})
                    history.unlink()
                else:
                    history.payment_ids = [(3, payment.id)]
                    history.amount -= payment.amount

        return super(AccountPayment, self).action_draft()

    def action_cancel(self):
        res = super(AccountPayment, self).action_cancel()

        if self.ref:
            move = self.env['account.move'].search([('name', '=', self.ref)])
            move.write({'cancel_receipt_id': self.id,
                        'cancel_receipt_name': self.name})

        # Unlink Payment reference from loan payment history
        pay_his_obj = self.env['account.payment.history']
        trans_his_obj = self.env['loan.transaction.history']
        for payment in self:
            transactions = trans_his_obj.search([('reference', '=', payment.name)])
            if transactions:
                for trans in transactions:
                    trans.write({'state': 'cancel'})
                transactions.unlink()
            histories = pay_his_obj.search([('payment_ids', 'in', payment.id), ('partner_id', '=', self.partner_id.id)])
            for history in histories:
                if len(history.payment_ids.ids) == 1 and history.payment_ids.id == payment.id:
                    history.write({'state': 'cancel'})
                    history.unlink()
                else:
                    history.payment_ids = [(3, payment.id)]
                    history.amount -= payment.amount

        return res


class LoanChanges(models.Model):
    _name = 'loan.changes'
    _description = "Loan Changes"

    date = fields.Date('Date of Change')
    due_date_selection = fields.Selection([('by_days', 'By Certain Amount of Days'),
                                           ('by_month', 'By Number of Months'),
                                           ('reset', "Reset all Installment's date")], string="Action")
    data_added = fields.Integer("Days/Months Postponed")
    reason = fields.Text("Reason")
    loan_id = fields.Many2one('account.loan', string="Loan")
    old_inv_date = fields.Date("Initial due date")
    new_inv_date = fields.Date("New due date")
