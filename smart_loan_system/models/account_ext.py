from odoo import api, fields, models, _


class AccountExt(models.Model):
    _inherit = 'account.account'

    transfer_account_id = fields.Many2one('account.account')
    transfer_type = fields.Selection([('no', 'No'),
                                      ('draft', 'Create in Draft'),
                                      ('create_validate', 'Create and Validate')], default='no',)
