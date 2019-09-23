# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import odoo.addons.decimal_precision as dp


class StockProductionLot(models.Model):
    _inherit = 'stock.production.lot'

    labeled_value_ids = fields.One2many('certification.labeled.value', 'lot_id', string='Labeled Values')
    manufacturer_id = fields.Many2one('certification.manufacturer', ondelete='restrict', string='Manufacturer')
