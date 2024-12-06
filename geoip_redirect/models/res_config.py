# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   If not, see <https://store.webkul.com/license.html/>
#
#################################################################################

from odoo import api, fields, models, _
from odoo.http import request

class GeoIPRedirectSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    _name = 'geoip.redirect.settings'
    _description = 'Geoip Redirect'

    first_visit = fields.Boolean(string="First visit redirect only", help="Enable redirect for only first or for each visit")
    enable_geoip = fields.Boolean(string="Enable GeoIP Redirect")
    enable_auto_redirect = fields.Boolean(string="Enable Auto Redirect")
    hide_odoo_languages = fields.Boolean(string="Hide Languages From Website")
    show_geo_country = fields.Boolean(string='Show Geo Country')
    ignore_search_engines = fields.Text(string="Search Engines To Ignore")

    def set_values(self):
        super(GeoIPRedirectSettings, self).set_values()
        first_visit = self.env['ir.default'].sudo().get('geoip.redirect.settings', 'first_visit')
        ignore_search_engines = self.env['ir.default'].sudo().get('geoip.redirect.settings', 'ignore_search_engines')
        if first_visit != self.first_visit:
            request.session['geocountry_code'] = ''
        if ignore_search_engines != self.ignore_search_engines:
            self.setSearchEngines(self.ignore_search_engines)

        IrDefault = self.env['ir.default'].sudo()
        IrDefault.set('geoip.redirect.settings', 'first_visit', self.first_visit)
        IrDefault.set('geoip.redirect.settings', 'enable_auto_redirect', self.enable_auto_redirect)
        IrDefault.set('geoip.redirect.settings', 'enable_geoip', self.enable_geoip)
        IrDefault.set('geoip.redirect.settings', 'ignore_search_engines', self.ignore_search_engines)
        IrDefault.set('geoip.redirect.settings', 'hide_odoo_languages', self.hide_odoo_languages)
        IrDefault.set('geoip.redirect.settings', 'show_geo_country', self.show_geo_country)
        return True

    def get_values(self):
        res = super(GeoIPRedirectSettings, self).get_values()
        IrDefault = self.env['ir.default'].sudo()
        res.update({
            'first_visit':IrDefault.get('geoip.redirect.settings','first_visit', self.first_visit),
            'enable_auto_redirect':IrDefault.get('geoip.redirect.settings','enable_auto_redirect', self.enable_auto_redirect),
            'enable_geoip':IrDefault.get('geoip.redirect.settings','enable_geoip', self.enable_geoip),
            'ignore_search_engines':IrDefault.get('geoip.redirect.settings','ignore_search_engines', self.ignore_search_engines),
            'hide_odoo_languages':IrDefault.get('geoip.redirect.settings','hide_odoo_languages', self.hide_odoo_languages),
            'show_geo_country':IrDefault.get('geoip.redirect.settings','show_geo_country', self.show_geo_country),
        })
        return res

    def setSearchEngines(self, ignore_search_engines):
        viewObj = self.env['ir.ui.view'].sudo().search([('name', '=', 'website.robots')])
        if viewObj:
            arch_base = """<?xml version="1.0"?>
<t t-name="website.robots">
User-agent: *
Sitemap: <t t-esc="url_root"/>sitemap.xml
</t>
            """
            if ignore_search_engines:
                searchEngines = ignore_search_engines.split(",")
                data = ''
                for searchEngine in searchEngines:
                    searchEngine = "User-agent: {}\nDisallow: /".format(searchEngine)
                    data = "{}\n{}".format(data, searchEngine)
                if data:
                    arch_base = """<?xml version="1.0"?>
<t t-name="website.robots">
{}
Sitemap: <t t-esc="url_root"/>sitemap.xml
</t>
                    """.format(data)
            if arch_base:
                viewObj[0].arch_base = arch_base
        return True
