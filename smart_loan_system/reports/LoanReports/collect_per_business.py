from odoo import fields, api, models
from dateutil import rrule
from datetime import date

class CollectPerBusiness(models.TransientModel):
       _name = 'collect.per.business'
       _description = 'Collect Per Business'

       date_from = fields.Date(string='Date From', required=True)
       date_to = fields.Date(string='Date To', required=True)
       per_month = fields.Selection(selection=[('month','Month')],default='month',string='Per Month')

       def get_report(self):
              dates = list(rrule.rrule(rrule.MONTHLY, dtstart=self.date_from, until=self.date_to))
              account_loan = self.env['account.loan'].sudo().search([])
              account_loan_retail = account_loan.filtered(lambda l: l.kyc_type == 'retail')
              account_loan_corporate = account_loan.filtered(lambda l: l.kyc_type == 'corporate')

              invoice_lines_retail = self.get_invoice_lines(account_loan_retail)
              invoice_lines_corporate = self.get_invoice_lines(account_loan_corporate)
              data = []
              cumulatative_retail_corporate = {}
              for dt in dates:
                    subdata = []
                    subdata.append(f'{dt.strftime("%b")} - {dt.year}')
                    date_corporate = "{:,.2f}".format(sum(invoice_lines_corporate.filtered(
                        lambda l: l.create_date.month == dt.month and l.create_date.year == dt.year).mapped(
                        'residual_amount_paid')))
                    subdata.append(date_corporate)
                    data_retail = "{:,.2f}".format(sum(invoice_lines_retail.filtered(lambda l: l.create_date.month == dt.month and l.create_date.year == dt.year).mapped(
                           'residual_amount_paid')))
                    subdata.append(data_retail)
                    subdata.append("{:,.2f}".format(float(data_retail)+float(date_corporate)))
                    data.append(subdata)
              report_action = self.env.ref("smart_loan_system.collect_per_business_report_action").report_action(self.id,data={'data':data})
              return report_action

       def get_invoice_lines(self,loans):
           config_obj = self.env['ir.config_parameter']
           interest_prod_id = config_obj.sudo().get_param('ae_loan_manag.interest_prod_id')
           principal_prod_id = config_obj.sudo().get_param('ae_loan_manag.principal_prod_id')
           total_invoices = self.env['account.move.line']
           for loan in loans:
               domain = [('move_id.loan_id', '=', loan.id), ('product_id', '=', int(principal_prod_id)),
                         ('move_id.state', '=', 'posted'), ('move_id.move_type', '=', 'out_invoice')]
               invoice_lines = self.env['account.move.line'].search(domain)
               total_invoices = total_invoices | invoice_lines
           return total_invoices
