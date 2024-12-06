# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   If not, see <https://store.webkul.com/license.html/>
#
#################################################################################

from odoo import api, fields, models, _

class CountryMapping(models.Model):
    _name = 'country.mapping'
    _description = 'Country Mapping'

    country_id = fields.Many2one('res.country', 'Country', required=True, copy=True)
    currency_id = fields.Many2one(
        related="country_id.currency_id", string="Currency", readonly=True, store=True)
    pricelist_id = fields.Many2one("product.pricelist", required=True, string="Pricelist")
    lang_id = fields.Many2one("res.lang", string="Languages", required=True)
    add_url = fields.Boolean('Use Custom Url', copy=True)
    custom_url = fields.Char(string='Url')

    @api.onchange('add_url')
    def _onchange_add_url(self):
        if not self.add_url:
            self.custom_url = ''
