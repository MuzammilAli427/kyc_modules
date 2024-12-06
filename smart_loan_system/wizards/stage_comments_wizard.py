from odoo import api, fields, models, _
from pytz import timezone
import pytz

class LafStageComments(models.TransientModel):
    _name = 'laf.stage.comment'
    _description = "Laf Stage Comment"

    loan_id = fields.Many2one('account.loan', string='Loan', readonly=True)
    reason = fields.Text()

    def approve_laf_stage(self):
        for rec in self.loan_id:
            if self.reason:
                # Get the current UTC time
                now_utc = fields.Datetime.now()

                # Convert UTC time to Curaçao time
                curacao_tz = timezone('America/Curacao')
                now_curacao = now_utc.astimezone(curacao_tz)

                # Format the time for display
                formatted_time = now_curacao.strftime('%Y-%m-%d %H:%M:%S')

                rec.sudo().write({
                    'stage_comment': rec.stage_comment + '\n' + formatted_time + ' @ ' + self.env.user.name + ' Leave the comment on LAf: ' + self.reason 
                    if rec.stage_comment else 
                    formatted_time + ' @ ' + self.env.user.name + ' Leave the comment on LAf: ' + self.reason,
                })
