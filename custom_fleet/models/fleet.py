# © 2022 (Jamie Escalante <jescalante@blueminds.cl>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models, tools, fields, _


class InheritFleet(models.Model):
    _inherit = 'fleet.vehicle'

    date_delivery = fields.Date(
        string="Fecha entrega de Vehiculo", related='subscription.date_start')
    date_return = fields.Date(
        string="Fecha devolucion de Vehiculo", related='subscription.date')
    date_expect_refund_subs = fields.Date(strin="Fecha esperada")
    subscription = fields.Many2one(
        'sale.subscription', string='subscripcion activa', compute='_compute_subscription')
    traccion_vehicle = fields.Selection(
        [('4x4', '4x4'), ('4x2', '4x2'), ('AWD', 'AWD')])
    accesories_vehicle = fields.Many2many(
        'accesories.tags', string='Accesorios de Vehiculo', store=True)
    purchase = fields.Many2one('purchase.order', string="Orden de compra")
    date_purchase = fields.Datetime(string="Fecha de Compra")
    account_move = fields.Many2one(
        'account.move', string="Factura OC",compute='_compute_account')
    date_account = fields.Datetime(string="Fecha de Factura")
    account_price_total = fields.Monetary(string="Total Factura")
    purchase_price_total = fields.Monetary(string="Total compra")
    margin_total = fields.Monetary(string="Margen")
    purchase_price_total = fields.Monetary(string="Precio de compra")
    fleet_counter = fields.Integer(compute='_compute_fleet_count')
    
    attach_1 = fields.Binary()
    attach_1_fname = fields.Char()
    attach_2 = fields.Binary()
    attach_2_fname = fields.Char()
    attach_3 = fields.Binary()
    attach_3_fname = fields.Char()  

    def _compute_fleet_count(self):
        fleet_data = self.env['fleet.vehicle'].read_group(domain=[('drive_id', 'in', self.ids), ('state_id', '!=', False)],
                                                                     fields=['drive_id'],
                                                                     groupby=['drive_id'])
        mapped_data = dict([(m['driver_id]'][0], m['partner_id_count']) for m in fleet_data])
        for fleets in self:
            fleets.fleet_counter = mapped_data.get(fleets.id, 0)

    

         

    
   # Funcion que permite buscar la factura de venta asociada al vehiculo y extraer informacion
    @api.depends()
    def _compute_account(self):
        self.account_move = False
        self.date_account = False
        self.account_price_total = False
        self.purchase = False
        self.date_purchase = False
        
        for record in self:
            if record.state_id.name == 'Vendido':
                account_move_id = self.env['account.move'].search([('partner_id', '=', record.driver_id.id),('state', '=', 'posted'),('move_type', '=', 'out_invoice')]) 
                purchase_partner_id = self.env['purchase.order.line'].search([('product_id', '=', self.product_id.id)])
                for line in account_move_id.invoice_line_ids.filtered(lambda w: w.product_id.id == record.product_id.id):
                    
                        record.account_move = line.move_id.id
                        record.date_account = line.move_id.invoice_date
                        record.account_price_total = line.move_id.amount_total
                if purchase_partner_id:
                    record.purchase = purchase_partner_id.order_id.id
                    if record.purchase:
                        record.date_purchase = purchase_partner_id.order_id.date_approve
                        record.purchase_price_total = purchase_partner_id.order_id.amount_total
                        
            if record.purchase_price_total and record.account_price_total:
                record.margin_total = record.account_price_total - record.purchase_price_total
                
            

   

    # Funcion que coloca el ultimo odometro consultado en la vista formulario, solo valida etiqueta GPS

    def _get_odometer(self):
        FleetVehicalOdometer = self.env['fleet.vehicle.odometer']
        for record in self:
            vehicle_odometer = FleetVehicalOdometer.search(
                [('vehicle_id', '=', record.id), ('tag_ids', 'in', [2])], order='id desc', limit=1)
            if vehicle_odometer:
                record.odometer = vehicle_odometer.value
            else:
                record.odometer = 0


    @api.depends()
    def _compute_subscription(self):
        for record in self:
            subscription_ids = self.env['sale.subscription'].search(
                [('vehicle_id', '=', record.id)])
            if subscription_ids:
                record.subscription = subscription_ids.id
                record.date_expect_refund_subs = subscription_ids.date_expect_refund
            else:
                record.subscription = False
                record.date_expect_refund_subs = False


class InheritFleetAssignation(models.Model):
    _inherit = 'fleet.vehicle.assignation.log'

    date_delivery = fields.Date(
        string="Fecha entrega de Vehiculo", related='vehicle_id.date_delivery')
    date_return = fields.Date(
        string="Fecha devolucion de Vehiculo", related='vehicle_id.date_return')


class AccesoriesTags(models.Model):

    _name = 'accesories.tags'

    name = fields.Char(string="Nombre")
    color = fields.Integer(string="Color")
