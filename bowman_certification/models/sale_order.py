# -*- coding: utf-8 -*-

from odoo import api, models, fields

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    date_calibration = fields.Date(string='Calibration Date')
