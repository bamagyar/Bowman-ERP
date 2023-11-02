# -*- coding: utf-8 -*-
from odoo import models, fields


class StockLocation(models.Model):
    _inherit = 'stock.location'

    create_service = fields.Boolean('Create Service')


class StockProductionLot(models.Model):
    _inherit = 'stock.production.lot'

    labeled_value_ids = fields.One2many('certification.labeled.value', 'lot_id', string='Labeled Values')
    manufacturer_id = fields.Many2one('certification.manufacturer', ondelete='restrict', string='Manufacturer')
