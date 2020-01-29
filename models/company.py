# -*- coding: utf-8 -*-

from odoo import fields, models, api

    
class ResCompany(models.Model):
    _inherit = 'res.company'
    
    unique_product_id = fields.Many2one('product.product', 'Unique Product')
    unique_min_amount = fields.Float('Minimum Unique Amount', help='this amount will be added in quotation')
    unique_max_amount = fields.Float('Maximum Unique Amount', help='this amount will be added in quotation')

class SaleConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    unique_product_id = fields.Many2one('product.product', 'Unique Product', config_parameter='website_payment_transfer.unique_product_id')
    unique_min_amount = fields.Float('Minimum Unique Amount', help='this amount will be added in quotation', config_parameter='website_payment_transfer.unique_min_amount')
    unique_max_amount = fields.Float('Maximum Unique Amount', help='this amount will be added in quotation', config_parameter='website_payment_transfer.unique_max_amount')

    def execute(self):
        res = super(SaleConfigSettings, self).execute()
        self.ensure_one()
        to_write = {}
        if self.unique_product_id :
            to_write['unique_product_id'] = self.unique_product_id.id
        if self.unique_min_amount :
            to_write['unique_min_amount'] = self.unique_min_amount
        if self.unique_max_amount :
            to_write['unique_max_amount'] = self.unique_max_amount
        if to_write :
            self.company_id.write(to_write)
        return res
