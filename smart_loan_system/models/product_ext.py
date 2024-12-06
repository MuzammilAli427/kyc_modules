# -*-coding: utf-8 -*-

from odoo import fields, models, api, _


class ProductExt(models.Model):
    _inherit = "product.template"

    automatic_transfer = fields.Boolean(default=False)
