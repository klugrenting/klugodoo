# -*- coding: utf-8 -*-

from odoo import api, models, fields


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    def _get_computed_name(self):
        self.ensure_one()

        if not self.product_id:
            return ''

        if self.partner_id.lang:
            product = self.product_id.with_context(lang=self.partner_id.lang)
        else:
            product = self.product_id

        values = []
        if product.partner_ref:
            values.append(product.partner_ref)
        if self.journal_id.type == 'sale':
            if product.marca:
                values.append('Marca: '+ str(product.marca))
            if product.modelo:
                values.append('Modelo: '+ str(product.modelo))
            if product.chasis:
                values.append('Chasis: '+ str(product.chasis))
            if product.motor:
                values.append('Motor: '+ str(product.motor))
            if product.cilindrada:
                values.append('Cilindrada: '+ str(product.cilindrada))
            if product.anio:
                values.append('Año: '+ str(product.anio))
            if product.transmision:
                values.append('Transmisión: '+ str(product.transmision))
            if product.color_kg:
                values.append('Color: '+ str(product.color_kg))
            if product.combustible:
                values.append('Combustible: '+ str(product.combustible))
            if product.tipo_vehiculo:
                values.append('Tipo Vehículo: '+ str(product.tipo_vehiculo))
            if product.patente:
                values.append('Patente: '+ str(product.patente))
            if product.description_sale:
                values.append(product.description_sale)
        elif self.journal_id.type == 'purchase':
            if product.description_purchase:
                values.append(product.description_purchase)
        return '\n'.join(values)