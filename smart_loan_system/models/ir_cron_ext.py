from odoo import api, fields, models, _
import time
import logging
from odoo.exceptions import UserError, Warning
import psycopg2
from psycopg2 import InterfaceError, OperationalError


_logger = logging.getLogger(__name__)


class IrCronExt(models.Model):
    _inherit = "ir.cron"

    total_retries = fields.Integer(string='Total Retries Count')

    def _run_cron_job(self, cron_name):
        cron = self.env['ir.cron'].search(
            ['|', ('active', '=', True), ('active', '=', False), ('name', '=', cron_name)]
        )
        if cron:
            try:
                _logger.info(f"Running cron job {cron_name}...")
                cron.method_direct_trigger()
                _logger.info(f"Cron job {cron_name} ran successfully!")
                self.env.cr.commit()
                return True
            except (Exception, OperationalError, InterfaceError, psycopg2.Error, UserError) as e:
                _logger.error(f"Error occurred while running {cron_name}: {str(e)}")
                return False

        else:
            _logger.error(f"Cron job {cron_name} not found!")
            return False

    @api.model
    def run_loan_robots(self):
        cron_names = [
            'Automatic Transfer On Reconciliation',
            'Accrual Creation',
            'Loan Penalty Application',
            'Loan Auto Invoice Generation',
            # 'Loan Auto Xlsx Generation',
        ]

        for cron_name in cron_names:
            # if cron_name == 'Loan Auto Xlsx Generation':
            #     if not self._run_cron_job(cron_name):
            #         break
            #     else:
            #         return
            # else:
                self._run_cron_job(cron_name)


