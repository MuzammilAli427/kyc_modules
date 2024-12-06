# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   If not, see <https://store.webkul.com/license.html/>
#
#################################################################################

from odoo import models
from odoo.http import request
import requests

class Website(models.Model):
    _inherit = "website"

    def get_countries(self):
        countries = self.env['country.mapping'].sudo().search([])
        self.get_default_country()
        return countries

    def get_blocked_ip_countries(self):
        restrictIpList = []
        restrictCountryCodeList = []
        restrictIPs = self.env['restricted.ip'].sudo().search([])
        for restrictIP in restrictIPs:
            if restrictIP.restrict_by == 'ip':
                restrictIpList.append(restrictIP.ip_address)
            if restrictIP.restrict_by == 'country':
                restrictIpList.append(restrictIP.country_id.name)
                restrictCountryCodeList.append(restrictIP.country_id.code)
        if restrictIpList:
            ip = request.httprequest.environ.get('HTTP_X_REAL_IP')
            if not ip:
                ip = request.httprequest.environ.get('REMOTE_ADDR')
            ipUrl = "{}/{}/json".format("https://ipapi.co", ip)
            currentLocation = requests.get(ipUrl)
            if currentLocation.status_code == 200:
                data = currentLocation.json()
                if data.get('ip'):
                    if data.get('ip') in restrictIpList:
                        return True
                if data.get('country'):
                    if data.get('country') in restrictIpList:
                        return True
                    else:
                        if data.get('country_code') in restrictCountryCodeList:
                            return True
        return False

    def get_default_country(self, defCountry=''):
        if defCountry:
            request.session['geocountry'] = defCountry
        else:
            defaultCountry = request.session.get('geocountry')
            if not defaultCountry:
                langCode = self.sudo().get_current_website().default_lang_id.url_code
                if langCode:
                    defLang = self.env['res.lang'].sudo().search([('code', '=', langCode)], limit=1)
                    if defLang:
                        defCountries = self.env['country.mapping'].sudo().search([('lang_id', '=', defLang.id)], limit=1)
                        if defCountries:
                            request.session['geocountry'] = [defCountries.country_id.id, defCountries.country_id.name]
        return True
