from odoo import api, fields, models, _


class AccountJournalExt(models.Model):
    _inherit = "account.journal"

    search_allowed = fields.Boolean(compute='_compute_search_allowed')

    def _compute_search_allowed(self):
        for rec in self:
            if rec.env.user.has_group('smart_loan_system.group_accounting_search_allow'):
                rec.search_allowed = True
            else:
                rec.search_allowed = False
