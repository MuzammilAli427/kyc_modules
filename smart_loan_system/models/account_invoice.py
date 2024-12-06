from odoo import api, fields, models, _
import logging

_logger = logging.getLogger(__name__)

try:
    import numpy
except (ImportError, IOError) as err:
    _logger.error(err)


class AccountInvoice(models.Model):
    _inherit = 'account.move'

    emi = fields.Boolean('Is Installment?')
    is_down_payment = fields.Boolean('Is Downpayment?')
    splitted_invoice = fields.Boolean("Splitted Invoice")
    main_invoice_id = fields.Many2one("account.move")
    is_restructuring_inv = fields.Boolean('Is Restructuring?', default=False)
    is_automatic_entry = fields.Boolean('Is Automatic Entry?', default=False)
    is_mistaken_reconcile = fields.Boolean('Is Mistaken Reconcile?', default=False)


class PartnerInherit(models.Model):
    _inherit = 'res.partner'

    loan_count = fields.Integer(string='Loans', compute="get_loan_count")
    total_payment_amount = fields.Float('Total Payment Amount', compute='cal_payment_amt')
    kyc_customer_number = fields.Char()
    kyc_type = fields.Selection([
        ('retail', 'Retail'),
        ('corporate', 'Corporate'),
        ('group', 'Group')])
    status = fields.Selection(
        [('active', 'Active'),
         ('unactive', 'None Active')],
        'Status')

    def name_get(self):
        res = []
        for rec in self:
            if rec.kyc_customer_number:
                res.append((rec.id, '%s / %s' % (rec.kyc_customer_number, rec.name)))
            else:
                res.append((rec.id, '%s' % (rec.name)))
        return res

    def cal_payment_amt(self):
        """
        Calculate total payment amount of loan.
        :return:
        """
        pay_his_obj = self.env['account.payment.history']
        for partner in self:
            histories = pay_his_obj.search([('partner_id', '=', partner.id), ('state', '=', 'running')])
            partner.total_payment_amount = sum(history.amount for history in histories)

    def get_loan_count(self):
        """
        Count total loan of partner.
        :return:
        """
        loan = self.env['account.loan']
        for partner in self:
            partner.loan_count = len(loan.search([('partner_id', '=', partner.id)]))
