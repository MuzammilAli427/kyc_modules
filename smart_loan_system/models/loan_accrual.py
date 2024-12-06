from odoo import api, fields, models, _
from datetime import date, datetime, timedelta
import pytz
import logging
from odoo.exceptions import UserError, Warning
import psycopg2
from psycopg2 import InterfaceError, OperationalError
import time
import xlsxwriter
import base64
from io import BytesIO


_logger = logging.getLogger(__name__)



class LoanAccrual(models.Model):
    _name = 'loan.accrual'
    _description = 'Loan Accrual'
    _rec_name = 'loan_name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    loan_id = fields.Many2one('account.loan')
    loan_name = fields.Char(related='loan_id.name')
    currency_id = fields.Many2one('res.currency', related='loan_id.currency_id')
    daily_interest_accrue = fields.Monetary(currency_field='currency_id')
    daily_penalty_accrue = fields.Monetary(currency_field='currency_id')
    monthly_interest_accrue = fields.Monetary(string='MTD', currency_field='currency_id', compute='_compute_mtd_ytd')
    yearly_interest_accrue = fields.Monetary(string='YTD', currency_field='currency_id', compute='_compute_mtd_ytd')

    loan_accrual_interest_ids = fields.One2many('loan.accrual.interest', 'loan_accrual_id')
    loan_accrual_penalty_ids = fields.One2many('loan.accrual.penalty', 'loan_accrual_id')
    is_accrual_created = fields.Boolean(default=False)

    def rounding_button(self):
        for rec in self:
            if rec.loan_accrual_interest_ids:
                for int_line in rec.loan_accrual_interest_ids:
                    int_line.write({'interest_amount': round(int_line.interest_amount, 2)})
            if rec.loan_accrual_penalty_ids:
                for pnt_line in rec.loan_accrual_penalty_ids:
                    pnt_line.write({'penalty_amount': round(pnt_line.penalty_amount, 2)})

    @api.depends('loan_accrual_interest_ids')
    def _compute_mtd_ytd(self):
        for rec in self:
            if rec.loan_accrual_interest_ids:
                today = fields.Date.today()
                monthly_total = 0.0
                yearly_total = 0.0
                for line in rec.loan_accrual_interest_ids:
                    if line.date and line.date.month == today.month:
                        monthly_total = monthly_total + round(line.interest_amount, 2)
                    if line.date and line.date.year == today.year:
                        yearly_total = yearly_total + round(line.interest_amount, 2)
                rec.monthly_interest_accrue = round(monthly_total, 2)
                rec.yearly_interest_accrue = round(yearly_total, 2)
            else:
                rec.monthly_interest_accrue = 0.0
                rec.yearly_interest_accrue = 0.0
            rec.loan_id.write({'monthly_interest_accrue': rec.monthly_interest_accrue,
                               'yearly_interest_accrue': rec.yearly_interest_accrue})

    @api.model
    def daily_loan_accrual_creation(self):
        curacao_tz = pytz.timezone('America/Curacao')
        utc_now = datetime.now(pytz.utc)
        curacao_now = utc_now.astimezone(curacao_tz)
        today_date = curacao_now.date()
        error_messages = []
        loan_data = []
        loans = self.env['account.loan'].search(
            ['|', ('loan_migration_group', '=', 'Group 5'), ('loan_migration_group', '=', False), ('expected_end_date', '>=', today_date), ('state', '=', 'posted')])
        for loan in loans:
            try:
                interest_accrue_line = False
                loan_line = self.env['account.loan.line'].search([('loan_id', '=', loan.id), ('date', '>=', today_date)],
                                                                 order='date', limit=1)
                previous_loan_line = False
                if loan_line.sequence > 1:
                    previous_loan_line = self.env['account.loan.line'].search(
                        [('loan_id', '=', loan.id), ('sequence', '=', (loan_line.sequence - 1))], limit=1)
                if loan.start_date <= today_date and loan.first_payment_due >= today_date:
                    interest_accrue_line = self.env['account.loan.line'].search(
                        [('loan_id', '=', loan.id), ('sequence', '=', 1)])
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
                if interest_accrue_line and interest_accrue_line.pending_principal_amount and loan.rate:
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
                if interest_accrue_line:
                    existing_interest_lines = self.env['loan.accrual.interest'].search(
                        [('loan_id', '=', loan.id), ('loan_line_id', '=', interest_accrue_line.id)])
                    if existing_interest_lines:
                        total_daily_interest = round(daily_interest, 2) + sum(
                            round(amount, 2) for amount in existing_interest_lines.mapped('interest_amount'))
                else:
                    total_daily_interest = round(daily_interest, 2)

                if penalty_accrue_line:
                    existing_penalty_lines = self.env['loan.accrual.penalty'].search(
                        [('loan_id', '=', loan.id), ('loan_line_id', '=', penalty_accrue_line.id)])
                    if existing_penalty_lines:
                        total_daily_penalty = round(daily_penalty, 2) + sum(
                            round(amount, 2) for amount in existing_penalty_lines.mapped('penalty_amount'))
                else:
                    total_daily_penalty = round(daily_penalty, 2)

                loan_data.append({
                    'loan_name': loan.name,
                    'interest_accrue_amount': interest_accrue_line.interest_accrue or 0.0,
                    'penalty_accrue_amount': penalty_accrue_line.penalty_accrue or 0.0,
                    'new_interest_accrue_amount': total_daily_interest or 0.0,
                    'new_penalty_accrue_amount': total_daily_penalty or 0.0,
                })

                if not interest_accrue_line.loan_id.is_accrual_created:
                    interest_accrue_line.write({'interest_accrue': total_daily_interest})
                if not penalty_accrue_line.loan_id.is_accrual_created:
                    penalty_accrue_line.write({'penalty_accrue': total_daily_penalty})
                penalty_accrue_line.loan_id.write({'is_accrual': True})
                print(loan)
                # Accrual
                new_accrual = self.env['loan.accrual']
                accrual = self.env['loan.accrual'].search([('loan_id', '=', loan.id)])
                if accrual and not accrual.is_accrual_created:
                    accrual.write({'daily_interest_accrue': total_daily_interest or 0.0,
                                   'daily_penalty_accrue': total_daily_penalty or 0.0})
                elif not accrual:
                    accrual_data = {
                        'loan_id': loan.id,
                        'daily_interest_accrue': total_daily_interest or 0.0,
                        'daily_penalty_accrue': total_daily_penalty or 0.0,
                    }
                    new_accrual = new_accrual.create(accrual_data)

                # Interest line
                interest_line = self.env['loan.accrual.interest'].search([
                    ('loan_accrual_id', '=', accrual.id or new_accrual.id),
                    ('date', '=', today_date)
                ])
                if not interest_line.loan_accrual_id.is_accrual_created:
                    interest_line_data = {
                        'loan_accrual_id': accrual.id or new_accrual.id,
                        'rate': loan.rate or 0.0,
                        'principal_amount': interest_accrue_line.pending_principal_amount or 0.0,
                        'interest_amount': round(daily_interest, 2),
                        'date': today_date,
                        'loan_line_id': interest_accrue_line.id,
                        'loan_id': loan.id
                    }
                    interest_line.create(interest_line_data) if not interest_line else interest_line.write(
                        interest_line_data)

                # Penalty line
                penalty_line = self.env['loan.accrual.penalty'].search([
                    ('loan_accrual_id', '=', accrual.id or new_accrual.id),
                    ('date', '=', today_date)
                ])
                if not penalty_line.loan_accrual_id.is_accrual_created:
                    penalty_line_data = {
                        'loan_accrual_id': accrual.id or new_accrual.id,
                        'amount_due': loan.amount_due or 0.0,
                        'penalty_rate': loan.penalty_percent or 0.0,
                        'date': today_date,
                        'penalty_amount': round(daily_penalty, 2),
                        'loan_line_id': penalty_accrue_line.id,
                        'loan_id': loan.id
                    }
                    penalty_line.create(penalty_line_data) if not penalty_line else penalty_line.write(penalty_line_data)

                if accrual:
                    accrual.write({'is_accrual_created': True})
                if new_accrual:
                    new_accrual.write({'is_accrual_created': True})
                if loan:
                    loan.write({'is_accrual_created': True})

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
                'name': 'Loan Robots-->Accrual Creation',
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

        if loan_data:
            output = BytesIO()
            workbook = xlsxwriter.Workbook(output, {'in_memory': True})
            worksheet = workbook.add_worksheet()

            worksheet.set_column('A:A', 30)
            worksheet.set_column('B:B', 35)
            worksheet.set_column('C:C', 35)
            worksheet.set_column('D:D', 35)
            worksheet.set_column('E:E', 35)

            headers = ['Loan Name', 'Previous Interest Amount', 'Previous Penalty Amount',  'Current Interest Amount', 'Current Penalty Amount']
            for col_num, header in enumerate(headers):
                worksheet.write(0, col_num, header)

            # Write data rows
            for row_num, data in enumerate(loan_data, 1):
                worksheet.write(row_num, 0, data['loan_name'])
                worksheet.write(row_num, 1, data['interest_accrue_amount'])
                worksheet.write(row_num, 2, data['penalty_accrue_amount'])
                worksheet.write(row_num, 3, data['new_interest_accrue_amount'])
                worksheet.write(row_num, 4, data['new_penalty_accrue_amount'])

            workbook.close()

            # Save XLSX to binary field
            output.seek(0)
            xlsx_data = base64.b64encode(output.read())
            file_name = f'Loan_Accrual_Report_{today_date}.xlsx'

            # Create an attachment in Odoo
            attachment = self.env['ir.attachment'].create({
                'name': file_name,
                'type': 'binary',
                'datas': xlsx_data,
                'store_fname': file_name,
                'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            })

            folder_id = self.env['documents.folder'].search([('name', '=', 'Accrual Creation Reports')], limit=1)
            if not folder_id:
                folder_id = self.env['documents.folder'].create({'name': 'Accrual Creation Reports'})

            document_defaults = {'folder_id': folder_id.id}
            document = self.env['documents.document'].create(
                {'attachment_id': attachment.id, **document_defaults})

        


    @api.model
    def round_loan_accrual(self):
        accruals = self.env['loan.accrual'].search([])
        for acc in accruals:
            acc.rounding_button()


    @api.model
    def missing_loan_accrual_creation(self):
        curacao_tz = pytz.timezone('America/Curacao')
        utc_now = datetime.now(pytz.utc)
        curacao_now = utc_now.astimezone(curacao_tz)
        today_date = curacao_now.date()
        loans = self.env['account.loan'].search(
            [('expected_end_date', '>=', today_date), ('loan_migration_group', '=', 'Group 5'),
             ('state', '=', 'posted')])
        for loan in loans:
            interest_accrue_line = False
            loan_line = self.env['account.loan.line'].search([('loan_id', '=', loan.id), ('date', '>=', today_date)],
                                                             order='date', limit=1)
            previous_loan_line = False
            if loan_line.sequence > 1:
                previous_loan_line = self.env['account.loan.line'].search(
                    [('loan_id', '=', loan.id), ('sequence', '=', (loan_line.sequence - 1))], limit=1)
            if loan.start_date <= today_date and loan.first_payment_due >= today_date:
                interest_accrue_line = self.env['account.loan.line'].search(
                    [('loan_id', '=', loan.id), ('sequence', '=', 1)])
            else:
                interest_accrue_line = loan_line
            penalty_accrue_line = self.env['account.loan.line'].search(
                [('loan_id', '=', loan.id), ('invoice_ids', '!=', False), ('date', '<', today_date)],
                order='sequence desc', limit=1)
            accrual = self.env['loan.accrual'].search([('loan_id', '=', loan.id)])
            penalty_accrual_aug = accrual.loan_accrual_penalty_ids.filtered(
                lambda l: l.create_date.date().day == 27 and l.create_date.date().month == 8)
            interest_accrual_aug = accrual.loan_accrual_interest_ids.filtered(
                lambda l: l.create_date.date().day == 27 and l.create_date.date().month == 8)
            if penalty_accrual_aug:
                penalty_accrual_aug.unlink()
            if interest_accrual_aug:
                interest_accrual_aug.unlink()
            penalty_sum = sum(accrual.loan_accrual_penalty_ids.mapped('penalty_amount'))
            interest_sum = sum(accrual.loan_accrual_interest_ids.mapped('interest_amount'))
            penalty_accrue_line.write({'penalty_accrue': round(penalty_sum, 2)})
            interest_accrue_line.write({'interest_accrue': round(interest_sum, 2)})


    @api.model
    def updating_loan_accrual(self):
        accruals = self.env['loan.accrual'].search([('is_accrual_created', '!=', False)])
        loans = self.env['account.loan'].search([('is_accrual_created', '!=', False)])
        penalty_moves = self.env['account.move'].search([('is_penalty_created', '!=', False)])
        for move in penalty_moves:
            move.write({'is_penalty_created': False})
        for accrual in accruals:
            accrual.write({'is_accrual_created': False})
        for loan in loans:
            loan.write({'is_accrual_created': False})


class LoanAccrualInterest(models.Model):
    _name = 'loan.accrual.interest'
    _description = 'Loan Accrual Interest'

    loan_accrual_id = fields.Many2one('loan.accrual')
    loan_id = fields.Many2one('account.loan')
    loan_line_id = fields.Many2one('account.loan.line')
    currency_id = fields.Many2one('res.currency')
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


class LoanAccrualPenalty(models.Model):
    _name = 'loan.accrual.penalty'
    _description = 'Loan Accrual Penalty'

    loan_accrual_id = fields.Many2one('loan.accrual')
    loan_id = fields.Many2one('account.loan')
    loan_line_id = fields.Many2one('account.loan.line')
    currency_id = fields.Many2one('res.currency')
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
                seq = rec.loan_line_id.sequence + 1
                next_line = self.env['account.loan.line'].search(
                    [('sequence', '=', seq), ('loan_id', '=', rec.loan_id.id)])
                if rec.loan_line_id.date >= today_date:
                    rec.next_installment_date = rec.loan_line_id.date
                elif next_line:
                    rec.next_installment_date = next_line.date
                else:
                    rec.next_installment_date = False
            else:
                rec.next_installment_date = False
