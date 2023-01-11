from odoo import api, fields, models
import pandas as pd

class GenerateBookMissing(models.TransientModel):
    _name = 'generate.book.missing'
    _description = 'Generate Book Missing'

    date_start = fields.Date(string='Start')
    date_end = fields.Date(string='End')

    def action_generate(self):
        dates = pd.date_range(start=str(self.date_start), end=str(self.date_end))
        date_range = [date for date in dates.array.date]
        DayliBook = self.env['l10n_cl.daily.sales.book']
        for d in date_range:
            book_id = DayliBook.create({
                'date': d,
                'send_sequence': 1,
                'company_id': self.env.user.company_id.id,
                'l10n_cl_dte_status': 'not_sent'
            })
            fact_ids = book_id._get_move_ids_without_daily_sales_book_by_date(d)
            move_ids = self.env['account.move'].search([('id', 'in', fact_ids)])
            for move in move_ids:
                move.l10n_cl_daily_sales_book_id = book_id.id
            book_id._create_dte()