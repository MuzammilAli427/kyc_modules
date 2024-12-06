# -*- coding: utf-8 -*-
##############################################################################
#                                                                            #
# Part of Caret IT Solutions Pvt. Ltd. (Website: www.caretit.com).           #
# See LICENSE file for full copyright and licensing details.                 #
#                                                                            #
##############################################################################

from odoo import models, fields


class CronTrackLog(models.Model):
    _name = "cron.track.log"
    _order = "error_msg_time desc"
    _description = "Cron Tracking"

    cron_track_id = fields.Many2one('cron.track')
    error_msg = fields.Text(string="Error Message")
    error_msg_time = fields.Datetime(string="Error DateTime")
