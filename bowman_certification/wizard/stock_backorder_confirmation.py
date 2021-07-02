# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class StockBackorderConfirmation(models.TransientModel):
    _inherit = 'stock.backorder.confirmation'

    # @api.one
    def _process(self, cancel_backorder=False):
        self.ensure_one()
        self.pick_ids.action_done()
        for picking in self.pick_ids:
            picking.move_line_ids.filtered(lambda line: line.location_dest_id and line.location_dest_id.create_service).generate_certification_service()
        if cancel_backorder:
            for pick_id in self.pick_ids:
                backorder_pick = self.env['stock.picking'].search([('backorder_id', '=', pick_id.id)])
                backorder_pick.action_cancel()
                pick_id.message_post(body=_("Back order <em>%s</em> <b>cancelled</b>.") % (",".join([b.name or '' for b in backorder_pick])))
