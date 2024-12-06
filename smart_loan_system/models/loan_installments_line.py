from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class CustomerLoansIns(models.Model):
    _name = 'loan.installment.line'
    _description = 'This model contains the installments of the customers loans'

    payment_number = fields.Char('Payment Number', readonly=True, required=True, copy=False, default='0000', store=True)
    payment_date = fields.Date('Payment Date')
    current_rate = fields.Char('Current Rate')
    payment = fields.Float('Payment')
    interest_por = fields.Float('Interest Portion')
    principle_portion = fields.Float('Principle Portion')
    principle_balance = fields.Float('Principal Balance')
    loan_id = fields.Many2one('customer.loans')

    """
    **======================================================================**
    ** The methods below are for the validations of the fields containing % **
    **======================================================================**
    """

    @api.onchange('current_rate')
    def check_digit(self):
        for record in self:
            if record.current_rate:
                if '%' in record.current_rate:
                    rate = record.current_rate.replace('%', '').replace('.', '')
                    if rate and not rate.isdigit():
                        raise ValidationError("Only numbers are allowed in Current Rate.")
                    number = int(rate)
                    if number > 100:
                        raise ValidationError("You cannot exceed the limit number.")
                else:
                    for record in self:
                        if record.current_rate and not record.current_rate.isdigit():
                            raise ValidationError("Only numbers are allowed in Current Rate.")
                if '%' not in record.current_rate:
                    record.current_rate = record.current_rate + '%'

    """
    **===========================================================================**
    ** The method below is for the creation of a sequence in the field Payment No**
    **===========================================================================**
    """

    @api.model_create_multi
    def create(self, vals):
        vals[0]['payment_number'] = self.env['ir.sequence'].next_by_code('payment_ins_sequence_code')
        return super(CustomerLoansIns, self).create(vals)
