from odoo import api, fields, models, _
import logging
from odoo.exceptions import UserError, Warning
import psycopg2
from psycopg2 import InterfaceError, OperationalError
import time


_logger = logging.getLogger(__name__)


class Accruals(models.Model):
    _name = 'loan.accruals'
    _description = 'Loan Accruals'
    _rec_name = 'loan_id'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    loan_id = fields.Many2one('account.loan')
    currency_id = fields.Many2one('res.currency', related='loan_id.currency_id')
    daily_interest_accrue = fields.Monetary(currency_field='currency_id')
    daily_penalty_accrue = fields.Monetary(currency_field='currency_id')
    monthly_interest_accrue = fields.Monetary(string='MTD', currency_field='currency_id', compute='_compute_mtd_ytd')
    yearly_interest_accrue = fields.Monetary(string='YTD', currency_field='currency_id', compute='_compute_mtd_ytd')

    accrual_interest_ids = fields.One2many('accrual.interest', 'accrual_id')
    accrual_penalty_ids = fields.One2many('accrual.penalty', 'accrual_id')

    @api.depends('accrual_interest_ids')
    def _compute_mtd_ytd(self):
        for rec in self:
            if rec.accrual_interest_ids:
                today = fields.Date.today()
                monthly_total = 0.0
                yearly_total = 0.0
                for line in rec.accrual_interest_ids:
                    if line.date and line.date.month == today.month:
                        monthly_total = monthly_total + line.interest_amount
                    if line.date and line.date.year == today.year:
                        yearly_total = yearly_total + line.interest_amount
                rec.monthly_interest_accrue = monthly_total
                rec.yearly_interest_accrue = yearly_total
            else:
                rec.monthly_interest_accrue = 0.0
                rec.yearly_interest_accrue = 0.0
            rec.loan_id.write({'monthly_interest_accrue': rec.monthly_interest_accrue,
                               'yearly_interest_accrue': rec.yearly_interest_accrue})

    def _create_accruals(self, loan_id, daily_interest_accrue, daily_penalty_accrue):
        for rec in self:
            accrual = rec.env['loan.accruals'].create({'loan_id': loan_id,
                                                       'daily_interest_accrue': daily_interest_accrue,
                                                       'daily_penalty_accrue': daily_penalty_accrue})
            return accrual

    @api.model
    def daily_loan_accruals_creation(self):
        today_date = fields.Date.today()
        loans = self.env['account.loan'].search(
            [('expected_end_date', '>=', today_date), ('loan_migration_group', '=', 'Group 5'),
             ('state', '=', 'posted')])
        print(len(loans))
        error_messages = []
        for loan in loans:
            try:
                interest_accrue_line = False
                loan_line = self.env['account.loan.line'].search([('loan_id', '=', loan.id), ('date', '>=', today_date)],
                                                                 order='date', limit=1)
                previous_loan_line = False
                if loan_line.sequence > 1:
                    previous_loan_line = self.env['account.loan.line'].search(
                        [('loan_id', '=', loan.id), ('sequence', '=', (loan_line.sequence - 1))], limit=1)
                    interest_accrue_line = previous_loan_line
                else:
                    interest_accrue_line = loan_line

                penalty_accrue_line = self.env['account.loan.line'].search(
                    [('loan_id', '=', loan.id), ('invoice_ids', '!=', False), ('date', '<', today_date)],
                    order='sequence desc', limit=1)

                days_difference = 0
                if loan_line.sequence == 1:
                    days_difference = (loan.first_payment_due - loan.start_date).days
                elif previous_loan_line and loan_line.sequence > 1:
                    days_difference = (loan_line.date - previous_loan_line.date).days
                daily_interest = 0.0
                if interest_accrue_line.pending_principal_amount and loan.rate:
                    if days_difference == 31:
                        daily_interest = (loan.rate / 100 / 372 * interest_accrue_line.pending_principal_amount)
                    elif days_difference == 30:
                        daily_interest = (loan.rate / 100 / 360 * interest_accrue_line.pending_principal_amount)
                    elif days_difference == 29:
                        daily_interest = (loan.rate / 100 / 348 * interest_accrue_line.pending_principal_amount)
                    elif days_difference == 28:
                        daily_interest = (loan.rate / 100 / 336 * interest_accrue_line.pending_principal_amount)
                    else:
                        daily_interest = (loan.rate / 100 / 360 * interest_accrue_line.pending_principal_amount)
                else:
                    daily_interest = 0.0

                daily_penalty = 0.0
                if loan.penalty_percent and loan.amount_due:
                    daily_penalty = (loan.penalty_percent / 100 / 360 * loan.amount_due)
                else:
                    daily_penalty = 0.0
                total_daily_interest = 0.0
                total_daily_penalty = 0.0
                existing_interest_lines = self.env['accrual.interest'].search(
                    [('loan_id', '=', loan.id), ('loan_line_id', '=', interest_accrue_line.id)])
                if existing_interest_lines:
                    total_daily_interest = total_daily_interest + sum(
                        existing_interest_lines.mapped('interest_amount')) + daily_interest
                existing_penalty_lines = self.env['accrual.penalty'].search(
                    [('loan_id', '=', loan.id), ('loan_line_id', '=', penalty_accrue_line.id)])
                if existing_penalty_lines:
                    total_daily_penalty = total_daily_penalty + sum(
                        existing_penalty_lines.mapped('penalty_amount')) + daily_penalty
                interest_accrue_line.write({'interest_accrue': total_daily_interest})
                penalty_accrue_line.write({'penalty_accrue': total_daily_penalty})
                # loan.write({'is_accrual': True})
                print(loan)
                # Accrual
                accrual = self.env['loan.accruals'].search([('loan_id', '=', loan.id)])
                if not accrual:
                    accrual = self._create_accruals(loan.id, total_daily_interest, total_daily_penalty)


                # Interest line
                interest_line = self.env['accrual.interest'].search([
                    ('accrual_id', '=', accrual.id),
                    ('date', '=', today_date)
                ])
                interest_line_data = {
                    'accrual_id': accrual.id,
                    'rate': loan.rate or 0.0,
                    'principal_amount': interest_accrue_line.pending_principal_amount or 0.0,
                    'interest_amount': daily_interest,
                    'date': today_date,
                    'loan_line_id': interest_accrue_line.id
                }
                interest_line.create(interest_line_data) if not interest_line else interest_line.write(
                    interest_line_data)

                # Penalty line
                penalty_line = self.env['accrual.penalty'].search([
                    ('accrual_id', '=', accrual.id),
                    ('date', '=', today_date)
                ])
                penalty_line_data = {
                    'accrual_id': accrual.id,
                    'amount_due': loan.amount_due or 0.0,
                    'penalty_rate': loan.penalty_percent or 0.0,
                    'date': today_date,
                    'penalty_amount': daily_penalty,
                    'loan_line_id': penalty_accrue_line.id
                }
                penalty_line.create(penalty_line_data) if not penalty_line else penalty_line.write(penalty_line_data)
                print('Record is Created')
                self.env.cr.commit()
            except (Exception, OperationalError, InterfaceError, psycopg2.Error, UserError) as e:
                if 'cursor already closed' in str(e):
                    self.env.cr.reset()
                    time.sleep(5)
                    self.env.cr.rollback()
                else:
                    error_message = f"Error in 'Accrual Creation' for Loan {loan.name}: {str(e)}"
                    _logger.error(error_message)
                    error_messages.append(error_message)
                    time.sleep(5)
                    self.env.cr.rollback()
                continue

        if error_messages:
            failure_record = self.env['failure.history'].create({
                'name': 'Loan Robots-->Loan Penalty Application',
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


class AccrualInterest(models.Model):
    _name = 'accrual.interest'
    _description = 'Accrual Interest'

    accrual_id = fields.Many2one('loan.accruals')
    loan_id = fields.Many2one('account.loan', related='accrual_id.loan_id')
    loan_line_id = fields.Many2one('account.loan.line')
    currency_id = fields.Many2one('res.currency', related='accrual_id.currency_id')
    principal_amount = fields.Float()
    rate = fields.Float()
    date = fields.Date()
    interest_amount = fields.Monetary(currency_field='currency_id')
    next_installment_date = fields.Date(compute='_compute_next_installment_date')

    @api.depends('loan_line_id', 'loan_id')
    def _compute_next_installment_date(self):
        for rec in self:
            today_date = fields.Date.today()
            if rec.loan_line_id and rec.loan_id:
                if rec.loan_line_id.date >= today_date:
                    rec.next_installment_date = rec.loan_line_id.date
                else:
                    rec.next_installment_date = False
            else:
                rec.next_installment_date = False


class AccrualPenalty(models.Model):
    _name = 'accrual.penalty'
    _description = 'Accrual Penalty'

    accrual_id = fields.Many2one('loan.accruals')
    loan_id = fields.Many2one('account.loan', related='accrual_id.loan_id')
    loan_line_id = fields.Many2one('account.loan.line')
    currency_id = fields.Many2one('res.currency', related='accrual_id.currency_id')
    amount_due = fields.Monetary(currency_field='currency_id')
    penalty_rate = fields.Float()
    date = fields.Date()
    penalty_amount = fields.Monetary(currency_field='currency_id')
    next_installment_date = fields.Date(compute='_compute_next_installment_date')

    @api.depends('loan_line_id', 'loan_id')
    def _compute_next_installment_date(self):
        for rec in self:
            today_date = fields.Date.today()
            if rec.loan_line_id and rec.loan_id:
                if rec.loan_line_id.date >= today_date:
                    rec.next_installment_date = rec.loan_line_id.date
                else:
                    rec.next_installment_date = False
            else:
                rec.next_installment_date = False
