from odoo import fields, api, models
from dateutil import rrule
import matplotlib.pyplot as plt
import io, base64

class RetailLoanInstallmentAndRepayment(models.TransientModel):
       _name = 'retail.loan.installment.repayment'
       _description = 'Retail Loan Installment Repayment'

       date_from = fields.Date(string='Date from')
       date_to = fields.Date(string='Date to')
       partner_id = fields.Many2one('res.partner', string='Partner')
       bar_chart_html = fields.Html()
       bar_image_data = fields.Binary()


       def get_report(self):
              categories = []
              values = []

              def addlabels(x, y):
                  for i in range(len(x)):
                       plt.text(i, y[i], y[i], ha='center')

              plt.xlabel('Dates')
              plt.ylabel('Amounts')
              plt.title('Retail Loan Installments and repayments')


              dates = list(rrule.rrule(rrule.MONTHLY, dtstart=self.date_from, until=self.date_to))
              account_loan = self.env['account.loan'].sudo().search([])
              account_loan_retail_only = account_loan.filtered(lambda l: l.kyc_type == 'retail')
              invoices_loan_retail_only = self.get_invoice_lines(account_loan_retail_only)
              for dt in dates:
                     categories.append(f'{dt.strftime("%b")} - {dt.year}')
                     account_loan_retail = "{:,.2f}".format(sum(invoices_loan_retail_only.filtered(
                            lambda l: l.create_date.month == dt.month and l.create_date.year == dt.year).mapped(
                            'residual_amount_paid')))
                     values.append("{:,.2f}".format(float(account_loan_retail)))

              plt.bar(categories,values)
              addlabels(categories,values)
              buffer = io.BytesIO()
              plt.savefig(buffer, format='png')
              buffer.seek(0)
              image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
              self.bar_image_data = image_base64
              report_action = self.env.ref("smart_loan_system.retail_loan_installment_repayment_report_action").report_action(self.id)
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
