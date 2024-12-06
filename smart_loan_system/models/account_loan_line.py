from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError, Warning
import logging
from dateutil.relativedelta import relativedelta as rd
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from datetime import datetime, timedelta
import time
import psycopg2
from psycopg2 import InterfaceError, OperationalError
import xlsxwriter
import base64
from io import BytesIO


_logger = logging.getLogger(__name__)


class AccountLoanLine(models.Model):
    _name = 'account.loan.line'
    _description = 'Annuity'
    _order = 'sequence asc, date desc'

    name = fields.Char(compute='_compute_name')
    loan_id = fields.Many2one('account.loan', required=True, readonly=True, ondelete='cascade')
    sequence = fields.Integer(required=True, readonly=True)
    date = fields.Date(required=True, readonly=True, help='Date when the payment will be accounted for')
    currency_id = fields.Many2one('res.currency', related='loan_id.currency_id')
    pending_principal_amount = fields.Monetary(currency_field='currency_id', readonly=True,
                                               help='Pending amount of the loan before the next payment')
    payment_amount = fields.Monetary(currency_field='currency_id', readonly=True,
                                     help='Total amount that will be paid (installment)')
    interests_amount = fields.Monetary(currency_field='currency_id', readonly=True,
                                       help='Amount from the the payment that will be set aside as interest')
    principal_amount = fields.Monetary(currency_field='currency_id',
                                       compute='_compute_amounts',
                                       help='Amount of the payment that will reduce the pending loan principal amount')
    final_pending_principal_amount = fields.Monetary(currency_field='currency_id',
                                                     compute='_compute_amounts',
                                                     help='Pending amount of the loan after the payment')
    invoice_ids = fields.One2many('account.move', inverse_name='loan_line_id')
    has_invoices = fields.Boolean(compute='_compute_has_invoices', string="Has Invoices?")
    paid_on = fields.Date('Paid on', compute='_get_paid_date')
    total_invoice_amount = fields.Monetary('Total Amount', compute='get_invoice_amt_detail', store=True)
    total_amount_due = fields.Monetary('Amount Due', compute='get_invoice_amt_detail', store=True)
    all_lines_has_invoice = fields.Boolean('All lines has invoice?', compute='check_all_line_has_invoice', store=True)
    emi = fields.Boolean("Is EMI?")
    is_down_payment = fields.Boolean("Is Down Payment?")
    is_last_payment = fields.Boolean("Is Last Payment")
    interest_accrue = fields.Monetary(currency_field='currency_id')
    penalty_accrue = fields.Monetary(currency_field='currency_id')
    is_extra_payment = fields.Boolean(default=False)

    @api.depends('invoice_ids')
    def check_all_line_has_invoice(self):
        """
        Check all line has invoice and based on that displyed Total invoice amt and Total due amt in line list view.
        :return:
        """
        for line in self:
            line.all_lines_has_invoice = False
            if line.has_invoices == True:
                line.all_lines_has_invoice = True

    @api.model
    def apply_penalty(self):
        loans = self.env['account.loan'].search([('state', '=', 'posted'), ('is_penalty', '=', True)])
        error_messages = []
        loan_data = []
        for loan in loans:
            try:
                loan_line = self.env['account.loan.line'].search([
                    ('loan_id', '=', loan.id),
                    ('invoice_ids', '!=', False),
                    ('date', '<', fields.Date.today())
                ], order='sequence desc', limit=1)

                if loan_line.invoice_ids and not loan_line.is_extra_payment:
                    for invoice in loan_line.invoice_ids.filtered(lambda l: l.move_type != 'entry'):
                        if loan.amount_due and not invoice.is_penalty_created:
                            penalty_amount = (loan_line.loan_id.penalty_percent / 100) / 360 * loan.amount_due

                            existing_penalty_line = invoice.invoice_line_ids.filtered(
                                lambda l: l.product_id == loan_line.loan_id.penalty_product_id and
                                          l.date == fields.Date.today()
                            )

                            if invoice.payment_state in ('partial', 'in_payment', 'paid'):
                                for line in invoice.line_ids:
                                    line.remove_move_reconcile()
                                # self.env.invalidate_all()

                            penalty_line = existing_penalty_line or invoice.invoice_line_ids.filtered(
                                lambda l: l.product_id == loan_line.loan_id.penalty_product_id
                            )

                            previous_penalty_amount = 0.0
                            previous_unpaid_amount = 0.0

                            loan_data.append({
                                'loan_name': loan.name,
                                'previous_penalty_amount': penalty_line.unpaid_amount or 0.0,
                                'previous_unpaid_amount': penalty_line.unpaid_amount or 0.0,
                                'current_penalty_amount': penalty_line.unpaid_amount + penalty_amount or 0.0,
                                'current_unpaid_amount': penalty_line.unpaid_amount + penalty_amount or 0.0,
                            })

                            if penalty_line:
                                previous_penalty_amount = penalty_line.unpaid_amount
                                previous_unpaid_amount = penalty_line.unpaid_amount
                                penalty_line.write({
                                    'quantity': 1.0,
                                    'price_unit': round(penalty_amount + previous_penalty_amount, 2),
                                    'unpaid_amount': round(penalty_amount + previous_unpaid_amount, 2),
                                    'date': fields.Date.today(),
                                })
                            else:
                                invoice.invoice_line_ids = [(0, 0, {
                                    'product_id': loan_line.loan_id.penalty_product_id.id,
                                    'name': loan_line.loan_id.penalty_product_id.name,
                                    'quantity': 1.0,
                                    'price_unit': round(penalty_amount + previous_penalty_amount, 2),
                                    'unpaid_amount': round(penalty_amount + previous_unpaid_amount, 2),
                                    'move_id': invoice.id,
                                    'tax_ids': False,
                                    'date': fields.Date.today(),
                                })]
                            invoice.write({'is_penalty_created': True})
                            ref_move_ids = self.env['account.move'].search([('ref', '=', invoice.name)]).ids
                            write_off_invoices = self.env['account.move'].search(
                                [('reversed_entry_id', '=', invoice.id)])

                            if write_off_invoices:
                                for wr_inv in write_off_invoices:
                                    ref_move_ids.append(wr_inv.id)

                            line_ids_for_reconcile = self.env['account.move.line'].search(
                                [('move_id', 'in', ref_move_ids)]
                            ).filtered(lambda l: l.debit == 0).ids

                            credit_ids = self.env['account.partial.reconcile'].search([]).mapped(
                                'credit_move_id').ids

                            if line_ids_for_reconcile:
                                for line_id in line_ids_for_reconcile:
                                    line = self.env['account.move.line'].browse(line_id)
                                    if line_id not in credit_ids and line.move_id.state == 'posted':
                                        invoice.js_assign_outstanding_line(line_id)
                # self.env.cr.commit()
            except (Exception, OperationalError, InterfaceError, psycopg2.Error, UserError) as e:
                if 'cursor already closed' in str(e):
                    self.env.cr.reset()
                    time.sleep(5)
                    self.env.cr.rollback()
                else:
                    error_message = f"Error in 'Loan Penalty Application' for Loan {loan.name}: {str(e)}"
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

        if loan_data:
            output = BytesIO()
            workbook = xlsxwriter.Workbook(output, {'in_memory': True})
            worksheet = workbook.add_worksheet()

            worksheet.set_column('A:A', 30)
            worksheet.set_column('B:B', 35)
            worksheet.set_column('C:C', 35)
            worksheet.set_column('D:D', 35)
            worksheet.set_column('E:E', 35)

            headers = ['Loan Name', 'Previous Penalty Amount', 'Previous Unpaid Amount',  'Current Penalty Amount', 'Current Unpaid Amount']
            for col_num, header in enumerate(headers):
                worksheet.write(0, col_num, header)

            # Write data rows
            for row_num, data in enumerate(loan_data, 1):
                worksheet.write(row_num, 0, data['loan_name'])
                worksheet.write(row_num, 1, data['previous_penalty_amount'])
                worksheet.write(row_num, 2, data['previous_unpaid_amount'])
                worksheet.write(row_num, 3, data['current_penalty_amount'])
                worksheet.write(row_num, 4, data['current_unpaid_amount'])

            workbook.close()

            # Save XLSX to binary field
            output.seek(0)
            xlsx_data = base64.b64encode(output.read())
            file_name = f'Penalty_Application_Report_{fields.Date.today()}.xlsx'

            # Create an attachment in Odoo
            attachment = self.env['ir.attachment'].create({
                'name': file_name,
                'type': 'binary',
                'datas': xlsx_data,
                'store_fname': file_name,
                'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            })

            folder_id = self.env['documents.folder'].search([('name', '=', 'Penalty Application Report')], limit=1)
            if not folder_id:
                folder_id = self.env['documents.folder'].create({'name': 'Penalty Application Report'})

            document_defaults = {'folder_id': folder_id.id}
            document = self.env['documents.document'].create(
                {'attachment_id': attachment.id, **document_defaults})



    @api.depends('invoice_ids.amount_total')
    def get_invoice_amt_detail(self):
        """
        Calculate Total Invoice amount and Total Due Amount of line invoice.
        :return:
        """
        for line in self:
            if line.invoice_ids:
                total_amt = amt_due = 0
                for invoice in line.invoice_ids:
                    total_amt += invoice.amount_total
                    amt_due += invoice.amount_residual
                line.total_invoice_amount = total_amt
                line.total_amount_due = amt_due

    # @api.multi
    @api.depends('invoice_ids.state')
    def _get_paid_date(self):
        """
        Update date on 'paid_on' when invoice fully paid.
        :return:
        """
        payment_obj = self.env['account.payment']
        for record in self:
            if not record.paid_on and record.invoice_ids:
                for invoice in record.invoice_ids:
                    # payment_ids = payment_obj.search([('reconciled_invoice_ids', 'in', invoice.ids)])
                    payment_id = payment_obj.search([('ref', '=', invoice.name)], order='create_date desc', limit=1)
                    if payment_id and invoice.amount_residual == 0:
                        # list_payment = payment_ids.ids
                        # list_payment.sort()
                        # last_payment = payment_obj.browse(list_payment[-1])
                        record.paid_on = payment_id.date
                    elif record.invoice_ids[0].custom_payment_id:
                        record.paid_on = record.invoice_ids[0].custom_payment_id.date

    @api.depends('invoice_ids')
    def _compute_has_invoices(self):
        """
        Update has_invoices flag if any invoice is created for line.
        :return:
        """
        for record in self:
            record.has_invoices = bool(record.invoice_ids)

    @api.depends('loan_id.name', 'sequence')
    def _compute_name(self):
        """
        Update loan line name based on loan name and sequence.
        :return:
        """
        for record in self:
            record.name = '%s-%d' % (record.loan_id.name, record.sequence)

    @api.depends('payment_amount', 'interests_amount',
                 'pending_principal_amount')
    def _compute_amounts(self):
        """
        Calculate principal_amount, final_pending_principal_amount and payment_amount.
        :return:
        """
        for rec in self:
            rec.final_pending_principal_amount = (
                    rec.pending_principal_amount - rec.payment_amount +
                    rec.interests_amount
            )
            rec.principal_amount = rec.payment_amount - rec.interests_amount
            if rec.payment_amount > rec.pending_principal_amount:
                rec.principal_amount = rec.pending_principal_amount
                rec.payment_amount = rec.principal_amount + rec.interests_amount

    def compute_amount(self):
        """
        Computes the payment amount
        :return: Amount to be payed on the annuity
        """
        return self.loan_id.fixed_amount

    def check_amount(self):
        """Recompute amounts if the annuity has not been processed"""
        if self.invoice_ids:
            raise UserError(_(
                'Amount cannot be recomputed if invoices exists '
                'already'
            ))
        if not self.loan_id.round_on_end:
            if self.loan_id.interest_type == 'simple':
                self.interests_amount = self.loan_id.fixed_loan_amount * self.loan_id.rate_period / 100
                self.payment_amount = self.currency_id.round(self.compute_amount())
                if self.loan_id.loan_type == 'interest_loan':
                    self.payment_amount = self.loan_id.rate / 100 / 360 * self.pending_principal_amount * (
                        (self.loan_id.first_payment_due - self.loan_id.start_date).days)
                    self.principal_amount = 0.0
                    self.interests_amount = self.payment_amount
                    if self.is_last_payment:
                        self.payment_amount = self.loan_id.fixed_loan_amount + self.interests_amount
                if self.pending_principal_amount == self.loan_id.fixed_loan_amount and self.loan_id.loan_type == 'amortizing_loan':
                    self.interests_amount = self.loan_id.rate / 100 / 360 * self.pending_principal_amount * (
                        (self.loan_id.first_payment_due - self.loan_id.start_date).days)
                if self.loan_id.loan_type == 'amortizing_loan' and self.is_last_payment:
                    self.payment_amount = self.principal_amount + self.interests_amount
            else:
                self.interests_amount = self.currency_id.round(
                    self.pending_principal_amount * self.loan_id.rate_period / 100)
                self.payment_amount = self.currency_id.round(self.compute_amount())
                if self.loan_id.loan_type == 'interest_loan':
                    self.payment_amount = self.loan_id.rate / 100 / 360 * self.pending_principal_amount * (
                        (self.loan_id.first_payment_due - self.loan_id.start_date).days)
                    self.principal_amount = 0.0
                    self.interests_amount = self.payment_amount
                    if self.is_last_payment:
                        self.payment_amount = self.loan_id.fixed_loan_amount + self.interests_amount
                if self.pending_principal_amount == self.loan_id.fixed_loan_amount and self.loan_id.loan_type == 'amortizing_loan':
                    self.interests_amount = self.loan_id.rate / 100 / 360 * self.pending_principal_amount * (
                        (self.loan_id.first_payment_due - self.loan_id.start_date).days)
                if self.loan_id.loan_type == 'amortizing_loan' and self.is_last_payment:
                    self.payment_amount = self.principal_amount + self.interests_amount
        else:
            if self.loan_id.interest_type == 'simple':
                self.interests_amount = self.loan_id.fixed_loan_amount * self.loan_id.rate_period / 100
                self.payment_amount = self.compute_amount()
                if self.loan_id.loan_type == 'interest_loan':
                    self.payment_amount = self.loan_id.rate / 100 / 360 * self.pending_principal_amount * (
                        (self.loan_id.first_payment_due - self.loan_id.start_date).days)
                    self.principal_amount = 0.0
                    self.interests_amount = self.payment_amount
                    if self.is_last_payment:
                        self.payment_amount = self.loan_id.fixed_loan_amount + self.interests_amount
                if self.pending_principal_amount == self.loan_id.fixed_loan_amount and self.loan_id.loan_type == 'amortizing_loan':
                    self.interests_amount = self.loan_id.rate / 100 / 360 * self.pending_principal_amount * (
                        (self.loan_id.first_payment_due - self.loan_id.start_date).days)
                if self.loan_id.loan_type == 'amortizing_loan' and self.is_last_payment:
                    self.payment_amount = self.principal_amount + self.interests_amount

            else:
                self.interests_amount = (
                        self.pending_principal_amount * self.loan_id.rate_period / 100)
                self.payment_amount = self.compute_amount()

                if self.loan_id.loan_type == 'interest_loan':
                    self.payment_amount = self.loan_id.rate / 100 / 360 * self.pending_principal_amount * (
                        (self.loan_id.first_payment_due - self.loan_id.start_date).days)
                    self.principal_amount = 0.0
                    self.interests_amount = self.payment_amount
                    if self.is_last_payment:
                        self.payment_amount = self.loan_id.fixed_loan_amount + self.interests_amount
                if self.pending_principal_amount == self.loan_id.fixed_loan_amount and self.loan_id.loan_type == 'amortizing_loan':
                    self.interests_amount = self.loan_id.rate / 100 / 360 * self.pending_principal_amount * (
                        (self.loan_id.first_payment_due - self.loan_id.start_date).days)
                if self.loan_id.loan_type == 'amortizing_loan' and self.is_last_payment:
                    self.payment_amount = self.principal_amount + self.interests_amount
            if self.payment_amount < self.interests_amount:
                self.principal_amount = self.payment_amount - self.interests_amount

    # @api.multi
    def _get_display_price(self, product):
        partner = self.loan_id.partner_id
        pricelist = partner.property_product_pricelist
        if pricelist.discount_policy == 'with_discount':
            return product.with_context(pricelist=pricelist.id).lst_price
        final_price, rule_id = pricelist.get_product_price_rule(product, 1.0, partner)
        context_partner = dict(self.env.context, partner_id=partner.id, date=fields.Datetime.now)
        base_price, currency_id = self.with_context(context_partner)._get_real_price_currency(product, rule_id, 1.0,
                                                                                              product.uom_id,
                                                                                              pricelist.id)
        return max(base_price, final_price)

    def invoice_line_vals(self):
        vals = list()
        loan = self.loan_id
        config_param_obj = self.env['ir.config_parameter'].sudo()
        product_obj = self.env['product.product']

        principal_prod_id = config_param_obj.get_param('ae_loan_manag.principal_prod_id')
        principal_prod = product_obj.browse(int(principal_prod_id))

        interest_prod_id = config_param_obj.get_param('ae_loan_manag.interest_prod_id')
        interest_prod = product_obj.browse(int(interest_prod_id))

        bonaire_principal_prod_id = config_param_obj.get_param('ae_loan_manag.bonaire_principal_prod_id')
        bonaire_principal_prod = product_obj.browse(int(bonaire_principal_prod_id))

        bonaire_interest_prod_id = config_param_obj.get_param('ae_loan_manag.bonaire_interest_prod_id')
        bonaire_interest_prod = product_obj.browse(int(bonaire_interest_prod_id))

        ground_lease_prod_id = config_param_obj.get_param('ae_loan_manag.ground_lease_product_id')
        ground_lease_prod = product_obj.browse(int(bonaire_interest_prod_id))

        income_acc_id = config_param_obj.sudo().get_param('ae_loan_manag.income_acc_id')
        if not income_acc_id:
            raise Warning(_("Please Configure Income Account from Loans -> Configurations -> Settings!"))

        if not principal_prod_id:
            raise Warning(_("Please configure 'Principal Product' from Loan -> Configurations -> Account"
                            " Setting!"))

        if not interest_prod_id:
            raise Warning(_("Please configure 'Interest Product' from Loan -> Configurations -> Account"
                            " Setting!"))

        if not ground_lease_prod_id:
            raise Warning(_("Please configure 'Ground Lease Product' from Loan -> Configurations -> Account"
                            " Setting!"))

        if loan.bonaire_principal_amount > 0.0:
            insurance_product = loan.bonaire_principal_prod_id or bonaire_principal_prod
            vals.append({
                'product_id': insurance_product.id,
                'name': insurance_product.name,
                'quantity': 1,
                'price_unit': loan.bonaire_principal_amount,
                'unpaid_amount': 1 * loan.bonaire_principal_amount,

            })

        if loan.bonaire_interest_amount > 0.0:
            tax_product = loan.bonaire_interest_prod_id or bonaire_interest_prod
            vals.append({
                'product_id': tax_product.id,
                'name': tax_product.name,
                'quantity': 1,
                'price_unit': loan.bonaire_interest_amount,
                'unpaid_amount': 1 * loan.bonaire_interest_amount,

            })
        if self.principal_amount > 0.0:
            dict = {
                'quantity': 1,
                'price_unit': self.principal_amount,
                'product_id': principal_prod.id,
                'name': principal_prod.name,
                'unpaid_amount': 1 * self.principal_amount,
            }

            vals.append(dict)
        if self.interests_amount > 0.0:
            dict_interest = {
                'quantity': 1,
                'price_unit': self.interests_amount,
                'product_id': interest_prod.id,
                'name': interest_prod.name,
                'unpaid_amount': 1 * self.interests_amount,
            }

            vals.append(dict_interest)

        if loan.is_ground_lease and loan.ground_lease_amount > 0.0:
            ground_lease_product = loan.ground_lease_product_id or ground_lease_prod
            vals.append({
                'product_id': ground_lease_product.id,
                'name': ground_lease_product.name,
                'quantity': 1,
                'price_unit': loan.ground_lease_amount,
                'unpaid_amount': 1 * loan.ground_lease_amount,

            })
        return vals

    # @api.multi
    def create_invoice(self):
        res = []
        config_param_obj = self.env['ir.config_parameter'].sudo()
        acc_rec_id = config_param_obj.get_param('ae_loan_manag.acc_rec_id')
        if not acc_rec_id:
            raise Warning(_("Please Configure Account receivable from Loan -> Configurations -> Account Setting!"))
        acc_rec = self.env['account.account'].browse(int(acc_rec_id))

        loan_jou_id = config_param_obj.get_param('ae_loan_manag.loan_jou_id')
        if not loan_jou_id:
            raise Warning(_('Please configure Loan Journal from Loan -> Configurations -> Account Settings!'))
        loan_jou = self.env['account.journal'].browse(int(loan_jou_id))

        if acc_rec and loan_jou:
            for rec in self:
                inv_obj = self.env['account.move']
                due_date = datetime.strptime(str(rec.date), DF).date()
                invoice_date = due_date - rd(days=12)
                inv_data = {
                    'loan_line_id': rec.id,
                    'loan_id': rec.loan_id.id,
                    #                    'account_id': acc_rec and acc_rec.id or False,
                    'partner_id': rec.loan_id.partner_id.id,
                    'currency_id': self.loan_id.currency_id.id if self.loan_id.currency_id else (
                        self.loan_id.company_id.currency_id.id if self.loan_id.company_id.currency_id else False),
                    'move_type': 'out_invoice',
                    'invoice_date_due': due_date,
                    'invoice_date': invoice_date,
                    'journal_id': loan_jou and loan_jou.id or False,
                    'company_id': self.env.user.company_id.id,

                    'invoice_line_ids': [(0, 0, vals) for vals in
                                         self.invoice_line_vals()]
                }
                inv_id = inv_obj.create(inv_data)
                if inv_id:
                    inv_id.emi = True
                    inv_id.with_context(from_validate=True).action_post()
                    if rec.loan_id.is_straight_through:
                        selected_lines = inv_id.invoice_line_ids.filtered(
                            lambda line: line.display_type == 'product' and line.fully_paid == False)
                        total_amount = sum(selected_lines.mapped('unpaid_amount'))
                        move = inv_id
                        convert_value = move.currency_id._convert(total_amount, inv_id.currency_id, inv_id.company_id,
                                                                  inv_id.invoice_date)
                        for line in selected_lines:
                            line.write({'select': True})
                        journal = rec.loan_id.payment_journal_id
                        payment_method = journal.inbound_payment_method_line_ids[0].payment_method_id
                        payment_method_line = self.env['account.payment.method.line'].search(
                            [('journal_id', '=', journal.id), ('payment_method_id', '=', payment_method.id)])
                        register_pay_wiz = self.env['account.payment.register'].sudo().with_context(
                            active_model='account.move', active_ids=inv_id.ids).create({'journal_id': journal.id,
                                                                                        'partner_id': inv_id.partner_id.id,
                                                                                        'amount': convert_value,
                                                                                        'currency_id': inv_id.currency_id.id,
                                                                                        'payment_method_line_id': payment_method_line.id if payment_method_line else False,
                                                                                        'payment_date': fields.Date.today(),
                                                                                        'partner_bank_id': journal.bank_account_id.id if journal.bank_account_id else False,
                                                                                        'communication': rec.loan_id.old_loan_name if rec.loan_id.is_straight_through else rec.name,
                                                                                        'selected_amount': convert_value,
                                                                                        'move_id': inv_id.id,
                                                                                        'inv_line_ids': [
                                                                                            (6, 0, selected_lines.ids)]
                                                                                        })
                        register_pay_wiz.action_create_payments()

                res.append(inv_id.id)

            return

    # @api.multi
    def view_account_values(self):
        """Shows the invoice if it is a leasing or the move if it is a loan"""
        self.ensure_one()
        return self.view_account_invoices()

    # @api.multi
    def view_process_values(self):
        self.ensure_one()
        amount = 0
        config_param_obj = self.env['ir.config_parameter'].sudo()
        principal_prod = config_param_obj.get_param('ae_loan_manag.land_contract_principal_id')
        interest_prod = config_param_obj.get_param('ae_loan_manag.land_contract_interest_id')
        if principal_prod and interest_prod:
            for invoice in self.invoice_ids:
                for invoice_line in invoice.invoice_line_ids:
                    if invoice_line.product_id and (invoice_line.product_id.id == int(principal_prod) or \
                                                    invoice_line.product_id.id == int(interest_prod)):
                        amount += invoice_line.price_subtotal
        if amount < self.payment_amount:
            inv_obj = self.create_invoice()
            self.loan_id.write({'line_inv_ids': [(4, self.invoice_ids.id)]})
            loan_name = self.loan_id.name
            invoice_name = self.invoice_ids[0].name if self.invoice_ids else None
            if self.invoice_ids[0].custom_payment_id:
                self.invoice_ids[0].custom_payment_id.action_approve()
                self.write({'paid_on': self.invoice_ids[0].custom_payment_id.date})
            return self.view_account_values()

    # @api.multi
    def view_account_invoices(self):
        self.ensure_one()
        action = self.env.ref('account.action_move_out_invoice_type')
        result = action.read()[0]
        result['context'] = {
            'default_loan_line_id': self.id,
            'default_loan_id': self.loan_id.id
        }
        result['domain'] = [
            ('loan_line_id', '=', self.id),
            ('move_type', '=', 'out_invoice')
        ]
        if len(self.invoice_ids) == 1:
            res = self.env.ref('account.view_move_form')
            result['views'] = [(res and res.id or False, 'form')]
            result['res_id'] = self.invoice_ids.id
        return result
