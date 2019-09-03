# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import odoo.addons.decimal_precision as dp


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    name = fields.Char(related='move_id.name', readonly=True)
    service_lot_id = fields.Many2one('stock.production.lot', ondelete='restrict', string='Serviced Serial #')
    create_service = fields.Boolean(related='location_dest_id.create_service', store=True)

    def _prepare_certification_service_values(self):
        self.ensure_one()
        return {
            'name': self.name or self.move_id.name,
            'company_id': self.picking_id.company_id.id,
            'product_id': self.product_id.id,
            'lot_id': self.service_lot_id.id,
            'move_line_id': self.id,
            'group_id': self.move_id.group_id.id,
            'date_calibration': self.move_id.group_id.sale_id.date_calibration if self.move_id.group_id and self.move_id.group_id.sale_id else False
        }
    
    @api.multi
    def generate_certification_service(self):
        for sml in self:
            if sml.create_service and sml.product_id and sml.service_lot_id and sml.move_id.group_id:
                if not self.env['certification.service'].search([('move_line_id', '=', sml.id)]):
                    service = self.env['certification.service'].create(sml._prepare_certification_service_values())
                    # auto create reading
                    service.generate_readings(service.lot_id.element_ids, service.required_reading_count())
                        

    @api.multi
    def check_certification_services_done(self):
        service_ids = self.env['certification.service'].search([('move_line_id', 'in', self.ids)])
        if service_ids and any(service_ids.filtered(lambda service: service.state != 'done')):
            return False
        return True
