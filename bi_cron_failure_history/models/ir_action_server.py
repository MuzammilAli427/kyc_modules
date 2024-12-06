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




class ServerActions(models.Model):
    """ Add email option in server actions. """
    _name = 'ir.actions.server'
    _description = 'Server Action'
    _inherit = ['ir.actions.server']


    activity_type_id = fields.Many2one(
        'mail.activity.type', string='Activity',
        domain="['|', ('res_model', '=', False), ('res_model', '=', model_name)]",
        ondelete='restrict')

    res_model = fields.Many2one('ir.model', 'Document Model', ondelete='cascade')

    
    
    def run(self):
        """ Runs the server action. For each server action, the
        :samp:`_run_action_{TYPE}[_multi]` method is called. This allows easy
        overriding of the server actions.

        The `_multi` suffix means the runner can operate on multiple records,
        otherwise if there are multiple records the runner will be called once
        for each

        :param dict context: context should contain following keys

                             - active_id: id of the current object (single mode)
                             - active_model: current model that should equal the action's model

                             The following keys are optional:

                             - active_ids: ids of the current records (mass mode). If active_ids
                               and active_id are present, active_ids is given precedence.

        :return: an action_id to be executed, or False is finished correctly without
                 return action
        """
        res = False
        for action in self.sudo():
            action_groups = action.groups_id
            if action_groups:
                if not (action_groups & self.env.user.groups_id):
                    raise AccessError(_("You don't have enough access rights to run this action."))
            else:
                try:
                    self.env[action.model_name].check_access_rights("write")
                except AccessError:
                    _logger.warning("Forbidden server action %r executed while the user %s does not have access to %s.",
                        action.name, self.env.user.login, action.model_name,
                    )
                    raise

            eval_context = self._get_eval_context(action)
            records = eval_context.get('record') or eval_context['model']
            records |= eval_context.get('records') or eval_context['model']
            if records:
                try:
                    records.check_access_rule('write')
                except AccessError:
                    _logger.warning("Forbidden server action %r executed while the user %s does not have access to %s.",
                        action.name, self.env.user.login, records,
                    )
                    raise

            runner, multi = action._get_runner()
            if self._context.get('from_direct'):
                if runner and multi:
                    # call the multi method
                    run_self = action.with_context(eval_context['env'].context)
                    res = runner(run_self, eval_context=eval_context)
                elif runner:
                    active_id = self._context.get('active_id')
                    if not active_id and self._context.get('onchange_self'):
                        active_id = self._context['onchange_self']._origin.id
                        if not active_id:  # onchange on new record
                            res = runner(action, eval_context=eval_context)
                    active_ids = self._context.get('active_ids', [active_id] if active_id else [])
                    for active_id in active_ids:
                        # run context dedicated to a particular active_id
                        run_self = action.with_context(active_ids=[active_id], active_id=active_id)
                        eval_context["env"].context = run_self._context
                        res = runner(run_self, eval_context=eval_context)
                else:
                    _logger.warning(
                        "Found no way to execute server action %r of type %r, ignoring it. "
                        "Verify that the type is correct or add a method called "
                        "`_run_action_<type>` or `_run_action_<type>_multi`.",
                        action.name, action.state
                    )
                return res or False
            else:
                try:
                    if runner and multi:
                        # call the multi method
                        run_self = action.with_context(eval_context['env'].context)
                        res = runner(run_self, eval_context=eval_context)
                    elif runner:
                        active_id = self._context.get('active_id')
                        if not active_id and self._context.get('onchange_self'):
                            active_id = self._context['onchange_self']._origin.id
                            if not active_id:  # onchange on new record
                                res = runner(action, eval_context=eval_context)
                        active_ids = self._context.get('active_ids', [active_id] if active_id else [])
                        for active_id in active_ids:
                            # run context dedicated to a particular active_id
                            run_self = action.with_context(active_ids=[active_id], active_id=active_id)
                            eval_context["env"].context = run_self._context
                            res = runner(run_self, eval_context=eval_context)
                    else:
                        _logger.warning(
                            "Found no way to execute server action %r of type %r, ignoring it. "
                            "Verify that the type is correct or add a method called "
                            "`_run_action_<type>` or `_run_action_<type>_multi`.",
                            action.name, action.state
                        )
                    return res or False
                except Exception as e:
                    cron = self.env['ir.cron'].search([('name', '=', action.name)], limit = 1)
                    
                    a = self.env['cron.notify'].search([('name', '=', 'Cron Failure History')], limit = 1)
                    if not a:
                        raise UserError(_('Please upgrade the module!'))
        
                    manager_id = self.env['ir.model.data'].sudo().get_object_reference('base','group_system')[1]
                    group_manager = self.env['res.groups'].sudo().browse(manager_id)
                    super_user = group_manager.users[0]
                    tz = pytz.timezone(super_user.tz or 'UTC')
                    tz_time = datetime.now(tz=tz).strftime("%H:%M:%S")
                    dt_str = datetime.now(tz=tz).strftime("%Y-%m-%d %H:%M:%S")
                    
                    msg_dis= (" Dear Team <br><br>I have noticed error/exception during running of cron job in odoo with below details <br><br>  Cron job name: %s <br>  Date time of run: %s <br>  Details  %s <br> <br>Regards. <br> YourCompany "
                     %(cron.name, dt_str, e))
                    a.message_post(body=msg_dis)
                    
                    
                    msg_dis_on_cron= ("Cron job name: %s <br>  Date time of run: %s <br>  Details  %s"
                     %(cron.name, dt_str, e))
                    
                    for obj_cron in cron:
                        activity_exception = obj_cron.activity_schedule('mail.mail_activity_data_warning', note=msg_dis_on_cron, user_id= super_user.id, summary='Scheduler Cron Fail',)
                        activity_exception.notes = e
                        activity_exception.dt = dt_str
                
                
                
                
                
                
                
