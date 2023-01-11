# Copyright (C) 2022 - TODAY, Jescalante@blueminds.cl
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, SUPERUSER_ID, _
from logging import getLogger


class ZonaComercial(models.Model):
    _name = "zona.comercial"
    _description = "Zonas Comerciales"

    name = fields.Char('Nombre', size=30)
    code = fields.Char('Código', size=30)

class ComunaComercial(models.Model):
    _name = "comuna.comercial"
    _description = "Comunas comerciales"
    _rec_name = 'commune'

    commune = fields.Many2one('res.country.commune', 'Comuna')
    code = fields.Char('Código', size=30)
    zona_id = fields.Many2one('zona.comercial', string='Zona Comercial', required=True)

class SectorComercial(models.Model):
    _name = "sector.comercial"
    _description = "Sectores Comercial"

    name = fields.Char('Nombre', size=30)
    code = fields.Char('Código', size=30)
    comuna_id = fields.Many2one('comuna.comercial', string='Comuna Comercial', required=True, ondelete='cascade', index=True,
                               copy=False)

class ZonaMantencion(models.Model):
    _name = "zona.mantencion"
    _description = "Zonas Mantencion"

    name = fields.Char('Nombre', size=30)
    code = fields.Char('Código', size=30)

class ComunaMantencion(models.Model):
    _name = "comuna.mantencion"
    _description = "Comunas mentenciones"
    _rec_name = 'commune'

    commune = fields.Many2one('res.country.commune', 'Comuna')
    code = fields.Char('Código', size=30)
    zona_id = fields.Many2one('zona.mantencion', string='Zona Mantencion', required=True, ondelete='cascade', index=True,
                               copy=False)

class SectorMantencion(models.Model):
    _name = "sector.mantencion"
    _description = "Sectores mentenciones"

    name = fields.Char('Nombre', size=30)
    code = fields.Char('Código', size=30)
    comuna_id = fields.Many2one('comuna.mantencion', string='Comuna Mantencion', required=True, ondelete='cascade', index=True,
                               copy=False)

