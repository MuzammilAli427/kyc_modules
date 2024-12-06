from datetime import timedelta
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError



class CronFailedReport(models.AbstractModel):
    _name = 'report.bi_cron_failure_history.cron_failed_report'
    _description = 'Cron Failed Report'

    
    
    def _get_failed_cron_activities(self, cron_ids):
        
        all_msg = []
        for cron in cron_ids:
            all_activities = self.env['mail.activity'].search([('res_model_id', '=', 'ir.cron'), ('res_id', 'in', cron.ids)])
            all_activities = all_activities.filtered(lambda r: r.activity_type_id.name == 'Exception')
            for i in all_activities:
                all_msg.append({'Cron job name': cron.name, 'Date Time of Run': str(i.dt), 'Details':i.notes})
        return all_msg
        
        

    @api.model
    def _get_report_values(self, docids, data=None):

        cron_failed_report = self.env['ir.actions.report']._get_report_from_name('bi_cron_failure_history.cron_failed_report')
        cron_ids = self.env['ir.cron'].browse(docids)
        return {
            'doc_ids': self.ids,
            'doc_model': cron_failed_report.model,
            'docs': cron_ids,
            'get_failed_cron_activities': self._get_failed_cron_activities(cron_ids),
        }
        
        
        
        
    