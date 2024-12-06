from odoo import api, fields, models, _
from dateutil.relativedelta import relativedelta
import logging
from odoo.exceptions import UserError, Warning
import psycopg2
from psycopg2 import InterfaceError, OperationalError
import time
import xlsxwriter
import base64
from io import BytesIO


_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = 'account.move'

    loan_line_id = fields.Many2one('account.loan.line', readonly=False, ondelete='restrict')
    loan_id = fields.Many2one('account.loan', readonly=True, ondelete='restrict')
    partner = fields.Many2one('res.partner', related='loan_id.partner_id', store=True, string="Partner")
    reconcile_amount = fields.Float()
    custom_payment_id = fields.Many2one('account.payment', tracking=True, string='Payment')
    custom_payment_status = fields.Selection(related='custom_payment_id.state', string='Payment Status')
    custom_payment_state = fields.Selection(
        [('draft', 'Draft'), ('waiting', 'Waiting For Approval'), ('reject', 'Reject'), ('posted', 'Posted'),
         ('cancel', 'Cancelled')], string='Payment State', tracking=True)
    cancel_outstanding_receipt_id = fields.Many2one('account.payment', tracking=True)
    cancel_receipt_id = fields.Many2one('account.payment', tracking=True, string='Cancel Outstanding Receipt')
    cancel_receipt_name = fields.Char()
    writeoff_reverse_entry_id = fields.Many2one('account.move', tracking=True, string='Write-Off Reverse Entry')
    is_penalty_created = fields.Boolean(default=False)

    @api.model
    def create(self, vals_list):
        if isinstance(vals_list, dict):
            vals_list = [vals_list]

        res = super(AccountMove, self).create(vals_list)

        if self.env.context.get('import_file'):
            for record in res:
                if record.move_type == 'entry':
                    self._post_import_message(record)

        return res

    def _post_import_message(self, res):
        message = "Journal Entry Created"
        res.message_post(body=message)

    def write(self, values):
        res = super(AccountMove, self).write(values)
        if values.get('line_ids') and len(values.get('line_ids')) >= 2 and values.get('line_ids')[1][2] and values.get('line_ids')[1][2].get('partner_id') and self.move_type == 'entry' and self.statement_line_id.is_import_file:
            author_id = False
            if self.statement_line_id.is_import_file:
                author_id = self.env['res.partner'].search([('active', '=', False), ('name', '=', 'OdooBot')])
            else:
                author_id = self.env.user.partner_id

            partner_obj = self.env['res.partner'].search([('id', '=', values.get('line_ids')[1][2].get('partner_id'))])
            new_description = str(partner_obj.name).replace('[',
                                                        '').replace(
                ']',
                '').replace(
                "'", "")
            self.message_post(
                body="<b>None</b> <i class='fa fa-long-arrow-right mx-1 text-600' title='Changed' role='img' aria-label='Changed'></i> %s (Partner)" % (
                    new_description),
                author_id=author_id.id, )
        if 'cancel_receipt_id' in values:
            payment = self.env['account.payment'].browse(values.get('cancel_receipt_id'))
            msg = _(
                "Cancel Outstanding Receipt %s updated",
                payment._get_html_link(title=f"#{payment.name}")
            )
            if self:
                self._message_log(
                    body=msg,
                )
        if 'writeoff_reverse_entry_id' in values:
            move = self.env['account.move'].browse(values.get('writeoff_reverse_entry_id'))
            msg = _(
                "Write-Off Reverse Entry %s updated",
                move._get_html_link(title=f"#{move.name}")
            )
            if self:
                self._message_log(
                    body=msg,
                )
        if 'custom_payment_id' in values:
            payment = self.env['account.payment'].browse(values.get('custom_payment_id'))
            msg = _(
                "Payment  has been created, to view payment please click this link %s",
                payment._get_html_link(title=f"#{payment.name}")
            )
            if self:
                self._message_log(
                    body=msg,
                )
        if 'custom_payment_state' in values:
            if values.get('custom_payment_state') == 'posted':
                payment = self.env['account.payment'].search([('ref', '=', self.name)], order='id desc', limit=1)
                msg = _(
                    "Payment has been approved, to view payment please click this link %s",
                    payment._get_html_link(title=f"#{payment.name}")
                )
                if self:
                    self._message_log(
                        body=msg,
                    )
            if values.get('custom_payment_state') == 'reject':
                payment = self.env['account.payment'].search([('ref', '=', self.name)], order='id desc', limit=1)
                msg = _(
                    "Payment has been rejected, to view payment please click this link %s",
                    payment._get_html_link(title=f"#{payment.name}")
                )
                if self:
                    self._message_log(
                        body=msg,
                    )
        return res

    @api.model
    def automatic_transfer_on_reconciliation(self):
        loans = self.env['account.loan'].search([('state', '!=', 'draft')])
        error_messages = []
        transfer_data = []
        for loan in loans:
            try:
                all_transfer_entries = []
                all_reversal_moves = []
                invoices = self.env['account.move'].search([('loan_id', '=', loan.id), ('move_type', '!=', 'entry')])
                for inv in invoices:
                    if inv and inv.loan_id and inv.loan_id.old_loan_name:
                        payments = self.env['account.payment'].search(
                            ['|', ('ref', '=', inv.name), ('ref', '=', inv.loan_id.old_loan_name)])
                        for pay in payments:
                            entries = self.env['account.move'].search(
                                [('move_type', '=', 'entry'), ('loan_id', '=', loan.id),
                                 ('is_automatic_entry', '=', True), ('id', 'in', pay.transfer_entry_ids.ids)])
                            if pay.is_reconciled and pay.reconciled_statement_line_ids and not pay.transfer_entry_ids and pay.state == 'posted':
                                company_currency = self.env.company.currency_id
                                rate = 1.0
                                if inv.currency_id != company_currency:
                                    rate_line = self.env['res.currency.rate'].search(
                                        [('currency_id', '=', inv.currency_id.id)],
                                        order='name desc', limit=1)
                                    rate = rate_line.inverse_company_rate
                                if pay.payment_inv_line:
                                    transfer_entries_list = []
                                    for pay_inv_line in pay.payment_inv_line:
                                        name = 'Transfer' + ' ' + pay_inv_line.move_line_id.account_id.name + '(' + str(
                                            (round(
                                                pay_inv_line.paid_amount * rate,
                                                2))) + ')' + ' ' + 'From Loan' + ' ' + loan.name
                                        entry = entries.filtered(
                                            lambda l: l.ref == name and not l.is_mistaken_reconcile)
                                        if pay_inv_line.move_line_id.account_id.transfer_account_id and pay_inv_line.move_line_id.account_id.transfer_type != 'no' and pay_inv_line.move_line_id.product_id.automatic_transfer and not entry:
                                            transfer_entry = self.env['account.move'].create({
                                                'journal_id': inv.journal_id.id or False,
                                                'loan_id': loan.id or False,
                                                'ref': name,
                                                'date': fields.date.today(),
                                                'move_type': 'entry',
                                                'currency_id': inv.currency_id.id,
                                                'partner_id': inv.partner_id.id or False,
                                                'is_automatic_entry': True,
                                            })
                                            lines = [{
                                                'account_id': pay_inv_line.move_line_id.account_id.transfer_account_id.id,
                                                'partner_id': inv.partner_id.id or False,
                                                'debit': 0,
                                                'credit': (round(pay_inv_line.paid_amount * rate, 2)),
                                                'amount_currency': -1 * (round(pay_inv_line.paid_amount, 2)),
                                                'name': inv.name,
                                                'date': fields.date.today(),
                                                'ref': name,
                                                'currency_id': inv.currency_id.id,
                                            }, {
                                                'account_id': pay_inv_line.move_line_id.account_id.id,
                                                'partner_id': inv.partner_id.id or False,
                                                'debit': (round(pay_inv_line.paid_amount * rate, 2)),
                                                'credit': 0,
                                                'amount_currency': (round(pay_inv_line.paid_amount, 2)),
                                                'name': inv.name,
                                                'date': fields.date.today(),
                                                'ref': name,
                                                'currency_id': inv.currency_id.id,
                                            }]
                                            transfer_entry.line_ids = [(0, 0, val) for val in lines]
                                            transfer_entry.reconcile_amount = pay.amount
                                            if pay_inv_line.move_line_id.account_id.transfer_type == 'create_validate':
                                                transfer_entry.post()
                                            transfer_entries_list.append(transfer_entry)
                                            all_transfer_entries.append(transfer_entry)
                                    pay.write(
                                        {'transfer_entry_ids': [vals_sec.id for vals_sec in transfer_entries_list]})

                            elif pay.is_reconciled and pay.transfer_entry_ids and pay.reconciled_statement_lines_count == 0:
                                for ent in pay.transfer_entry_ids.filtered(
                                        lambda l: l.reconcile_amount == pay.amount and not l.is_mistaken_reconcile):
                                    if ent.state == 'draft':
                                        ent.action_post()
                                    reversal_wizard = self.env['account.move.reversal'].with_context(
                                        {'active_ids': [ent.id], 'active_id': ent.id,
                                         'active_model': 'account.move'}).create({
                                        'refund_method': 'cancel',
                                        'reason': 'Mistakenly Created',
                                        'journal_id': ent.journal_id.id,
                                        'date_mode': 'entry'
                                    })
                                    ent.write({'is_mistaken_reconcile': True})
                                    reversal_move = reversal_wizard.reverse_moves()
                                    all_reversal_moves.append(reversal_move)
                            elif pay.state in (
                                    'draft',
                                    'cancel') and pay.transfer_entry_ids and pay.reconciled_statement_lines_count == 0:
                                for ent in pay.transfer_entry_ids.filtered(
                                        lambda l: l.reconcile_amount == pay.amount and not l.is_mistaken_reconcile):
                                    if ent.state == 'draft':
                                        ent.action_post()
                                    reversal_wizard = self.env['account.move.reversal'].with_context(
                                        {'active_ids': [ent.id], 'active_id': ent.id,
                                         'active_model': 'account.move'}).create({
                                        'refund_method': 'cancel',
                                        'reason': 'Mistakenly Created',
                                        'journal_id': ent.journal_id.id,
                                        'date_mode': 'entry'
                                    })
                                    reversal_move = reversal_wizard.reverse_moves()
                                    all_reversal_moves.append(reversal_move)
                transfer_data.append({
                    'loan_name': loan.name,
                    'total_transfer_entries': len(all_transfer_entries) if all_transfer_entries else 0.0,
                    'total_reversal_entries': len(all_reversal_moves) if all_reversal_moves else 0.0,
                    'transfer_entries': [entry.name for entry in all_transfer_entries],
                    'reversal_entries': [move.name for move in all_reversal_moves],
                })
            except (Exception, OperationalError, InterfaceError, psycopg2.Error, UserError) as e:
                if 'cursor already closed' in str(e):
                    self.env.cr.reset()
                    time.sleep(5)
                    self.env.cr.rollback()
                else:
                    error_message = f"Error in 'Automatic Transfer On Reconciliation' for Loan {loan.name}: {str(e)}"
                    _logger.error(error_message)
                    error_messages.append(error_message)
                    time.sleep(5)
                    self.env.cr.rollback()
                continue

        if error_messages:
            failure_record = self.env['failure.history'].create({
                'name': 'Loan Robots-->Automatic Transfer On Reconciliation',
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

        if transfer_data:
            output = BytesIO()
            workbook = xlsxwriter.Workbook(output, {'in_memory': True})
            worksheet = workbook.add_worksheet()

            worksheet.set_column('A:A', 30)
            worksheet.set_column('B:B', 35)
            worksheet.set_column('C:C', 35)
            worksheet.set_column('D:D', 35)
            worksheet.set_column('E:E', 35)

            headers = ['Loan Name', 'Total Transfer Entries', 'Total Reversal Entries', 'Transfer Entries',
                       'Reversal Entries']
            for col_num, header in enumerate(headers):
                worksheet.write(0, col_num, header)

            # Write data rows
            for row_num, data in enumerate(transfer_data, 1):
                worksheet.write(row_num, 0, data['loan_name'])
                worksheet.write(row_num, 1, data['total_transfer_entries'])
                worksheet.write(row_num, 2, data['total_reversal_entries'])
                worksheet.write(row_num, 3,
                                ', '.join(data['transfer_entries']) or 'N/A')
                worksheet.write(row_num, 4,
                                ', '.join(data['reversal_entries']) or 'N/A')

            workbook.close()

            # Save XLSX to binary field
            output.seek(0)
            xlsx_data = base64.b64encode(output.read())
            file_name = f'Automatic_Transfer_Reconciliation_Report_{fields.Date.today()}.xlsx'

            # Create an attachment in Odoo
            attachment = self.env['ir.attachment'].create({
                'name': file_name,
                'type': 'binary',
                'datas': xlsx_data,
                'store_fname': file_name,
                'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            })

            folder_id = self.env['documents.folder'].search(
                [('name', '=', 'Automatic Transfer Reconciliation Reports')], limit=1)
            if not folder_id:
                folder_id = self.env['documents.folder'].create({'name': 'Automatic Transfer Reconciliation Reports'})

            document_defaults = {'folder_id': folder_id.id}
            document = self.env['documents.document'].create(
                {'attachment_id': attachment.id, **document_defaults})



    @api.model
    def delay_reconciliation_email(self):
        loans = self.env['account.loan'].search([('is_straight_through', '=', True)])
        admin = self.env['res.users'].search([('id', '=', 2)])
        for loan in loans:
            invoices = self.env['account.move'].search([('loan_id', '=', loan.id), ('move_type', '!=', 'entry')])
            for inv in invoices:
                payments = self.env['account.payment'].search([('ref', '=', inv.name)])
                for pay in payments:
                    if pay.is_reconciled and not pay.reconciled_statement_line_ids and pay.state == 'posted' and (
                            pay.date + relativedelta(days=5)) == fields.Date.today():
                        loan.is_straight_through = False
                        mail_id = self.env['mail.mail'].sudo().create({
                            'subject': loan.name + ' Straight Through Disabled',
                            'body_html': 'Dear ' + loan.user_id.name + ' the Loan ' + loan.name + ' Straight Through has been disabled because Date of Payment  ' + pay.name + '  has passed 5 days without it has been reconcilled. Please check to avoid any further issue.',
                            'email_to': loan.user_id.partner_id.email or self.env.user.partner_id.email,
                            'auto_delete': False,
                            'email_from': admin.email if admin else False,
                        })
                        mail_id.sudo().send()

    def post(self):
        """
        Create Transaction history when validating loan invoice.
        :return:
        """
        res = super(AccountMove, self).action_post()
        loan_transaction_history = self.env['loan.transaction.history']
        for invoice in self.filtered(lambda x: x.loan_id and x.move_type == "out_invoice"):
            for invoice_line in invoice.invoice_line_ids:
                loan_transaction_history.create({
                    'date': invoice.invoice_date,
                    'loan_id': invoice.loan_id and invoice.loan_id.id or False,
                    'reference': invoice.name and invoice.name or False,
                    # 'description': invoice_line.product_id.name if invoice_line.product_id else invoice_line.name,
                    'debit': invoice_line.price_subtotal,
                    'move_id': invoice and invoice.id or False,
                    'state': 'running'
                })
        return res

    def write_off_invoice(self):
        for rec in self:
            lines = []
            for line in rec.invoice_line_ids:
                lines.append((0, 0,
                              {'move_line_id': line.id,
                               'product_id': line.product_id.id,
                               'name': line.name,
                               'account_id': line.account_id.id,
                               'quantity': line.quantity,
                               'price_unit': line.price_unit,
                               'tax_ids': line.tax_ids.ids,
                               'currency_id': line.currency_id.id,
                               'price_subtotal': line.price_subtotal,
                               'price_total': line.price_total,
                               'paid_amount': line.paid_amount,
                               'unpaid_amount': line.unpaid_amount
                               }))
            existing_write_off_move = self.env['write.off.move'].search(
                [('move_id', '=', rec.id), ('state', 'in', ('draft', 'submit_approval'))], limit=1)
            if not existing_write_off_move:
                write_off_move = self.env['write.off.move'].create({'move_id': rec.id,
                                                                    'write_off_date': fields.Date.today(),
                                                                    'journal_id': rec.journal_id.id,
                                                                    'loan_id': rec.loan_id.id,
                                                                    'currency_id': rec.currency_id.id})
                write_off_move.write({'write_off_line_ids': lines})

            return {
                'name': _('Write-Off Move'),
                'res_model': 'write.off.move',
                'res_id': existing_write_off_move.id or write_off_move.id,
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'view_id': False,
                'target': 'new'
            }


class AccountInvoiceLine(models.Model):
    _inherit = 'account.move.line'

    loan_invoice_id = fields.Many2one('account.move')
    residual_amount_paid = fields.Float(compute='_compute_residual_amount_paid')

    @api.depends('paid_amount')
    def _compute_residual_amount_paid(self):
        for record in self:
            company_currency = record.env.company.currency_id
            rate = 1.0
            if record.currency_id != company_currency:
                rate_line = record.env['res.currency.rate'].search(
                    [('currency_id', '=', record.currency_id.id)],
                    order='name desc', limit=1)
                rate = rate_line.company_rate
                record.residual_amount_paid = rate * record.paid_amount
            else:
                record.residual_amount_paid = record.paid_amount

    @api.model
    def unpaid_amount_invoice_lines(self):
        inv_lines = self.env['account.move.line'].search(
            [('partial_paid', '!=', True), ('fully_paid', '!=', True), ('move_id.move_type', '=', 'out_invoice')])
        for line in inv_lines:
            if line.move_id.payment_state == 'not_paid':
                line.unpaid_amount = line.price_unit
