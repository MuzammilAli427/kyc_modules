from odoo import api, fields, models, _
from odoo.exceptions import UserError, Warning


class WriteOffMove(models.Model):
    _name = 'write.off.move'
    _description = "Write-Off Move"

    move_id = fields.Many2one('account.move')
    write_off_date = fields.Date()
    journal_id = fields.Many2one('account.journal')
    loan_id = fields.Many2one('account.loan')
    currency_id = fields.Many2one('res.currency')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submit_approval', 'Submit For Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], default='draft')
    write_off_line_ids = fields.One2many('write.off.move.line', 'write_off_id')
    edit_allow = fields.Boolean(compute='_compute_edit_allow')
    write_off_wiz_id = fields.Many2one('write.off.move')

    @api.depends('state')
    def _compute_edit_allow(self):
        for rec in self:
            if rec.state == 'draft' and self.env.user.has_group(
                    'smart_loan_system.group_loan_cao'):
                rec.edit_allow = True
            else:
                rec.edit_allow = False

    def submit_for_approval(self):
        for rec in self:
            rec.write({'state': 'submit_approval'})

    def reject_write_off_move(self):
        for rec in self:
            rec.write({'state': 'rejected',
                       'write_off_wiz_id': rec.id})

    def process_write_off_move(self):
        for rec in self:
            date = fields.Date.today()
            loan_acc_rec_id = self.env['ir.config_parameter'].sudo().get_param('ae_loan_manag.acc_rec_id')
            if not loan_acc_rec_id:
                raise UserError(
                    _("Please Configure 'Loan Account Receivable' from Loans -> Configurations -> Settings!"))
            loan_acc_rec = self.env['account.account'].browse(int(loan_acc_rec_id))
            company_currency = self.env.company.currency_id
            rate = 1.0
            if rec.currency_id != company_currency:
                rate_line = self.env['res.currency.rate'].search([('currency_id', '=', rec.currency_id.id)],
                                                                 order='name desc', limit=1)
                rate = rate_line.inverse_company_rate
            if rec.write_off_line_ids:
                for line in rec.write_off_line_ids:
                    if line.is_select:
                        reversal_move = self.env['account.move'].create({
                            'journal_id': rec.journal_id.id,
                            'loan_id': rec.loan_id.id or False,
                            'ref': 'Reversal Entry For' + ' ' + line.account_id.name,
                            'date': date,
                            'invoice_date': date,
                            'move_type': 'entry',
                            'currency_id': line.currency_id.id,
                            'partner_id': rec.move_id.partner_id.id or False,
                            'reversed_entry_id': rec.move_id.id,
                            # 'pay_by_line_execute': False
                        })
                        lines = [{
                            'account_id': loan_acc_rec.id,
                            'partner_id': rec.move_id.partner_id.id or False,
                            'debit': 0,
                            'credit': (round(rate * line.unpaid_amount, 2)),
                            'amount_currency': (round(-1 * line.unpaid_amount, 2)),
                            'name': line.name,
                            'date': fields.Date.today(),
                            'ref': 'Reversal Credit Entry For' + ' ' + line.account_id.name,
                            'currency_id': rec.currency_id.id,
                        }, {
                            'account_id': line.account_id.id,
                            'partner_id': rec.move_id.partner_id.id or False,
                            'debit': (round(rate * line.unpaid_amount, 2)),
                            'credit': 0,
                            'amount_currency': (round(line.unpaid_amount, 2)),
                            'name': line.name,
                            'date': fields.Date.today(),
                            'ref': 'Reversal Debit Entry For' + ' ' + line.account_id.name,
                            'currency_id': rec.currency_id.id,
                        }]
                        reversal_move.line_ids = [(0, 0, val) for val in lines]
                        reversal_move.action_post()


                        line.move_line_id.write({'unpaid_amount' : line.move_line_id.unpaid_amount - line.unpaid_amount,
                                                 'paid_amount': line.move_line_id.paid_amount + line.unpaid_amount})

            rec.write({'state': 'approved'})


class WriteOffMoveLine(models.Model):
    _name = 'write.off.move.line'
    _description = "Write-Off Move Line"

    write_off_id = fields.Many2one('write.off.move')
    move_line_id = fields.Many2one('account.move.line')
    is_select = fields.Boolean(default=False, string='Select')
    product_id = fields.Many2one('product.product')
    name = fields.Char()
    account_id = fields.Many2one('account.account')
    quantity = fields.Float()
    price_unit = fields.Float()
    tax_ids = fields.Many2many('account.tax')
    currency_id = fields.Many2one('res.currency')
    price_subtotal = fields.Monetary(currency_field='currency_id')
    price_total = fields.Monetary(currency_field='currency_id')
    paid_amount = fields.Monetary(currency_field='currency_id')
    unpaid_amount = fields.Monetary(currency_field='currency_id')
