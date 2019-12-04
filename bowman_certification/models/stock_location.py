# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import odoo.addons.decimal_precision as dp


class StockLocation(models.Model):
    _inherit = 'stock.location'

    create_service = fields.Boolean('Create Service')
