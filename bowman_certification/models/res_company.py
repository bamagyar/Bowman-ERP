# -*- coding: utf-8 -*-
from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    reading_uom_id = fields.Many2one('uom.uom', ondelete='set null', string='Reading Unit of Measure')


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    reading_uom_id = fields.Many2one('uom.uom', related='company_id.reading_uom_id', readonly=False)
