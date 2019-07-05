# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import odoo.addons.decimal_precision as dp


class CertificationElement(models.Model):
    _name = 'certification.element'
    _description = 'Certification Element'

    name = fields.Char('Name', required=True)
    short_name = fields.Char('Short Name', required=True)
    density = fields.Float('Density', digits=dp.get_precision('Certification Service'), required=True)


class CertificationService(models.Model):
    _name = 'certification.service'
    _description = 'Certification Service'

    name = fields.Char('Name') # todo: add sequence to this
    product_id = fields.Many2one('product.product', ondelete='restrict', string='Product', required=True, readonly=True)
    lot_id = fields.Many2one('stock.production.lot', ondelete='restrict', string='Lot/Serial', required=True, readonly=True)
    move_line_id = fields.Many2one('stock.move.line', ondelete='set null', string='Packing Operation', required=True, readonly=True)
    group_id = fields.Many2one('procurement.group', ondelete='set null', string='Procurement Group', readonly=True, required=True)
    state = fields.Selection([('draft', 'Draft'), ('working_on', 'Working On'), ('done', 'Done')], string='State', default='draft', required=True)
    reading_ids = fields.One2many('certification.reading', 'service_id', string='Readings', readonly=True, states={'working_on': [('readonly', False)]})
    result_ids = fields.One2many('certification.result', 'service_id', string='Results', readonly=True)
    element_id = fields.Many2one('certification.element', ondelete='set null', string='Element', states={'done': [('readonly', True)]})
    is_pass = fields.Boolean('Pass', states={'done': [('readonly', True)]})
    date_calibration = fields.Date('Calibration Date', states={'done': [('readonly', True)]})
    date_received = fields.Datetime('Received Date', related='move_line_id.move_id.date', states={'done': [('readonly', True)]})
    standard_ids = fields.One2many('in.house.standard', 'service_id', string='In House Standards', states={'done': [('readonly', True)]})

    def action_start(self): # this is the same button as reopen, so no need to filter
        self.write({'state': 'working_on'})

    def action_finish(self):
        # todo: check the amount of reading
        self.filtered(lambda service: service.state == 'working_on').write({'state': 'done'})

    def action_compute_result(self):
        self.ensure_one()
        if self.result_ids:
            self.result_ids.sudo().unlink()
        unique_elements = {}
        for reading in self.reading_ids:
            if reading.element_id not in unique_elements:
                unique_elements[reading.element_id] = [0.0, 0]
            unique_elements[reading.element_id][0] += reading.reading
            unique_elements[reading.element_id][1] += 1
        # check reading count
        for element in unique_elements.keys():
            if unique_elements.get(element)[1] < 5:
                raise ValidationError(_('Element {} has less than 5 readings.'.format(element.name)))
        for element in unique_elements.keys():
            average = unique_elements.get(element)[0] / unique_elements.get(element)[1]
            label, diff = 0.0, 0.0
            label_value_ids = self.lot_id.labeled_value_ids.filtered(lambda lv: lv.element_id == element)
            if label_value_ids:
                label = label_value_ids[0].value
                diff = abs(average - label) # todo: do the uom convertion
            self.env['certification.result'].create({
                'element_id': element.id,
                'service_id': self.id,
                'average': average,
                'diff_from_label': diff,
                'percent_diff_from_label': (diff/label) * 100.0 if label else 0.0,
                'state': 'pass' if diff < 10.0 else 'fail',
            })
            

class CertificationReading(models.Model):
    _name = 'certification.reading'
    _description = 'Certification Reading'

    name = fields.Char('Name')
    description = fields.Text('Description')
    sequence = fields.Integer('Sequence')
    reading = fields.Float('Reading', digits=dp.get_precision('Certification Service'), required=True, )
    element_id = fields.Many2one('certification.element', ondelete='restrict', string='Element')
    service_id = fields.Many2one('certification.service', ondelete='restrict', string='Certification Service')
    density = fields.Float(digits=dp.get_precision('Certification Service'), related='element_id.density', readonly=True)

    
class CertificationResult(models.Model):
    _name = 'certification.result'
    _description = 'Certification Result'

    name = fields.Char('Name')

    element_id = fields.Many2one('certification.element', ondelete='restrict', string='Element')
    service_id = fields.Many2one('certification.service', ondelete='restrict', string='Certification Service')

    average = fields.Float('Average', digits=dp.get_precision('Certification Service'))

    diff_from_label = fields.Float('Diff. from Label', digits=dp.get_precision('Certification Service'))
    percent_diff_from_label = fields.Float('% Diff. from Labeled', digits=dp.get_precision('Certification Service'))
    state = fields.Selection([('pass', 'Pass'), ('fail', 'Fail')], string='Pass/Fail')
    
    
class InHouseStandard(models.Model):
    _name = 'in.house.standard'
    _description = 'In House Standard'

    element_id = fields.Many2one('certification.element', ondelete='set null', string='Element', required=True,)
    name = fields.Char(related='element_id.name')
    
    service_id = fields.Many2one('certification.service', ondelete='restrict', string='Certification Service', required=True,)
    lot_id = fields.Many2one('stock.production.lot', ondelete='restrict', string='Ref No.', required=True,)

    initial_reading = fields.Char('Ref Initial Reading', required=True,)
    subsequent = fields.Char('Ref Subsequent', required=True,)

    
class CertificationLabeledValue(models.Model):
    _name = 'certification.labeled.value'
    _description ='Certification Labeled Value'

    name = fields.Char('Name')
    value = fields.Float('Value', digits=dp.get_precision('Certification Service'))
    lot_id = fields.Many2one('stock.production.lot', ondelete='restrict', string='Lot/Serial')
    element_id = fields.Many2one('certification.element', ondelete='restrict', string='Element')
    uom_id = fields.Many2one('product.uom', ondelete='restrict', string='Unit of Measure')
