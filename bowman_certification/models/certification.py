# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import odoo.addons.decimal_precision as dp


class CertificationElement(models.Model):
    _name = 'certification.element'
    _description = 'Certification Element'

    name = fields.Char('Name', required=True)
    short_name = fields.Char('Short Name', required=True)
    # density = fields.Float('Density', digits=dp.get_precision('Certification Service'), required=True)
    # The density field in the element should be a text field, this is because they need to also type n/a for some densities.
    density = fields.Char('Density', required=True)

class CertificationService(models.Model):
    _name = 'certification.service'
    _description = 'Certification Service'

    name = fields.Char('Name', readonly=True, states={'working_on': [('readonly', False)]}) # todo: add sequence to this
    company_id = fields.Many2one('res.company', ondelete='restrict', string='Company', required=True, readonly=True)
    product_id = fields.Many2one('product.product', ondelete='restrict', string='Product', required=True, readonly=True)
    lot_id = fields.Many2one('stock.production.lot', ondelete='restrict', string='Lot/Serial', required=True, readonly=True)
    move_line_id = fields.Many2one('stock.move.line', ondelete='set null', string='Packing Operation', required=True, readonly=True)
    group_id = fields.Many2one('procurement.group', ondelete='set null', string='Procurement Group', readonly=True, required=True)
    state = fields.Selection([('draft', 'Draft'), ('working_on', 'Working On'), ('done', 'Done')], string='State', default='draft', required=True)
    reading_ids = fields.One2many('certification.reading', 'service_id', string='Readings', readonly=True, states={'working_on': [('readonly', False)]})
    result_ids = fields.One2many('certification.result', 'service_id', string='Results', readonly=True)
    element_ids = fields.Many2many('certification.element', string='Selectable Elements for Current Service', readonly=True, store=True, compute='_compute_element_ids')
    element_id = fields.Many2one('certification.element', ondelete='set null', string='Element', states={'done': [('readonly', True)]})
    is_pass = fields.Boolean('Pass', states={'done': [('readonly', True)]})
    date_calibration = fields.Date('Calibration Date', states={'done': [('readonly', True)]})
    date_received = fields.Datetime('Received Date', related='move_line_id.move_id.date', states={'done': [('readonly', True)]})

    # The in-house standard should not be a one2many, it should be a many2many field (the same standard could be used for several certification services)
    standard_ids = fields.Many2many('in.house.standard', string='In House Standards', states={'done': [('readonly', True)]})

    def _prepare_reading_values(self, element):
        self.ensure_one()
        return {
            'service_id': self.id,
            'element_id': element.id,
            'reading': 0.0,
        }

    def required_reading_count(self):
        return 5

    def generate_readings(self, elements, reading_count):
        for element in elements:
            for i in range(reading_count):
                self.env['certification.reading'].create(service._prepare_reading_values(element))

    @api.multi
    def write(self, vals):
        res = super(CertificationService, self).write(vals)
        for service in self:
            if not service.standard_ids:
                raise ValidationError(_('Must have at least one In House Standard!'))

        return res

    @api.multi
    @api.depends('lot_id', 'lot_id.labeled_value_ids', 'lot_id.labeled_value_ids.element_id')
    def _compute_element_ids(self):
        for service in self:
            service.element_ids = service.lot_id.labeled_value_ids.mapped('element_id')
    
    def action_start(self): # this is the same button as reopen, so no need to filter
        self.write({'state': 'working_on'})
        for cert in self:
            if not cert.reading_ids:
                # generate readings again if not already did in create
                cert.generate_readings(cert.element_ids, cert.required_reading_count())

    def action_finish(self):
        self.filtered(lambda service: service.state == 'working_on').write({'state': 'done'})

    def action_compute_result(self):
        self.ensure_one()
        if not self.company_id or not self.company_id.reading_uom_id:
            raise ValidationError(_('Please define the Unit of Measure for readings in Inventory Setting before proceeding.'))

        reading_uom_id = self.company_id.reading_uom_id
        
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
            required_reading_count = self.required_reading_count()
            if unique_elements.get(element)[1] < required_reading_count:
                raise ValidationError(_('Element {} has less than {} readings.'.format(element.name, required_reading_count)))

        for element in unique_elements.keys():
            average = unique_elements.get(element)[0] / unique_elements.get(element)[1]
            label, diff = 0.0, 0.0
            label_value_ids = self.lot_id.labeled_value_ids.filtered(lambda lv: lv.element_id == element)
            if label_value_ids:
                label_value_id = label_value_ids[0]
                # converted_average = reading_uom_id._compute_quantity(average, label_value_id.uom_id) 
                label = label_value_id.uom_id._compute_quantity(label_value_id.value, reading_uom_id) 
                diff = abs(average - label) 
            self.env['certification.result'].create({
                'element_id': element.id,
                'service_id': self.id,
                'average': average,
                'diff_from_label': diff,
                'percent_diff_from_label': (diff/label) * 100.0 if label else 0.0,
                'state': 'pass' if diff < 4.0 else 'fail', # It appears that the threshold is 4%
            })
            

class CertificationReading(models.Model):
    _name = 'certification.reading'
    _description = 'Certification Reading'

    name = fields.Char('Description', compute='_compute_name', store=True, readonly=True)
    sequence = fields.Integer('Sequence')
    reading = fields.Float('Reading', digits=dp.get_precision('Certification Service'), required=True)
    element_id = fields.Many2one('certification.element', ondelete='restrict', string='Element')
    service_id = fields.Many2one('certification.service', ondelete='restrict', string='Certification Service', readonly=True)
    # density = fields.Float(digits=dp.get_precision('Certification Service'), related='element_id.density', readonly=True)  ## what is this?
    density = fields.Char(related='element_id.density', readonly=True)  ## what is this?

    @api.multi
    @api.depends('reading', 'element_id', 'element_id.name')
    def _compute_name(self):
        for reading in self:
            if reading.element_id:
                reading.name = '[{}] {}'.format(reading.element_id.name, str(reading.reading))
            else:
                reading.name = ''

    
class CertificationResult(models.Model):
    _name = 'certification.result'
    _description = 'Certification Result'

    name = fields.Char('Name', related='element_id.name', readonly=True)

    element_id = fields.Many2one('certification.element', ondelete='restrict', string='Element', readonly=True)
    service_id = fields.Many2one('certification.service', ondelete='restrict', string='Certification Service', readonly=True)

    average = fields.Float('Average', digits=dp.get_precision('Certification Service'), readonly=True)

    diff_from_label = fields.Float('Diff. from Label', digits=dp.get_precision('Certification Service'), readonly=True)
    percent_diff_from_label = fields.Float('% Diff. from Labeled', digits=dp.get_precision('Certification Service'), readonly=True)
    state = fields.Selection([('pass', 'Pass'), ('fail', 'Fail')], string='Pass/Fail', readonly=True)
    
    
class InHouseStandard(models.Model):
    _name = 'in.house.standard'
    _description = 'In House Standard'

    element_id = fields.Many2one('certification.element', ondelete='set null', string='Element', required=True,)
    name = fields.Char(related='element_id.name')
    
    # service_ids = fields.Many2Many('certification.service', ondelete='restrict', string='Certification Service', required=True,)
    lot_id = fields.Many2one('stock.production.lot', ondelete='restrict', string='Ref No.', required=True,)

    initial_reading = fields.Char('Ref Initial Reading', required=True,)
    subsequent = fields.Char('Ref Subsequent', required=True,)

    
class CertificationLabeledValue(models.Model):
    _name = 'certification.labeled.value'
    _description ='Certification Labeled Value'

    name = fields.Char('Name')
    value = fields.Float('Value', digits=dp.get_precision('Certification Service'), required=True)
    lot_id = fields.Many2one('stock.production.lot', ondelete='restrict', string='Lot/Serial', required=True)
    element_id = fields.Many2one('certification.element', ondelete='restrict', string='Element', required=True)
    uom_id = fields.Many2one('uom.uom', ondelete='restrict', string='Unit of Measure', required=True)
