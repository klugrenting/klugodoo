# © 2022 (Jamie Escalante <jescalante@blueminds.cl>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models

class Means(models.Model):
	_name = 'means'
	_description = 'Recursos'

	name = fields.Char(string="Nombre del recurso")
