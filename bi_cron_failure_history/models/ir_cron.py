# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from itertools import groupby
from datetime import datetime, timedelta
import pytz

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.misc import formatLang
from odoo.tools import html2plaintext
import odoo.addons.decimal_precision as dp





class IrCron(models.Model):
	_name = "ir.cron"
	_inherit = ["ir.cron",'mail.thread', 'mail.activity.mixin']
	
	
	
	def action_schedule_fail_mail_send(self):
		self.ensure_one()
		
		template_id = self.env['ir.model.data']._xmlid_lookup('bi_cron_failure_history.email_template_error_msg_cron')[2]
		
		lang = self.env.context.get('lang')
		template = self.env['mail.template'].sudo().browse(template_id)
		if template.lang:
			lang = template._render_lang(self.ids)[self.id]
		ctx = {
			'default_model': 'ir.cron',
			'default_res_id': self.ids[0],
			'default_use_template': bool(template_id),
			'default_template_id': template_id,
			'default_composition_mode': 'comment',
			'mark_so_as_sent': False,
			'proforma': self.env.context.get('proforma', False),
			'force_email': True,
			'model_description': 'ir.cron,'


			}
		return {
			'type': 'ir.actions.act_window',
			'view_mode': 'form',
			'res_model': 'mail.compose.message',
			'views': [(False, 'form')],
			'view_id': False,
			'target': 'new',
			'context': ctx,
		}
  		
	
	
	

	def method_direct_trigger(self):
		try:
			self.check_access_rights('write')
			for cron in self:
				cron.with_user(cron.user_id).with_context(lastcall=cron.lastcall, from_direct=True).ir_actions_server_id.run()
				cron.lastcall = fields.Datetime.now()
				super(IrCron, self).method_direct_trigger()
			return True

		except Exception as e:
			a = self.env['cron.notify'].search([('name', '=', 'Cron Failure History')], limit = 1)
			if not a:
				raise UserError(_('Please upgrade the module!'))

			manager_id = self.env['ir.model.data'].sudo()._xmlid_lookup('base.group_system')[2]
			group_manager = self.env['res.groups'].sudo().browse(manager_id)
			super_user = group_manager.users[0]
			tz = pytz.timezone(super_user.tz or 'UTC')
			tz_time = datetime.now(tz=tz).strftime("%H:%M:%S")
			dt_str = datetime.now(tz=tz).strftime("%Y-%m-%d %H:%M:%S")
			
			msg_dis= (" Dear Team <br><br>I have noticed error/exception during running of cron job in odoo with below details <br><br>  Cron job name: %s <br>  Date time of run: %s <br>  Details  %s <br> <br>Regards. <br> YourCompany "
			 %(self.name, dt_str, e))
			a.message_post(body=msg_dis)
			
			
			msg_dis_on_cron= ("Cron job name: %s <br>  Date time of run: %s <br>  Details  %s"
			 %(self.name, dt_str, e))
			
			for obj_cron in self:
				activity_exception = obj_cron.activity_schedule('mail.mail_activity_data_warning', note=msg_dis_on_cron, user_id= super_user.id, summary='Scheduler Cron Fail',)
				activity_exception.notes = e
				activity_exception.dt = dt_str
		return True
	
	
	
	
	