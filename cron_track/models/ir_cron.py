# -*- coding: utf-8 -*-
##############################################################################
#                                                                            #
# Part of Caret IT Solutions Pvt. Ltd. (Website: www.caretit.com).           #
# See LICENSE file for full copyright and licensing details.                 #
#                                                                            #
##############################################################################

from odoo import models, api, fields
import logging
import odoo
import time
from datetime import datetime
import pytz

_logger = logging.getLogger(__name__)

class IrCron(models.Model):
    _inherit = "ir.cron"

    auto_commit = fields.Boolean(
        string="Auto Commit",
        help="""If you are the Technical Person and you know about the Commit 
        and Rollback than activate this options Otherwise keep as it is."""
    )

    def open_cron_track_log(self):
        """ open cron tracking fields."""
        cron_track_log = self.env['cron.track'].search(
            [('cron_name', '=', self.name)])
        action = self.env.ref('cron_track.action_cron_track').read()[0]
        if cron_track_log:
            if len(cron_track_log) > 1:
                action['domain'] = [('id', 'in', cron_track_log.ids)]
            elif cron_track_log:
                action['views'] = [(self.env.ref(
                    'cron_track.cron_track_form_view').id, 'form')]
                action['res_id'] = cron_track_log.id
            return action

    def create_cron_track(self, cron_name, cron_track_start_time,
                          custom_end_time, total_time, e=False):
        """create cron track record"""
        curacao_tz = pytz.timezone('America/Curacao')
        utc_now = datetime.now(pytz.utc)
        curacao_now = utc_now.astimezone(curacao_tz)
        if cron_name:
            cron_track_id = self.env['cron.track'].search(
                [('cron_name', '=', cron_name)])
            cron_obj = self.env['ir.cron'].search([('name', '=', cron_name)])
            if cron_track_id:
                cron_track_id.total_count += 1
                write_vals = {'start_time': cron_track_start_time,
                              'end_time': custom_end_time,
                              'total_time': total_time,
                              'last_date_cron_executed': curacao_now,
                              'total_retries': cron_obj.total_retries}
                cron_track_id.write(write_vals)
            if not cron_track_id:
                create_vals = {
                    'cron_name': cron_name,
                    'start_time': cron_track_start_time,
                    'end_time': custom_end_time,
                    'total_time': total_time,
                    'total_count': int(1),
                    'last_date_cron_executed': curacao_now,
                    'total_retries': cron_obj.total_retries
                }
                cron_track_id = self.env['cron.track'].create(create_vals)
            if cron_track_id and e:
                self.env['cron.track.log'].create({
                    'cron_track_id': cron_track_id.id,
                    'error_msg': e,
                    'error_msg_time': curacao_now
                })
            if cron_track_id:
                cron_track_id.action_send_cron_status()

    @api.model
    def _callback(self, cron_name, server_action_id, job_id):
        """ Run the method associated to a given job. It takes care of logging
        and exception handling. Note that the user running the server action
        is the user calling this method. """
        try:
            if self.pool != self.pool.check_signaling():
                # the registry has changed, reload self in the new registry
                self.env.reset()
                self = self.env()[self._name]

            log_depth = (None if _logger.isEnabledFor(logging.DEBUG) else 1)
            odoo.netsvc.log(_logger, logging.DEBUG, 'cron.object.execute',
                            (self._cr.dbname, self._uid, '*', cron_name,
                             server_action_id), depth=log_depth)
            start_time = False
            if _logger.isEnabledFor(logging.DEBUG):
                start_time = time.time()
            global custom_start_time
            custom_start_time = time.time()

            # Convert the current time to Curaçao time
            utc_now = datetime.now(pytz.utc)
            curacao_tz = pytz.timezone('America/Curacao')
            cron_track_start_time = utc_now.astimezone(curacao_tz).strftime("%H:%M:%S")

            self.env['ir.actions.server'].browse(server_action_id).run()
            custom_end_time = time.time()

            if start_time and _logger.isEnabledFor(logging.DEBUG):
                end_time = time.time()
                _logger.debug('%.3fs (cron %s, server action %d with uid %d)',
                              end_time - start_time, cron_name,
                              server_action_id, self.env.uid)
            
            # Convert the end time to Curaçao time
            cron_track_end_time = datetime.now(pytz.utc).astimezone(curacao_tz).strftime("%H:%M:%S")
            last_date_cron_executed = datetime.now(pytz.utc).astimezone(curacao_tz).strftime("%H:%M:%S")
            
            total_time = custom_end_time - custom_start_time
            self.create_cron_track(cron_name, cron_track_start_time,
                                   cron_track_end_time, total_time)
            self.pool.signal_changes()
        except Exception as e:
            custom_end_time = time.time()
            total_time = custom_end_time - custom_start_time
            
            # Convert the end time to Curaçao time in case of an exception
            cron_track_end_time = datetime.now(pytz.utc).astimezone(curacao_tz).strftime("%H:%M:%S")
            
            self.pool.reset_changes()
            _logger.exception(
                "Call from cron %s for server action #%s failed in Job #%s",
                cron_name, server_action_id, job_id)
            # Auto Commit start
            cron_id = self.env['ir.cron'].search([('name', '=', cron_name)])
            if cron_id and cron_id.auto_commit:
                cron_id.model_id._cr.commit()
            # Auto Commit end
            if cron_id and not cron_id.auto_commit:
                self._handle_callback_exception(cron_name, server_action_id,
                                                job_id, e)
            if cron_name:
                self.create_cron_track(cron_name, cron_track_start_time,
                                       cron_track_end_time, total_time, e)
