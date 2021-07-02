# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import odoo.addons.decimal_precision as dp


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    create_service = fields.Boolean(related='location_dest_id.create_service', store=True)

    # when confirming a transfer that has create service enabled, make sure it has serverce serial #
    # and then upon confirmation there will be a service record created
    # @api.multi
    def button_validate(self):
        self.ensure_one()
        if not self.move_lines and not self.move_line_ids:
            raise UserError(_('Please add some lines to move'))

        # check if source location has create service
        lines_to_check_src = self.move_line_ids.filtered(lambda line: line.location_id and line.location_id.create_service)

        at_least_one_done = False
        for line in lines_to_check_src:
            orig_lines_to_check_src = self.env['stock.move.line']
            for move in line.move_id.move_orig_ids:
                orig_lines_to_check_src |= move.move_line_ids

            if orig_lines_to_check_src and orig_lines_to_check_src.check_certification_services_done():
                at_least_one_done = True
                if line.product_uom_qty:
                    line.qty_done = line.product_uom_qty

        if lines_to_check_src and not at_least_one_done:
            raise ValidationError(_('Certification Error. Cannot validate order if certification services have not been completed'))

        # check if dest location has create service
        if self.create_service:
            lines_to_check_dest = self.move_line_ids.filtered(lambda line: line.create_service and not line.service_lot_id)

            if lines_to_check_dest:
                raise ValidationError(_('You need to supply Serviced Serial # for {}.'.format([line.product_id.display_name for line in lines_to_check_dest])))

        res = super(StockPicking, self).button_validate()

        if res:
            return res

        if self.create_service:
            self.move_line_ids.filtered('create_service').generate_certification_service()
        return
