# -*- coding: utf-8 -*-
#################################################################################
# Author      : Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# Copyright(c): 2015-Present Webkul Software Pvt. Ltd.
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <https://store.webkul.com/license.html/>
#################################################################################
{
    "name":  "GeoIP Redirect",
    "summary":  """Odoo GeoIP Redirect provides you a unique and extraordinary feature to detect your customer's IP and show them the website in their own language and currency.GeoIP Location in Orders
Location-based on IP Address
Odoo GeoIP Location in Orders
Location in Orders
GeoIP 
Track location
Track IP address
Customer’s location
Track Customers Location
Customer’s IP
Pinpoint customer’s location
Geological Address
Internet Protocol
Track IP Address For Location
Redirect
GeoIP
Odoo GeoIP Redirect
GeoIP Redirection
URL GeoIP Redirection
Auto-detect IP address
IP address Redirection""",
    "category":  "Website",
    "version":  "1.5",
    "sequence":  1,
    "author":  "Webkul Software Pvt. Ltd.",
    "license":  "Other proprietary",
    "website":  "https://store.webkul.com/Odoo-GeoIP-Redirect.html",
    "description":  """GeoIP Location in Orders
Location-based on IP Address
Odoo GeoIP Location in Orders
Location in Orders
GeoIP 
Track location
Track IP address
Customer’s location
Track Customers Location
Customer’s IP
Pinpoint customer’s location
Geological Address
Internet Protocol
Track IP Address For Location
Redirect
GeoIP
Odoo GeoIP Redirect
GeoIP Redirection
URL GeoIP Redirection
Auto-detect IP address
IP address Redirection""",
    "live_test_url":  "http://odoodemo.webkul.com/?module=geoip_redirect",
    "depends":  [
        'website_sale',
        'website_webkul_addons',
    ],
    "data":  [
        'views/website_templates.xml',
        'security/ir.model.access.csv',
        'views/restricted_ip_view.xml',
        'views/country_mapping_view.xml',
        'views/geoip_menu.xml',
        'views/res_config_view.xml',
        'views/webkul_addons_config_inherit_view.xml',
        'data/data_geoip.xml',
    ],
    "assets": {
        'web.assets_frontend': [
            '/geoip_redirect/static/src/css/wk_geoip.css',
            '/geoip_redirect/static/src/js/wk_geoip.js',
        ],
    },
    "images":  ['static/description/Banner.png'],
    "application":  True,
    "installable":  True,
    "auto_install":  False,
    "price":  99,
    "currency":  "USD",
    "pre_init_hook":  "pre_init_check",
}
