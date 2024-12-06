# -*- coding: utf-8 -*-

from odoo import api, models, fields, _
from odoo.exceptions import UserError, ValidationError



class LoanWiard(models.TransientModel):
    _name = 'account.loan.wizard'
    _description = 'Account Loan Wizard'

    new_create_date = fields.Date(string="Date", required=True)

    def get_report(self):
        name = 'EOD Report' + ' ' + str(self.new_create_date)
        get_attachment = self.env['ir.attachment'].search(
            [('res_model', '=', 'documents.document'), ('name', '=', name)], limit=1)
        if not get_attachment:
            raise UserError(_("No Report Found for that day."))
        action = {
            'type': 'ir.actions.act_url',
            'url': "web/content/?model=ir.attachment&id=" + str(
                get_attachment.id) + "&filename_field=name&field=datas&download=true&name=" + get_attachment.name,
            'target': 'self'
        }
        return action


class AccountLoanReport(models.AbstractModel):
    _name = 'report.smart_loan_system.account_loan_reports'
    _description = 'Account Loan Reports'
    _inherit = 'report.report_xlsx.abstract'

    def last_payment_date(self, loan):
        return self.env['account.payment.history'].search([('loan_id', '=', loan), ('state', '=', 'running')], limit=1,
                                                          order='payment_date asc').payment_date

    def outstanding_data(self, loan):
        disbursement_acc_id = self.env['ir.config_parameter'].sudo().get_param('ae_loan_manag.disbursement_acc_id')

        if not disbursement_acc_id:
            raise ValueError("Disbursement account ID is not set in the configuration.")
        try:
            disbursement_acc_id = int(disbursement_acc_id)
        except ValueError:
            raise ValueError("Disbursement account ID in configuration is not a valid integer.")
        move_lines = self.env['account.move.line'].search([
            ('move_id.loan_id', '=', loan),
            ('account_id', '=', disbursement_acc_id)
        ])
        total_debit = sum(move_lines.mapped('debit'))

        return total_debit

    def installment_amount(self, record):
        if record.line_ids:
            line = max(record.line_ids, key=lambda d: d.sequence)
            return line.payment_amount
        else:
            return 0

    def _collateral_amount(self, record):
        total_amount = sum(
            self.env['loan.collateral'].search([('customer_id', '=', record.partner_id.id)]).mapped('amount')) or 0
        return total_amount

    def generate_xlsx_report(self, workbook, data, obj):
        sheet = workbook.add_worksheet('Report')
        format1 = workbook.add_format({'font_size': 15})
        format2 = workbook.add_format({'font_size': 10, 'bold': True, 'bg_color': '#D3D3D3'})
        format3 = workbook.add_format({'font_size': 10})
        format5 = workbook.add_format({'font_size': 10})
        format4 = workbook.add_format({'font_size': 10, 'top': 1, 'bottom': 6})
        format1.set_align('center')
        format2.set_align('center')
        format5.set_align('center')
        ksh = workbook.add_format({'font_size': 10, 'bold': True, 'bg_color': '#D3D3D3'})
        ksh.set_align('center')
        table_headers = [
            'Customer',
            'Loan Name',
            'Old Loan Name',
            'Customer Number',
            'Currency',
            'Loan Amount (Principle)',
            'Interest Paid',
            'Start Date (Opening Date)',
            'Loan Product',
            'Maturity Date',
            'Days Due (Past Due Days)',
            'Rate ( Interest Rate)',
            'State (status)',
            'Officer',
            'Country Name',
            'Total Amount Due (Past_Due_amount)',
            'Principal Balance',
            'ACCOUNT',
            'LAST_PMT_DATE',
            'AVG_BALANCE',
            'INDUSTRY_TYPE',
            'ANNUITY_PAYMENT',
            'Outstanding Principal',
            'Fire Insurance Amount',
            'Fire Insurance Due',
            'Life Insurance amount',
            'Penalty Due',
            'Unpaid Principal',
            'Unpaid Interest',
            'Collateral Amount',
            'Due life insurance',
            'MTD Interest ',
            'YTD Interest'
        ]
        col = 0
        row = 0
        for header in table_headers:
            sheet.set_column(col, 1, 31)
            sheet.write(row, col, header, format2)
            col += 1
        row += 1
        col = 0
        for record in obj:
            # record = self.env['account.loan'].browse(record)
            if record.state == 'draft':
                state = 'IN PROGRESS'
            elif record.state == 'posted':
                state = 'ACTIVE'
            elif record.state == 'cancelled':
                state = 'WRITTEN-OFF'
            else:
                state = 'CLOSED'
            if record:
                sheet.write(row, col + 0, record.partner_id.name, format3)
                sheet.write(row, col + 1, record.name, format3)
                sheet.write(row, col + 2, record.old_loan_name, format3)
                sheet.write(row, col + 3, record.kyc_customer_number, format3)
                sheet.write(row, col + 4, record.currency_id.name, format3)
                sheet.write(row, col + 5, record.loan_amount, format3)
                sheet.write(row, col + 6, round(record.total_interest_balance, 2), format3)
                sheet.write(row, col + 7, record.start_date.strftime("%d/%m/%Y") if record.start_date else '', format3)
                sheet.write(row, col + 8, record.product_id.name, format3)
                sheet.write(row, col + 9,
                            record.expected_end_date.strftime("%d/%m/%Y") if record.expected_end_date else '', format3)
                sheet.write(row, col + 10, record.days_past_due, format3)
                sheet.write(row, col + 11, record.rate, format3)
                sheet.write(row, col + 12, state, format3)
                sheet.write(row, col + 13, record.user_id.name if record.user_id else '', format3)
                sheet.write(row, col + 14, record.country_id.name, format3)
                sheet.write(row, col + 15, record.amount_due, format3)
                sheet.write(row, col + 16, round(record.outstanding_bal, 2), format3)
                sheet.write(row, col + 17, record.name, format3)
                payment_date = self.last_payment_date(record.id)
                sheet.write(row, col + 18, payment_date.strftime("%d/%m/%Y") if payment_date else '', format3)
                outstanding_amt = self.outstanding_data(record.id)
                sheet.write(row, col + 19, round(outstanding_amt, 2), format3)
                sheet.write(row, col + 20, record.kyc_type if record.kyc_type else '', format3)
                payment_amt = self.installment_amount(record)
                sheet.write(row, col + 21, round(payment_amt, 2), format3)
                sheet.write(row, col + 22, round(record.outstanding_bal, 2), format3)
                sheet.write(row, col + 23, round(record.tax_sale_price, 2), format3)
                sheet.write(row, col + 24, round(record.total_unpaid_fire_insurance, 2), format3)
                sheet.write(row, col + 25, round(record.insurance_sale_price, 2), format3)
                sheet.write(row, col + 26, round(record.total_penalties, 2), format3)
                sheet.write(row, col + 27, round(record.total_unpaid_principal, 2), format3)
                sheet.write(row, col + 28, round(record.total_unpaid_interest, 2), format3)
                collateral_amt = self._collateral_amount(record)
                sheet.write(row, col + 29, round(collateral_amt, 2), format3)
                sheet.write(row, col + 30, round(record.total_unpaid_life_insurance, 2), format3)
                sheet.write(row, col + 31, record.monthly_interest_accrue, format3)
                sheet.write(row, col + 32, record.yearly_interest_accrue, format3)

                row += 1
            else:
                row += 1
