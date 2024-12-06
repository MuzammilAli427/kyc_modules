# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   If not, see <https://store.webkul.com/license.html/>
#
#################################################################################

from odoo import api, fields, models, _

class RestrictedIp(models.Model):
    _name = 'restricted.ip'
    _description = 'Restrict Ip'

    def _default_website(self):
        return self.env['website'].search([], limit=1)

    website_id = fields.Many2one('website', string="Website", required=True, default=_default_website)
    ip_address = fields.Char(string='IP Address')
    restrict_by = fields.Selection([
                                ('ip', 'IP'),
                                ('country', 'Country')
                            ],
                            'Restrict By',
                            default="country",
                            help="Restrict website by ip/country")
    country_id = fields.Many2one('res.country', 'Country', copy=True)

    @api.onchange('restrict_by')
    def _onchange_option(self):
        if self.restrict_by == 'ip':
            self.country_id = False
        if self.restrict_by == 'country':
            self.ip_address = ''
        
