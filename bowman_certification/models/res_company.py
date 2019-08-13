# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models, fields

class ResCompany(models.Model):
    _inherit = 'res.company'

    reading_uom_id = fields.Many2one('uom.uom', ondelete='set null', string='Reading Unit of Measure')
