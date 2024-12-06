from odoo import fields, api, models
from dateutil import rrule
from datetime import date

class CreditPortfolioGroup(models.TransientModel):
       _name = 'credit.portfolio.group'
       _description = 'Credit Portfolio Group'

       date_from = fields.Date(string='Date From')
       date_to = fields.Date(string='Date To')
       country_id = fields.Many2one('res.country', string='Country', domain="[('name','in',['Curaçao','Bonaire, Sint Eustatius and Saba'])]")

       def get_report(self):
              account_loan = self.env['account.loan'].sudo().search([('country_id', '=', self.country_id.id)])
              dates = list(rrule.rrule(rrule.MONTHLY, dtstart=self.date_from, until=self.date_to))
              docs = []


              for dt in dates:
                     data = {
                            'country': self.country_id.name,
                            'months': "",
                            'satisfactory': [],
                            'special_mention': [],
                            'substandard': [],
                            'doubtful': [],
                            'loss': [],
                            'total': [],
                     }
                     account_loans = account_loan.filtered(
                            lambda l: l.create_date.month == dt.month and l.create_date.year == dt.year)
                     data['months'] = f"{dt.strftime('%b')}-{dt.year}"
                     outstanding_balance = account_loans.filtered(lambda l: l.days_past_due >= 0 and l.days_past_due <= 29).mapped('outstanding_bal')
                     outstanding_balance_loans_counts = len(outstanding_balance)
                     outstanding_balance = "{:,.2f}".format(sum(outstanding_balance) / 1.000)
                     data['satisfactory'].append(outstanding_balance)
                     data['satisfactory'].append(outstanding_balance_loans_counts)

                     outstanding_balance = account_loans.filtered(
                            lambda l: l.days_past_due >= 30 and l.days_past_due <= 89).mapped('outstanding_bal')
                     outstanding_balance_loans_counts = len(outstanding_balance)
                     outstanding_balance = "{:,.2f}".format(sum(outstanding_balance) / 1.000)
                     data['special_mention'].append(outstanding_balance)
                     data['special_mention'].append(outstanding_balance_loans_counts)

                     outstanding_balance = account_loans.filtered(
                            lambda l: l.days_past_due >= 90 and l.days_past_due <= 119).mapped('outstanding_bal')
                     outstanding_balance_loans_counts = len(outstanding_balance)
                     outstanding_balance = "{:,.2f}".format(sum(outstanding_balance) / 1.000)
                     data['substandard'].append(outstanding_balance)
                     data['substandard'].append(outstanding_balance_loans_counts)

                     outstanding_balance = account_loans.filtered(
                            lambda l: l.days_past_due >= 120 and l.days_past_due <= 179).mapped('outstanding_bal')
                     outstanding_balance_loans_counts = len(outstanding_balance)
                     outstanding_balance = "{:,.2f}".format(sum(outstanding_balance) / 1.000)
                     data['doubtful'].append(outstanding_balance)
                     data['doubtful'].append(outstanding_balance_loans_counts)

                     outstanding_balance = account_loans.filtered(
                            lambda l: l.days_past_due >= 180 ).mapped('outstanding_bal')
                     outstanding_balance_loans_counts = len(outstanding_balance)
                     outstanding_balance = "{:,.2f}".format(sum(outstanding_balance) / 1.000)
                     data['loss'].append(outstanding_balance)
                     data['loss'].append(outstanding_balance_loans_counts)

                     data['total'].append(
                            float(data['satisfactory'][0])+
                            float(data['special_mention'][0])+
                            float(data['substandard'][0])+
                            float(data['doubtful'][0])+
                            float(data['loss'][0])
                     )
                     data['total'].append(
                            data['satisfactory'][1]+
                            data['special_mention'][1]+
                            data['substandard'][1]+
                            data['doubtful'][1]+
                            data['loss'][1]
                     )
                     docs.append(data)
              report_action = self.env.ref("smart_loan_system.credit_portfolio_group_report_action").report_action(self.id,data={'wrap':docs})
              return report_action