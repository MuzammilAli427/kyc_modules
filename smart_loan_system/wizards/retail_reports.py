from odoo import fields, api, models


class RetailReports(models.TransientModel):
       _name = 'retail.report.one'

       date_from = fields.Date(string='Date from')
       date_to = fields.Date(string='Date to')
       partner_id = fields.Many2one('res.partner', string='Partner')
       company_id = fields.Many2one('res.company', default=lambda self: self.env.company.id)


       def get_report(self):
           report_target = self.env.context.get('report_trigger')
           report_action = None
           if report_target == 1:
               report_action = self.env.ref("smart_loan_system.retail_report_pdf_action_1").report_action(self.id)
           if report_target == 2:
               report_action = self.env.ref("smart_loan_system.retail_report_pdf_action_2").report_action(self.id)
           if report_target == 3:
               report_action = self.env.ref("smart_loan_system.retail_report_pdf_action_3").report_action(self.id)

           return report_action



       def _get_data_for_report_1(self):
           return {}