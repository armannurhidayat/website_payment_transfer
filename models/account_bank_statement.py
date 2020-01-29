# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import models, api
from odoo.tools.float_utils import float_compare

class AccountBankStatement(models.Model):
    _inherit = 'account.bank.statement'
    
    def reconcile_auto(self):
        self.line_ids.try_reconcilliation()
    
class AccountBankStatementLine(models.Model):
    _inherit = 'account.bank.statement.line'
    
    @api.model
    def _try_reconciliation(self):
        self.search([('journal_entry_ids', '=', False), ('account_id', '=', False)]).try_reconcilliation()
        
    def try_reconcilliation(self):
        for line in self:
            if line.amount < 0 or line.journal_entry_ids or line.account_id:
                continue
            statement_currency = line.statement_id.currency_id
            company_currency = line.statement_id.journal_id.company_id.currency_id
            amount = line.amount
            if statement_currency != company_currency:
                amount = statement_currency.with_context({'date': line.date}).compute(amount, company_currency, round=False)
            domain = [
                ('account_id.internal_type', '=', 'receivable'),
                ('full_reconcile_id', '=', False),
                ('balance', '!=', 0),
                ('debit', '>', amount - company_currency.rounding),
                ('debit', '<', amount + company_currency.rounding),
            ]
            if line.partner_id:
                domain += [('partner_id', '=', line.partner_id.id)]
            for found_ml in self.env['account.move.line'].search(domain, order='date_maturity asc, date asc'):
                if not float_compare(found_ml.debit, amount, precision_rounding=company_currency.rounding):
                    if not line.partner_id:
                        line.partner_id = found_ml.partner_id.id
                    counterpart_aml_dicts = [{
                        'name' : line.name,
                        'debit' : 0,
                        'credit' : amount,
                        'move_line' : found_ml
                    }]
                    line.process_reconciliation(counterpart_aml_dicts)
                    break
                
            if line.journal_entry_ids:
                continue
            
            domain = [
                ('currency_id', '=', statement_currency.id),
                ('team_id.website_ids', '!=', False),
                ('state', '=', 'sent'),
                ('amount_total', '>', amount - statement_currency.rounding),
                ('amount_total', '<', amount + statement_currency.rounding),
            ]
            if line.partner_id:
                domain += [('partner_id', '=', line.partner_id.id)]
            for found_quot in self.env['sale.order'].search(domain, order='date_order asc'):
                if not float_compare(found_quot.amount_total, amount, precision_rounding=statement_currency.rounding):
                    if any(x.product_id.invoice_policy != 'order' for x in found_quot.order_line):
                        continue
                    if not line.partner_id:
                        line.partner_id = found_quot.partner_id.id
                    found_quot.action_confirm()
                    found_quot.action_invoice_create(final=True)
                    found_quot.invoice_ids.action_invoice_open()
                    ml = found_quot.invoice_ids.mapped('move_id.line_ids').filtered(lambda l:l.account_id == l.invoice_id.account_id and not l.full_reconcile_id)
                    cumulative = amount
                    counterpart_aml_dicts = []
                    for found_ml in ml:
                        if cumulative < 0:
                            continue
                        amount_to_rec = ml.debit if ml.debit < cumulative else cumulative
                        counterpart_aml_dicts.append({
                            'name' : line.name,
                            'debit' : 0,
                            'credit' : amount_to_rec,
                            'move_line' : found_ml
                        })
                        cumulative -= amount_to_rec
                    line.process_reconciliation(counterpart_aml_dicts)
                    break
            
        
                
            
        
