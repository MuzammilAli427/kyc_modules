from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class CustomerLoans(models.Model):
    _name = 'customer.loans'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'This model contains all the customers the loans'

    name = fields.Char('Loan Name', readonly=True, required=True, copy=False, default='/', store=True)
    customer_id = fields.Many2one('res.partner', 'Customer')  # to do
    compute_partners = fields.Many2many('res.partner', compute='_compute_kyc_partners')
    loan_product_id = fields.Many2one('loan.products', 'Loan Product')
    loan_amount = fields.Float('Loan Amount')
    interest = fields.Char('Interest Rate')
    no_of_installments = fields.Integer('No of Installments')
    grace_period = fields.Integer('Grace Period')
    payment_start_date = fields.Date('Payment starts date')
    currency_id = fields.Many2one('res.currency', 'Currency')
    monthly_payment = fields.Float('Monthly Payments')
    collateral_button = fields.Boolean('Collateral')
    loan_states = fields.Selection([('in_progress', 'In Progress'),
                                    ('active', 'Active'),
                                    ('closed', 'Closed'),
                                    ('written_off', 'Written-Off')],
                                   default='in_progress', tracking=True)
    loan_installment_line_ids = fields.One2many('loan.installment.line', 'loan_id')

    doc_count = fields.Integer(compute='_compute_attached_docs_count', string="Number of documents attached")
    close_loan_count = fields.Integer(compute='_close_loan_count', string="Number of Close Loans")
    doc_count_collaterals = fields.Integer(compute='_compute_collateral_count', string="Number of Collaterals")
    loan_id = fields.Many2one('customer.loans')

    """
    **==========================================================================**
    ** The method below is for the creation of a sequence in the field Loan Name**
    **==========================================================================**
    """

    @api.model
    def create(self, vals_list):
        if isinstance(vals_list, dict):
            vals_list = [vals_list]

        sequence_obj = self.env['ir.sequence']
        sequence_code = 'my_sequence_code'

        for vals in vals_list:
            vals['name'] = sequence_obj.next_by_code(sequence_code)

        res = super(CustomerLoans, self).create(vals_list)

        return res

    """
    **======================================================================**
    ** The method below is for the validations of the field Interest Rate % **
    **======================================================================**
    """

    @api.onchange('interest')
    def check_digit(self):
        for record in self:
            if record.interest:
                if '%' in record.interest:
                    rate = record.interest.replace('%', '').replace('.', '')
                    if rate and not rate.isdigit():
                        raise ValidationError("Only numbers are allowed in Current Rate.")
                    number = int(rate)
                    if number > 100:
                        raise ValidationError("You cannot exceed the limit number.")
                else:
                    for rec in self:
                        if rec.interest and not rec.interest.isdigit():
                            raise ValidationError("Only numbers are allowed in Current Rate.")
                if '%' not in record.interest:
                    record.interest = record.interest + '%'

    """
        **========================================================================**
        ** Smart button will display Attachments list view of the current partner **
        **========================================================================**
    """

    def attachment_tree_view_loan(self):
        return {
            'name': _('Attachments'),
            'domain': [('res_model', '=', 'customer.loans'), ('res_id', '=', self.id)],
            'res_model': 'documents.document',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,kanban',
            'context': {
                # "default_partner_id": self.partner_id.id,
                'default_res_model': 'customer.loans', 'default_res_id': self.id, "searchpanel_default_folder_id": False
                # "searchpanel_default_folder_id": self.env.ref('smart_loan_system.document_folder_company_doc').id
            },
        }

    """
        **==================================================================================**
        ** Count a documents according to Loan model and res_id and assign in computed field**
        **==================================================================================**
        """

    def _compute_attached_docs_count(self):
        read_group_var = self.env['documents.document'].search_count(
            [('res_model', '=', 'customer.loans'), ('res_id', '=', self.id)])
        for record in self:
            record.doc_count = read_group_var

    """
            **========================================================================**
            ** Smart button will display Collaterals list view of the current partner **
            **========================================================================**
        """

    def collateral_tree_view_loan(self):
        return {
            'name': _('Collaterals'),
            'domain': [('customer_id', '=', self.customer_id.id)],
            'res_model': 'loan.collateral',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            # 'context': {
            #     # "default_partner_id": self.partner_id.id,
            #     'default_res_model': 'customer.loans', 'default_res_id': self.id,
            #     # "searchpanel_default_folder_id": self.env.ref('smart_loan_system.document_folder_company_doc').id
            # },
        }

    def _close_loan_count(self):
        for loan in self:
            loan.close_loan_count = loan.env['customer.loans'].search_count([('loan_id', '=', loan.id)])

    """
            **=============================================================================================**
            ** Count collaterals according to Loan Collateral model and res_id and assign in computed field**
            **=============================================================================================**
            """

    def _compute_collateral_count(self):
        read_group_var = self.env['loan.collateral'].search_count(
            [('customer_id', '=', self.customer_id.id)])  # ('res_model', '=', 'customer.loans'), ('res_id', '=', self.id)
        for record in self:
            record.doc_count_collaterals = read_group_var

    def compute_monthly_loan_payment(self):
        for rec in self:
            if rec.loan_amount and rec.interest and rec.no_of_installments:
                percent_interest = int(rec.interest.split('%')[0]) / 100
                payment_formula_up = rec.loan_amount * (percent_interest / 12) * pow((1 + percent_interest / 12),
                                                                                     rec.no_of_installments)
                payment_formula_down = pow((1 + percent_interest / 12), rec.no_of_installments) - 1
                monthly_total_payment = payment_formula_up / payment_formula_down
                rec.write({'monthly_payment': monthly_total_payment})
                # if monthly_total_payment:
                #     interest_portion = percent_interest / 12 * rec.loan_amount
                #     if interest_portion:
                #         principal_interest = monthly_total_payment - interest_portion

    def submit_loan(self):
        pass

    def cancel_loan(self):
        pass

    def written_off_loan(self):
        for rec in self:
            rec.write({'loan_states': 'written_off'})

    def refuse_loan(self):
        pass

    def reschedule_loan(self):
        for rec in self:
            new_loan = rec.env['customer.loans'].create({
                'loan_id': rec.id,
                'loan_product_id': rec.loan_product_id.id,
                'loan_amount': rec.loan_amount,
                'interest': rec.interest,
                'no_of_installments': rec.no_of_installments,
                'grace_period': rec.grace_period,
                'payment_start_date': rec.payment_start_date,
                'currency_id': rec.currency_id.id,
                'monthly_payment': rec.monthly_payment,
            })
            rec.write({'loan_states': 'closed'})
            return {
                'name': _('Loans'),
                'domain': [('id', '=', new_loan.id)],
                'res_model': 'customer.loans',
                'type': 'ir.actions.act_window',
                'view_mode': 'tree,form',
            }

    def close_loan_tree_view_loan(self):
        for rec in self:
            return {
                'name': _('Loans'),
                'domain': [('loan_id', '=', rec.id)],
                'res_model': 'customer.loans',
                'type': 'ir.actions.act_window',
                'view_mode': 'tree,form',
            }

    @api.onchange('customer_id')
    def kyc_partners(self):
        for rec in self:
            kyc_retail_partner = rec.env['kyc.retail'].search([]).mapped('partner_id')
            kyc_corp_partner = rec.env['kyc.corporate'].search([]).mapped('partner_id')
            partners = kyc_retail_partner + kyc_corp_partner
            domain = [('id', 'in', partners.mapped('id'))]
            return {'domain': {'customer_id': domain}}

    def _compute_kyc_partners(self):
        for rec in self:
            kyc_retail_partner = rec.env['kyc.retail'].search([]).mapped('partner_id')
            kyc_corp_partner = rec.env['kyc.corporate'].search([]).mapped('partner_id')
            rec.compute_partners = kyc_retail_partner.ids + kyc_corp_partner.ids

    """
        **=========================================**
        ** This model contains the Customer loans **
        **=========================================**
    """
