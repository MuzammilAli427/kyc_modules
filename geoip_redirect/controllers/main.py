# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   If not, see <https://store.webkul.com/license.html/>
#
#################################################################################

import logging

import requests

from odoo import http
from odoo.addons.website.controllers.main import Website
from odoo.http import request

_logger = logging.getLogger("## GEOIP ##")

class Website(Website):

    def check_first_visit(self,country_code,country_name):
        IrDefault = request.env['ir.default'].sudo()
        geocountry_code = request.session.get('geocountry_code')
        geocountry_session = request.session.get('geocountry')
        first_visit = IrDefault.get('geoip.redirect.settings', 'first_visit')
        enable_auto_redirect = IrDefault.get('geoip.redirect.settings', 'enable_auto_redirect')
        geocountry = geocountry_session[1] if not first_visit and enable_auto_redirect and geocountry_session else geocountry_code
        if geocountry and self.checkGeoCountry(geocountry, country_code, country_name):
            return False
        if first_visit:
            request.session['geocountry_code'] = country_code
        else:
            request.session['geocountry_code'] = ''
        return True 
        
    @http.route(['/change/country'], type='json', auth="public", methods=['POST'], website=True)
    def change_country(self, countryId='', lang=''):
        ctx = dict(request.context or {})
        if countryId:
            countryId = int(countryId)
            ctx['country'] = countryId
            request.context = ctx
            if lang:
                ctx['lang'] = lang
            countryObj = request.env['res.country'].sudo().with_context(ctx).browse(countryId)
            pricelistId = self.getPricelist(lang, countryId)
            if pricelistId:
                request.session['website_sale_current_pl'] = pricelistId
                request.website.sale_get_order(update_pricelist=True)
            request.env['website'].get_default_country([countryObj.id, countryObj.name])
        return True

    @http.route(['/redirect/location'], type='json', auth="public", methods=['POST'], website=True)
    def redirect_location(self,**kw):
        ip, country_code, country_name, country_obj = kw.get('ip'), kw.get('country_code'), kw.get('country_name'), False
        if country_code and country_name:
            country_obj = self.getCountryObject(country_code, country_name)
        else:
            country_code, country_name, country_obj = self.getCountry(ip)
        contextLang = request.context.get('lang')
        langCode = request.session.context.get('lang')
        customUrl = ''
        pricelist_id = 0
        redirect = False
        geocountry = request.session.get('geocountry_code')
        if country_code or country_name:
            enable_geoip = request.env['ir.default'].sudo().get('geoip.redirect.settings', 'enable_geoip')
            enable_auto_redirect = request.env['ir.default'].sudo().get('geoip.redirect.settings', 'enable_auto_redirect')
            if not enable_geoip:
               return  False
            redirect = enable_auto_redirect
            if enable_auto_redirect:
                if self.check_first_visit(country_code,country_name):
                    redirect = True
                else:
                    redirect = False
            else: 
                if self.check_first_visit(country_code,country_name) and request.session['geocountry_code']:
                    redirect = True
                else:
                    redirect = False
                    
            if country_obj and redirect:
                countryMappingObj = request.env['country.mapping'].sudo().search([('country_id', '=', country_obj.id)], limit=1)
                if countryMappingObj:
                    langCode = countryMappingObj.lang_id.code
                    pricelist_id = countryMappingObj.pricelist_id.id
                    if countryMappingObj.add_url:
                        customUrl = countryMappingObj.custom_url
                    request.session['geocountry'] = [countryMappingObj.country_id.id, countryMappingObj.country_id.name]
                    if country_code:
                        request.session['geocountry_code'] = country_code
                    elif country_name:
                        request.session['geocountry_code'] = country_name
                else:
                    langCode = request.env['website'].sudo().get_current_website().default_lang_id.url_code
                    # pricelist_id = default pricelist
            else:
                langCode = request.env['website'].sudo().get_current_website().default_lang_id.url_code
                # pricelist_id = default pricelist
            if pricelist_id and redirect:
                request.session['website_sale_current_pl'] = pricelist_id
                request.website.sale_get_order(update_pricelist=True)
            
            return redirect and [langCode, contextLang, customUrl]
        else:
            return False

    def checkGeoCountry(self, geocountry, country_code, country_name):
        if country_code and country_code == geocountry:
            return True
        if country_name and country_name == geocountry:
            return True
        return False

    def getPricelist(self, lang, countryId):
        langObj = request.env['res.lang'].search([('code', '=', lang)], limit=1)
        if langObj:
            countryObj = request.env['country.mapping'].search([('country_id', '=', countryId), ('lang_id', '=', langObj.id)], limit=1)
            if countryObj:
                return countryObj.pricelist_id.id
        return False

    def getCountry(self, ip='', countryId=''):
        country_code, country_name = '', ''
        if not ip:
            env = request.httprequest.environ
            ip = env.get('HTTP_X_REAL_IP') or env.get('REMOTE_ADDR')
        if ip:
            ipUrl = "{}/{}/json".format("https://ipapi.co", ip)
            currentLocation = requests.get(ipUrl)
            if currentLocation.status_code == 200:
                data = currentLocation.json()
                country_code = data.get('country_code') or ''
                country_name = data.get('country_name') or ''
        mapped_codes = request.env['country.mapping'].sudo().search([]).mapped('country_id').mapped('code')
        if not(country_code or country_name) or country_code not in mapped_codes:
            _logger.info("No location data found for IP %r"%(ip))
            defCountryObj = request.env.user.company_id.country_id
            country_code = defCountryObj.code
            country_name = defCountryObj.name
        country_obj = request.env['res.country'].sudo().search([
            '|', ('code', '=', country_code), ('name', '=', country_name)], limit=1)
        country_obj = self.getCountryObject(country_code, country_name)
        return [country_code, country_name, country_obj]

    def getCountryObject(self, country_code, country_name):
        country_obj = request.env['res.country'].sudo().search([
            '|', ('code', '=', country_code), ('name', '=', country_name)], limit=1)
        return country_obj
