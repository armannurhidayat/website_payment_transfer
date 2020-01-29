# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import fields, models, api, tools, modules
from odoo.tools.float_utils import float_compare
from random import randint
import base64
import logging

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
	_inherit = 'sale.order'
	
	@api.depends('order_line.price_unit', 'order_line.tax_id', 'order_line.discount', 'order_line.product_uom_qty')
	def _compute_amount_unique(self):
		for order in self:
			order.amount_unique = sum(order.order_line.filtered('is_unique').mapped('price_subtotal'))

	@api.depends('order_line.is_unique')
	def _compute_has_unique(self):
		for order in self:
			order.has_unique = any(order.order_line.filtered('is_unique'))
			
	def _website_order_line(self):
		for order in self:
			order.website_order_line = order.order_line.filtered(lambda l: not l.is_delivery and not l.is_unique)
		
	amount_unique = fields.Monetary(
		compute='_compute_amount_unique', digits=0,
		string='Unique Amount',
		help="Unique Amount to pay", store=True)
	has_unique = fields.Boolean(
		compute='_compute_has_unique', string='Has Unique Amount',
		help="Has an order line set for unique amount", store=True)
	website_order_line = fields.One2many(
		'sale.order.line', compute=_website_order_line,
		string='Order Lines displayed on Website', readonly=True,
		domain=[('is_delivery', '=', False), ('is_unique', '=', False)],
		help='Order Lines to be displayed on the website. They should not be used for computation purpose.')

	def _unique_set(self):
		self.unique_set()

	def _unique_unset(self):
		self.env['sale.order.line'].search([('order_id', 'in', self.ids), ('is_unique', '=', True)]).unlink()

	def unique_set(self):
		self._unique_unset()
		for order in self:
			vals = {
				'order_id': order.id,
				'display_type':'line_section',
				'name': 'Unique Amount',
				'product_uom_qty': 1,
				'product_uom': order.company_id.unique_product_id.uom_id.id,
				'product_id': order.company_id.unique_product_id.id,
				'price_unit': order._get_unique_amount(),
				'is_unique': True,
			}
			if self.order_line:
				vals['sequence'] = order.order_line[-1].sequence + 1
			self.env['sale.order.line'].create(vals)
			
	def _get_unique_amount(self):
		return randint(self.company_id.unique_min_amount, self.company_id.unique_max_amount)
	
	def _cart_update(self, product_id=None, line_id=None, add_qty=0, set_qty=0, **kwargs):
		""" Override to update carrier quotation if quantity changed """
		values = super(SaleOrder, self)._cart_update(product_id, line_id, add_qty, set_qty, **kwargs)
		if add_qty or set_qty is not None:
			self.unique_set()
		return values


class SaleOrderLine(models.Model):
	_inherit = 'sale.order.line'
	
	is_unique = fields.Boolean(string="Is a Unique Amount", default=False)


class AccountPayment(models.Model):
	_inherit = 'account.payment'

	bukti_transfer = fields.Binary(
		string='Bukti Transfer',
		attachment=True,
	)