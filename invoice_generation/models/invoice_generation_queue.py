from odoo import api, fields, models

class InvoiceGenerationQueue(models.Model):
    _name = 'invoice.generation.queue'
    _description = 'Cola de generacion de facturas'

    name = fields.Char('Referencia')
    date = fields.Date('Fecha')
    rate = fields.Float('Tasa UF')
    state = fields.Selection([('in_process', 'En proceso'), ('finish', 'Procesado')], string='Estado', default='in_process')
    type_gen = fields.Selection(selection=[
        ('integral', 'Integral Cliente'),
        ('contrato', 'Separada por Contrato')], string='Tipo de Generación', required=False)
    rental_ids = fields.Many2many('sale.order', string='Rentals')
    move_ids = fields.Many2many('account.move', 'Facturas', compute='_get_invoiced')
    queue_rate_ids = fields.One2many('invoice.generation.queue.currency', 'queue_id')
    invoice_count = fields.Integer(string='Invoice Count', compute='_get_invoiced')

    def _get_invoiced(self):
        AccountMove = self.env['account.move']
        for queue in self:
            invoices = AccountMove.search([('queue_id', '=', queue.id),('move_type', '=', 'out_invoice')])
            queue.move_ids = invoices.ids
            queue.invoice_count = len(invoices)

    def action_view_invoices(self):
        invoices = self.mapped('move_ids')
        action = self.env["ir.actions.actions"]._for_xml_id("account.action_move_out_invoice_type")
        if len(invoices) > 1:
            action['domain'] = [('id', 'in', invoices.ids)]
        elif len(invoices) == 1:
            form_view = [(self.env.ref('account.view_move_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(state, view) for state, view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = invoices.id
        else:
            action = {'type': 'ir.actions.act_window_close'}

        context = {
            'default_move_type': 'out_invoice',
        }
        action['context'] = context
        return action

    def process_queue_manual_rentals(self):
        for record in self:
            if record.state == 'in_process':
                ctx = self._context.copy()
                ctx['type_gen'] = record.type_gen
                inv_ids = record.rental_ids.with_context(ctx)._create_invoices()
                if inv_ids:
                    for inv in inv_ids:
                        inv.queue_id = record.id
                    #record.state = 'finish'

    def process_queue_rentals(self):
        for record in self.search([('state', '=', 'in_process')]):
            if record.state == 'in_process':
                ctx = self._context.copy()
                ctx['type_gen'] = record.type_gen
                inv_ids = record.rental_ids.with_context(ctx)._create_invoices()
                if inv_ids:
                    for inv in inv_ids:
                        inv.queue_id = record.id
                    #record.state = 'finish'

class InvoiceGenQueueCurrency(models.Model):
    _name = 'invoice.generation.queue.currency'
    _description = u'Cola Generacion Facturas Tasas'

    queue_id = fields.Many2one('invoice.generation.queue')
    currency_id = fields.Many2one('res.currency', string='Moneda')
    rate = fields.Float(string='Tasa')