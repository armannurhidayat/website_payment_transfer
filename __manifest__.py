# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': "Wire Transfer E-Commerce",
    'description': "Pembayaran transfer pada e-commerce otomatis rekonsiliasi",
    'category': 'account',
    'version': '1.0',
    'depends': ['website_sale', 'delivery'],
    'data': [
        'data/ir_cron_data.xml',
        'views/account_bank_statement_view.xml',
        'views/sale_view.xml',
        'views/company_view.xml',
        'views/website_payment_transfer_templates.xml',
        'views/account_payment_view.xml',
        'views/stock_picking_view.xml',
    ],
}