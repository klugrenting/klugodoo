# © 2022 (Jamie Escalante <jescalante@blueminds.cl>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models

class Capabilities(models.Model):
	_name = 'capabilities'
	_description = 'Capacidades'

	name = fields.Char(string="Capacidades")
