from odoo import models, fields, api, _


class KycGroupRoles(models.Model):
    _name = 'kyc.group.roles'
    _description = 'This model contains the Group roles assigned to the users'
    _rec_name = 'name'

    name = fields.Char()


"""
    **=================================================================**
    ** This model is to assign multiple group roles to a single member **
    **=================================================================**
"""
