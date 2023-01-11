# -*- coding: utf-8 -*-
import base64
import io
import datetime
import werkzeug
from collections import OrderedDict
from dateutil.relativedelta import relativedelta
from odoo.exceptions import AccessError, MissingError
from odoo import http
from odoo.exceptions import ValidationError
from odoo.http import request
from odoo.tools.translate import _
from collections import Counter
from odoo.addons.payment.controllers import portal as payment_portal
from odoo.addons.payment import utils as payment_utils
from odoo.addons.portal.controllers import portal
from odoo.addons.portal.controllers.portal import get_records_pager, pager as portal_pager


class FleetPortal(portal.CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        model = 'fleet.vehicle'

        if 'fleet_count' in counters:
            if request.env[model].check_access_rights('read', raise_exception=False):
                partner = request.env.user.partner_id
                values['fleet_count'] = request.env[model].sudo(
                ).search_count(self._get_fleet_domain(partner))

            else:
                values['fleet_count'] = 0

        return values

    def _get_fleet_domain(self, partner):
        return [
            ('driver_id.id', 'in', [partner.id,
             partner.commercial_partner_id.id]),
        ]

    def _fleet_get_page_view_values(self, fleet, access_token, **kwargs):
        values = {
            "page_name": "Fleet",
            "fleet": fleet,
        }
        return self._get_page_view_values(
            fleet, access_token, values, False, False, **kwargs)

    @http.route(['/my/fleet', '/my/fleet/page/<int:page>'],
                type='http', auth="user", website=True)
    def portal_my_fleet(self, page=1, date_begin=None, date_end=None,
                        sortby=None, **kw):
        values = self._prepare_portal_layout_values()
        fleet_obj = request.env['fleet.vehicle']
        partner = request.env.user.partner_id
        domain = self._get_fleet_domain(partner)
        searchbar_sortings = {
            "name": {"label": _("OT"), "order": "name desc"},
            "code": {"label": _("Patente"), "order": "license_plate desc"},
        }
        # default sort by order
        if not sortby:
            sortby = 'name'
        order = searchbar_sortings[sortby]['order']
        # count for pager
        fleet_count = fleet_obj.search_count(domain)
        # pager
        pager = portal_pager(
            url="/my/fleet",
            url_args={
                "date_begin": date_begin,
                "date_end": date_end,
                "sortby": sortby,
            },
            total=fleet_count,
            page=page,
            step=self._items_per_page
        )
        # content according to pager and archive selected
        fleets = fleet_obj.search(
            domain,
            order=order,
            limit=self._items_per_page,
            offset=pager['offset']
        )

        values.update({
            "date": date_begin,
            "fleets": fleets,
            "page_name": "Fleets",
            "pager": pager,
            "default_url": "/my/fleet",
            "searchbar_sortings": searchbar_sortings,
            "sortby": sortby
        })
        return request.render("custom_fleet.portal_my_fleet", values)

    @http.route(['/my/fleet/<int:fleet_id>'],
                type='http', auth="public", website=True)
    def portal_my_fleet_detail(self, fleet_id, access_token=None, **kw):
        try:
            fleet_sudo = self._document_check_access(
                'fleet.vehicle', fleet_id, access_token
            )
        except (AccessError, MissingError):
            return request.redirect('/my')
        values = self._fleet_get_page_view_values(
            fleet_sudo, access_token, **kw)
        return request.render("custom_fleet.fleet", values)

    @http.route(['/my/fleet/<int:fleet_id>/download/1', ], type='http', auth='public')
    def download_attachment(self, fleet_id,  access_token=None, **kw):
        # Check if this is a valid attachment id

        try:
            fleet_sudo = self._document_check_access(
                'fleet.vehicle', fleet_id, access_token
            )
        except (AccessError, MissingError):
            return request.redirect('/my')
        values = self._fleet_get_page_view_values(
            fleet_sudo, access_token, **kw)
        if fleet_sudo.attach_1:
            data = io.BytesIO(base64.standard_b64decode(fleet_sudo.attach_1))
            return http.send_file(data, filename='soap.pdf', as_attachment=True)
        

        else:
            return request.not_found()

    @http.route(['/my/fleet/<int:fleet_id>/download/2', ], type='http', auth='public')
    def download_attachment2(self,fleet_id,  access_token=None, **kw):
        # Check if this is a valid attachment id
        

        try:
            fleet_sudo = self._document_check_access(
                'fleet.vehicle', fleet_id, access_token
            )
        except (AccessError, MissingError):
            return request.redirect('/my')
        values = self._fleet_get_page_view_values(
            fleet_sudo, access_token, **kw)
        if fleet_sudo.attach_2:
            data2=io.BytesIO(base64.standard_b64decode(fleet_sudo.attach_2))
            return http.send_file(data2, filename = 'permiso_circulacion.pdf', as_attachment = True)
            
        else:
            return request.not_found()
        
    @http.route(['/my/fleet/<int:fleet_id>/download/3', ], type='http', auth='public')
    def download_attachment3(self,fleet_id,  access_token=None, **kw):
        # Check if this is a valid attachment id
        

        try:
            fleet_sudo = self._document_check_access(
                'fleet.vehicle', fleet_id, access_token
            )
        except (AccessError, MissingError):
            return request.redirect('/my')
        values = self._fleet_get_page_view_values(
            fleet_sudo, access_token, **kw)
        if fleet_sudo.attach_3:
            data3=io.BytesIO(base64.standard_b64decode(fleet_sudo.attach_3))
            return http.send_file(data3, filename = 'homologado.pdf', as_attachment = True)
            
        else:
            return request.not_found()