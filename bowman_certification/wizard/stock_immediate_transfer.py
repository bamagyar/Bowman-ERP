# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, _
from odoo.exceptions import UserError


class StockImmediateTransfer(models.TransientModel):
    _inherit = 'stock.immediate.transfer'

    def process(self):
        res = super(StockImmediateTransfer, self).process()
        for picking in self.pick_ids.filtered(lambda pick: pick.state == 'done'):
            picking.move_line_ids.filtered(lambda line: line.location_dest_id and line.location_dest_id.create_service).generate_certification_service()
        return res
