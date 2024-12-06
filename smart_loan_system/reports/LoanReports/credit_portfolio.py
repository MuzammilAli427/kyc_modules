import datetime

from odoo import fields, api, models
from dateutil import rrule
from datetime import date

class CreditPortfolio(models.TransientModel):
       _name = 'credit.portfolio'
       _description = 'Credit Portfolio'

       date_from = fields.Date(string='Date From')
       date_to = fields.Date(string='Date To')
       country_id = fields.Many2one('res.country', string='Country', domain="[('name','in',['Curaçao','Bonaire, Sint Eustatius and Saba'])]")


       def get_report(self):
              account_loan = self.env['account.loan'].sudo().search([('country_id','=',self.country_id.id)])
              dates = list(rrule.rrule(rrule.MONTHLY, dtstart=self.date_from, until=self.date_to))
              data = {
                     'country': self.country_id.name,
                     'months': [],
                     'total_credit_portfolio': [],
                     'number_of_loans': [],
                     'number_of_clients': [],
                     'corporate_count': [],
                     'retail_count': [],
              }
              for dt in dates:
                     outstanding_amount = [self.outstanding_from_account_move_lines(loan,dt) for loan in account_loan]
                     outstanding_balance = "{:,.2f}".format(sum(outstanding_amount))
                     loan_count = "{:,.2f}".format(len(account_loan.filtered(
                            lambda l: l.start_date <= dt.date())))
                     partner_count = len(list(set(account_loan.filtered(
                            lambda l: l.start_date.month == dt.month and l.start_date.year == dt.year).mapped('partner_id'))))
                     partner_count_kyc_corporate_group = len(list(set(account_loan.filtered(lambda l: l.kyc_type in ['corporate',
                                                                                                            'group'] and l.start_date.month == dt.month and l.start_date.year == dt.year).mapped(
                            'partner_id'))))
                     partner_count_kyc_retail = len(list(set(account_loan.filtered(lambda l: l.kyc_type == 'retail' and l.start_date.month == dt.month and l.start_date.year == dt.year).mapped('partner_id'))))
                     data['months'].append(f"{dt.strftime('%b')} - {dt.year}")
                     data['total_credit_portfolio'].append(outstanding_balance)
                     data['number_of_loans'].append(loan_count)
                     data['number_of_clients'].append(partner_count)
                     data['corporate_count'].append(partner_count_kyc_corporate_group)
                     data['retail_count'].append(partner_count_kyc_retail)
              report_action = self.env.ref("smart_loan_system.credit_portfolio_report_action").report_action(self.id,data={'data':data})
              return report_action

       def outstanding_from_account_move_lines(self,loan,date):
              # loan = 12345
              # date = datetime.date(year=2024,month=4,day=20)
              product_id = self.env['ir.config_parameter'].sudo().get_param('ae_loan_manag.disbursement_acc_id')
              initial_domain = [('move_id.loan_id', '=', loan.id), ('account_id', '=', int(product_id))]
              account_move_line = self.env['account.move.line'].search(initial_domain)

              debit_amount = account_move_line.filtered(lambda l: l.debit != 0 and l.create_date <= date).mapped('debit')
              credit_amount = account_move_line.filtered(lambda l: l.credit != 0 and l.create_date <= date).mapped('credit')

              outstanding_amount = sum(debit_amount) - sum(credit_amount)

              return outstanding_amount

