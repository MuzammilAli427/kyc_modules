
from odoo import api, fields, tools, models, _
import json


class account_journal(models.Model):
    _inherit = "account.journal"

    def action_get_account_moves(self):
        self.ensure_one()
        extra_domain = []
        if not self.env.user.has_group('bit_accounting_dashboard.group_accounting_dashboard'):
            label_data = self.env['label.data'].search([])
            if label_data:
                extra_domain = ['|'] * (len(label_data) - 1)
                for rec in label_data:
                    extra_domain += [('name','ilike', '%' + rec.name + '%')]
        action_data = self.env['ir.actions.act_window']._for_xml_id('account.action_account_moves_all')
        action_data['domain'] = [('display_type', 'not in', ('line_section', 'line_note')), ('parent_state', '!=', 'cancel')] + (extra_domain or [])
        action_data['context'] = {'journal_type':'general', 'search_default_posted':1}
        return action_data



class AccountingStatmentLine(models.Model):
    _inherit = 'account.bank.statement.line'


    @api.model
    def _action_open_bank_reconciliation_widget(self, extra_domain=None, default_context=None, name=None, kanban_first=True):
        if not self.env.user.has_group('bit_accounting_dashboard.group_accounting_dashboard'):
            label_data = self.env['label.data'].search([])
            if label_data:
                extra_domain = ['|'] * (len(label_data) - 1)
                for rec in label_data:
                    extra_domain += [('payment_ref','ilike', '%' + rec.name + '%')]
        context = default_context or {}
        views = [
            (self.env.ref('account_accountant.view_bank_statement_line_kanban_bank_rec_widget').id, 'kanban'),
            (self.env.ref('account_accountant.view_bank_statement_line_tree_bank_rec_widget').id, 'list'),
        ]
        return {
            'name': name or _("Bank Reconciliation"),
            'type': 'ir.actions.act_window',
            'res_model': 'account.bank.statement.line',
            'context': context,
            'search_view_id': [self.env.ref('account_accountant.view_bank_statement_line_search_bank_rec_widget').id, 'search'],
            'view_mode': 'kanban,list' if kanban_first else 'list,kanban',
            'views': views if kanban_first else views[::-1],
            'domain': [('state', '!=', 'cancel')] + (extra_domain or []),
            'help': _("""
                <p class="o_view_nocontent_smiling_face">
                    Nothing to do here!
                </p>
                <p>
                    No transactions matching your filters were found.
                </p>
            """),
        }

class LabelData(models.Model):
    _name = 'label.data'

    name = fields.Char('Label')