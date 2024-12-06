from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class LoanProducts(models.Model):
    _name = 'loan.products'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'This model contains the loan products'
    _rec_name = 'code'

    name = fields.Char('Product Name', tracking=True, required=True)
    code = fields.Char(tracking=True)
    interest_min = fields.Char('Interest rate min', tracking=True)
    interest_max = fields.Char('Interest rate max', tracking=True)
    amount_minimum = fields.Monetary('Amount min', currency_field='currency_id', tracking=True)
    currency_id = fields.Many2one('res.currency', default=lambda self: self._default_currency_id(), tracking=True)
    amount_maximum = fields.Monetary('Amount max', currency_field='currency_id', tracking=True)
    no_of_installments_min = fields.Integer('Number of installments min', tracking=True)
    no_of_installments_max = fields.Integer('Number of installments max', tracking=True)
    grace_period_min = fields.Integer('Grace period min', tracking=True)
    grace_period_max = fields.Integer('Grace period max', tracking=True)
    penalties_rate = fields.Char('Penalty Rate/Charges', tracking=True)
    entry_fee = fields.Char('Restructuring Fee', tracking=True)
    partial_repayment_fee = fields.Char('Early partial repayment fees', tracking=True)
    total_repayment_fee = fields.Char('Early total repayment fees/ Administration Fee, Pay off', tracking=True)
    list_price = fields.Float()
    country_id = fields.Many2one('res.country', 'Country', tracking=True, domain = [('name', 'in', ['Curaçao', 'Bonaire, Sint Eustatius and Saba'])])


    comments = fields.Html(tracking=True)

    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'Product name must be unique'),
        ('code_uniq', 'unique(code)', 'Product code must be unique'),
        ]

    def _default_currency_id(self):
        return self.env.user.company_id.currency_id

    """
    **======================================================================**
    ** The methods below are for the validations of the fields containing % **
    **======================================================================**
    """

    @api.onchange('interest_min')
    def check_digit_interest_min(self):
        for record in self:
            if record.interest_min:
                if '%' in record.interest_min:
                    rate = record.interest_min.replace('%', '').replace('.', '')
                    if rate and not rate.isdigit():
                        raise ValidationError("Only numbers are allowed in Interest rate min.")
                    number = int(rate)
                    if number > 100:
                        raise ValidationError("You cannot exceed the limit number.")
                else:
                    for record in self:
                        rate = record.interest_min.replace('.', '')
                        if rate and not rate.isdigit():
                            raise ValidationError("Only numbers are allowed in Interest rate min.")
                if '%' not in record.interest_min:
                    record.interest_min = record.interest_min + '%'

    @api.onchange('interest_max')
    def check_digit_interest_max(self):
        for record in self:
            if record.interest_max:
                if '%' in record.interest_max:
                    rate = record.interest_max.replace('%', '').replace('.', '')
                    if rate and not rate.isdigit():
                        raise ValidationError("Only numbers are allowed in Interest rate max.")
                    number = int(rate)
                    if number > 100:
                        raise ValidationError("You cannot exceed the limit number.")
                else:
                    for record in self:
                        rate = record.interest_max.replace('.', '')
                        if rate and not rate.isdigit():
                            raise ValidationError("Only numbers are allowed in Interest rate max.")
                if '%' not in record.interest_max:
                    record.interest_max = record.interest_max + '%'

    @api.onchange('penalties_rate')
    def check_digit_penalties_rate(self):
        for record in self:
            if record.penalties_rate:
                if '%' in record.penalties_rate:
                    rate = record.penalties_rate.replace('%', '').replace('.', '')
                    if rate and not rate.isdigit():
                        raise ValidationError("Only numbers are allowed in Penalty Rate/Charges.")
                    number = int(rate)
                    if number > 100:
                        raise ValidationError("You cannot exceed the limit number.")
                else:
                    for record in self:
                        rate = record.penalties_rate.replace('.', '')
                        if rate and not rate.isdigit():
                            raise ValidationError("Only numbers are allowed in Penalty Rate/Charges.")
                if '%' not in record.penalties_rate:
                    record.penalties_rate = record.penalties_rate + '%'

    @api.onchange('entry_fee')
    def check_digit_entry_fee(self):
        for record in self:
            if record.entry_fee:
                if '%' in record.entry_fee:
                    rate = record.entry_fee.replace('%', '').replace('.', '')
                    if rate and not rate.isdigit():
                        raise ValidationError("Only numbers are allowed in Restructuring Fee.")
                    number = int(rate)
                    if number > 100:
                        raise ValidationError("You cannot exceed the limit number.")
                else:
                    for record in self:
                        rate = record.entry_fee.replace('.', '')
                        if rate and not rate.isdigit():
                            raise ValidationError("Only numbers are allowed in Restructuring Fee.")
                if '%' not in record.entry_fee:
                    record.entry_fee = record.entry_fee + '%'

    @api.onchange('partial_repayment_fee')
    def check_digit_partial_repayment_fee(self):
        for record in self:
            if record.partial_repayment_fee:
                if '%' in record.partial_repayment_fee:
                    rate = record.partial_repayment_fee.replace('%', '').replace('.', '')
                    if rate and not rate.isdigit():
                        raise ValidationError("Only numbers are allowed in Early partial repayment fees.")
                    number = int(rate)
                    if number > 100:
                        raise ValidationError("You cannot exceed the limit number.")
                else:
                    for record in self:
                        rate = record.partial_repayment_fee.replace('.', '')
                        if rate and not rate.isdigit():
                            raise ValidationError("Only numbers are allowed in Early partial repayment fees.")
                if '%' not in record.partial_repayment_fee:
                    record.partial_repayment_fee = record.partial_repayment_fee + '%'

    @api.onchange('total_repayment_fee')
    def check_digit_total_repayment_fee(self):
        for record in self:
            if record.total_repayment_fee:
                if '%' in record.total_repayment_fee:
                    rate = record.total_repayment_fee.replace('%', '').replace('.', '')
                    if rate and not rate.isdigit():
                        raise ValidationError("Only numbers are allowed in Early total repayment fees.")
                    number = int(rate)
                    if number > 100:
                        raise ValidationError("You cannot exceed the limit number.")
                else:
                    for record in self:
                        rate = record.total_repayment_fee.replace('.', '')
                        if rate and not rate.isdigit():
                            raise ValidationError("Only numbers are allowed in Early total repayment fees.")
                if '%' not in record.total_repayment_fee:
                    record.total_repayment_fee = record.total_repayment_fee + '%'

    """
        **=======================================**
        ** This model contains the loan products **
        **=======================================** 
    """

