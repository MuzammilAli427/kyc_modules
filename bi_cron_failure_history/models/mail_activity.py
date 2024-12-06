# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from itertools import groupby
from datetime import datetime, timedelta
import pytz

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.misc import formatLang
from odoo.tools import html2plaintext
import odoo.addons.decimal_precision as dp




class MailActivity(models.Model):
    _inherit = "mail.activity"

    notes = fields.Char(string="Related Note")
    dt = fields.Datetime('DT')


