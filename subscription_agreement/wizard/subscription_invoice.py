# © 2022 (Jamie Escalante <jescalante@blueminds.cl>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models, tools, fields, _
import base64
import logging
from io import BytesIO
from xlwt import Workbook, easyxf
from datetime import date
from dateutil.relativedelta import relativedelta
import calendar
import time
from datetime import timedelta, datetime
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class SaleSubscriptionInvoice(models.TransientModel):
    _name = 'sale.subscription.invoice'

    def create_invoices_lines(self,invoice, subscriptions):
        
        list_invoice = []
        for record in subscriptions:
            for line in record.recurring_invoice_line_ids:
                invoice_line_vals = {
                'move_id': invoice.id,
                'subscription_id': record.id,
                'product_id': line.product_id.id,
                'name': line.name,
                'quantity': line.quantity,
                'price_unit': line.price_subtotal,
                'account_id': line.product_id.categ_id.property_account_income_categ_id.id,
                'tax_ids': line.product_id.taxes_id.ids,
            }
                list_invoice.append(invoice_line_vals)
        invoice.write(
                {'invoice_line_ids': [(0, 0, invoice_line_vals) for invoice_line_vals in list_invoice]})
        invoice._onchange_partner_id()
        invoice._onchange_invoice_line_ids()
        invoice._context.get('check_move_validity', False)
        invoice._move_autocomplete_invoice_lines_values()
        invoice._move_autocomplete_invoice_lines_write(vals)
        #invoice._move_autocomplete_invoice_lines_create()

    def create_invoices(self):
        subscriptions = self.env['sale.subscription'].browse(self._context.get('active_ids', []))
        order_dict = {}
        values = {}
        # list_invoice = []
        company = self.env.company or self.company_id


        for record in subscriptions:
            journal = self.env['account.journal'].search([('type', '=', 'sale'), ('company_id', '=', company.id)], limit=1)
            
            invoice_vals = {
            'move_type': 'out_invoice',
            'invoice_date': record.recurring_next_date,
            'partner_id': record.partner_id.id,
            'currency_id': record.pricelist_id.currency_id.id,
            'journal_id': journal.id}
            
            
            
                
        
        
               
        
        invoice = self.env['account.move'].create(invoice_vals)
        self.create_invoices_lines(invoice,subscriptions)
        
        
        
        
            
            
            
            
            
            
              
            # for line in record.recurring_invoice_line_ids:
            #     invoice_line_vals = {
            #         'move_id': invoice.id,
            #         'subscription_id': record.id,
            #         'product_id': line.product_id.id,
            #         'name': line.name,
            #         'quantity': line.quantity,
            #         'price_unit': line.price_subtotal,
            #         'account_id': line.product_id.categ_id.property_account_income_categ_id.id,
            #         'tax_ids': line.product_id.taxes_id.ids,
            #     }
            #     list_invoice.append(invoice_line_vals)
                
            
            
            

            
            # invoice.write(
            #     {'invoice_line_ids': [(0, 0, invoice_line_vals) for invoice_line_vals in list_invoice]})
            # invoice._onchange_partner_id()
            # invoice._onchange_invoice_line_ids()
            # invoice._move_autocomplete_invoice_lines_values()
