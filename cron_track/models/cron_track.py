# -*- coding: utf-8 -*-
##############################################################################
#                                                                            #
# Part of Caret IT Solutions Pvt. Ltd. (Website: www.caretit.com).           #
# See LICENSE file for full copyright and licensing details.                 #
#                                                                            #
##############################################################################

from odoo import models, fields, _, api
from odoo.exceptions import ValidationError, UserError
from pytz import timezone


class CronTrack(models.Model):
    _name = "cron.track"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Cron Track"
    _rec_name = 'cron_name'

    cron_name = fields.Char(string="Cron Name")
    start_time = fields.Char(string="Start Time")
    end_time = fields.Char(string="End Time")
    total_time = fields.Char(string="Total Taken Time (in Sec)")
    total_count = fields.Integer(
        string="Total Count Of Cron Executed", default=0
    )
    last_date_cron_executed = fields.Char(string="Last Date Cron Executed")
    last_date_cron_executed_curacao = fields.Datetime(
        string="Last Date Cron Executed (Curaçao)",
        compute="_compute_last_date_cron_executed_curacao"
    )
    user_id = fields.Many2one('res.users', string="User")
    failed_cron_count = fields.Integer(
        string="Cron Failed Count", compute="compute_failed_cron_count"
    )
    total_retries = fields.Integer(string='Total Retries Count')
    cron_track_log = fields.One2many(
        'cron.track.log', 'cron_track_id',
        string="Cron Track Log"
    )

    @api.depends('last_date_cron_executed')
    def _compute_last_date_cron_executed_curacao(self):
        for record in self:
            if record.last_date_cron_executed:
                curacao_tz = timezone('America/Curacao')
                utc_timestamp = fields.Datetime.from_string(record.last_date_cron_executed)
                utc_timestamp = fields.Datetime.context_timestamp(record, utc_timestamp)
                record.last_date_cron_executed_curacao = utc_timestamp.astimezone(curacao_tz)
            else:
                record.last_date_cron_executed_curacao = False

    @api.model
    def create(self, vals):
        if 'last_date_cron_executed' in vals and isinstance(vals['last_date_cron_executed'], str):
            vals['last_date_cron_executed'] = fields.Datetime.to_string(
                fields.Datetime.from_string(vals['last_date_cron_executed'])
            )
        return super(CronTrack, self).create(vals)

    def write(self, vals):
        if 'last_date_cron_executed' in vals and isinstance(vals['last_date_cron_executed'], str):
            vals['last_date_cron_executed'] = fields.Datetime.to_string(
                fields.Datetime.from_string(vals['last_date_cron_executed'])
            )
        return super(CronTrack, self).write(vals)

    def open_cron_tracking(self):
        """open cron track log """
        action = self.env.ref('cron_track.action_cron_tracking_log').read()[0]
        cron_log_ids = self.mapped('cron_track_log')
        if not cron_log_ids:
            raise ValidationError(
            _("There is no Cron Tracking Log Because "
              "Every Time Cron Executed Successfully"))
        if len(cron_log_ids) > 1:
            action['domain'] = [('id', 'in', cron_log_ids.ids)]
        elif cron_log_ids:
            action['views'] = [(self.env.ref(
                'cron_track.cron_track_tracking_log_form_view').id, 'form')]
            action['res_id'] = cron_log_ids.id
        if cron_log_ids:
            return action

    def action_send_cron_status(self):
        """Send mail to User about the cron tracking log."""

        template_id = self.env.ref('cron_track.cron_status_template', False)
        if not template_id:
            raise UserError(_("Email template not found."))

        template_values = template_id.generate_email([self.id], ['body_html', 'subject'])[self.id]
        email_body = template_values.get('body_html')

        if email_body:
            email_body = email_body.replace('Loan Robots', self.cron_name)

        cron_obj = self.env['ir.cron'].search(
            ['|', ('active', '=', True), ('active', '=', False), ('name', '=', self.cron_name)])

        ctx = {
            'default_model': 'cron.track',
            'default_res_id': self.id,
            'default_use_template': bool(template_id),
            'default_template_id': template_id.id,
            'default_composition_mode': 'comment',
            'force_send': True,
        }

        compose = self.env['mail.compose.message'].with_context(ctx).create({
            'subject': template_values.get('subject', f'Cron Status Update: {self.cron_name}'),
            'model': 'cron.track',
            'res_id': self.id,
            'body': email_body,  # Use the dynamically generated email body
            'email_from': self.env.user.email_formatted,
            'partner_ids': cron_obj.partner_ids.ids if cron_obj else False
        })

        compose.action_send_mail()

        return True

    def compute_failed_cron_count(self):
        """count fail cron record"""
        for res in self:
            total_len = len(
                self.env['cron.track.log'].search([('cron_track_id', '=',
                                                    res.cron_name)]))
            res.failed_cron_count = total_len
