from odoo import api, fields, models, _


class ResUsersExt(models.Model):
    _inherit = 'res.users'

    is_officer = fields.Boolean('Officer', default=False)
