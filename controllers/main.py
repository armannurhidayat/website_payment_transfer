# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import http
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale
import json
import base64
from odoo import http, modules, tools

class WebsiteSalePayment(WebsiteSale):

	@http.route(['/shop/payment'], type='http', auth="public", website=True)
	def payment(self, **post):
		order = request.website.sale_get_order()
		if order:
			order._unique_set()
		return super(WebsiteSalePayment, self).payment(**post)

	def order_lines_2_google_api(self, order_lines):
		""" Transforms a list of order lines into a dict for google analytics """
		order_lines_not_unique = order_lines.filtered(lambda line: not line.is_unique)
		return super(WebsiteSalePayment, self).order_lines_2_google_api(order_lines_not_unique)

	def order_2_return_dict(self, order):
		""" Returns the tracking_cart dict of the order for Google analytics """
		ret = super(WebsiteSalePayment, self).order_2_return_dict(order)
		for line in order.order_line:
			if line.is_unique:
				ret['transaction']['unique'] = line.price_subtotal
		return ret


	@http.route(['/shop/confirmation'], type='http', auth="user", website=True)
	def shop_confirmation(self):
		return request.redirect('/shop')


	@http.route(['/payment/confirmation/<int:so_id>'], type='http', auth="user", website=True)
	def payment_confirmation(self, so_id, **post):
		account_journal = request.env['account.journal'].sudo().search([('type', 'in', ('bank',))])
		sale_order = request.env['sale.order'].sudo().search([('id', '=', so_id)])

		return request.render("website_payment_transfer.payment_confirmation", {
			'account_journal' : account_journal,
			'sale_order'      : sale_order,
		})


	@http.route(['/payment/confirmation/submit'], type='http', auth="user", methods=['POST'], website=True, csrf=False)
	def payment_confirmation_submit(self, **post):

		# process encode base64
		if post.get('bukti_transfer', False):
			name = post.get('bukti_transfer').filename
			file = post.get('bukti_transfer')
			attachment = file.read()
			encoded = base64.b64encode(attachment)

		data = {
			'partner_id'        : int(post.get('partner_id')),
			'amount'            : post.get('nominal_transfer'),
			'payment_date'      : post.get('tgl_transfer'),
			'journal_id'        : int(post.get('bank')),
			'communication'     : post.get('so_name') + ' | ' + post.get('memo'),
			'payment_type'      : 'inbound',
			'partner_type'      : 'customer',
			'payment_method_id' : 2,
			'bukti_transfer'    : encoded,
		}

		request.env['account.payment'].sudo().create(data)
		return request.redirect('/shop')