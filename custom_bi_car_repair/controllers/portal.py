# -*- coding: utf-8 -*-
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




class MaintenancePortal(portal.CustomerPortal):
    
    
    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        model = 'maintenance.request'
        
        if 'maintenance_count' in counters:
            if request.env[model].check_access_rights('read', raise_exception=False):
                partner = request.env.user.partner_id
                values['maintenance_count'] = request.env[model].sudo().search_count(self._get_maintenance_domain(partner))
            
            else:
                values['maintenance_count'] = 0
        
        return values
    
    

    def _get_maintenance_domain(self, partner):
        return [
            ('partner_id.id', 'in', [partner.id, partner.commercial_partner_id.id]),
        ]
        
        
    def _maintenance_get_page_view_values(self, maintenance, access_token, **kwargs):
        values = {
            "page_name": "Maintenance",
            "maintenance": maintenance,
        }
        return self._get_page_view_values(
            maintenance, access_token, values, False, False,**kwargs)
        
    
    def _get_filter_domain(self, kw):
        return []

    @http.route(['/my/maintenance', '/my/maintenance/page/<int:page>'],
                type='http', auth="user", website=True)
    def portal_my_maintenance(self, page=1, date_begin=None, date_end=None,
                            sortby=None, **kw):
        values = self._prepare_portal_layout_values()
        maintenance_obj = request.env['maintenance.request']
        partner = request.env.user.partner_id
        domain = self._get_maintenance_domain(partner)
        searchbar_sortings = {
            "date": {"label": _("Fecha prevista"), "order": "schedule_date desc"},
            "name": {"label": _("OT"), "order": "name desc"},
            "code": {"label": _("Patente"), "order": "license_plate desc"},
        }
        # default sort by order
        if not sortby:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']
        # count for pager
        maintenance_count = maintenance_obj.search_count(domain)
        # pager
        pager = portal_pager(
            url="/my/maintenance",
            url_args={
                "date_begin": date_begin,
                "date_end": date_end,
                "sortby": sortby,
            },
            total=maintenance_count,
            page=page,
            step=self._items_per_page
        )
        # content according to pager and archive selected
        maintenances = maintenance_obj.search(
            domain,
            order=order,
            limit=self._items_per_page,
            offset=pager['offset']
        )
        
        values.update({
            "date": date_begin,
            "maintenances": maintenances,
            "page_name": "Maintenances",
            "pager": pager,
            "default_url": "/my/maintenance",
            "searchbar_sortings": searchbar_sortings,
            "sortby": sortby
        })
        return request.render("custom_bi_car_repair.portal_my_maintenance", values)
    
    


    @http.route(['/my/maintenance/<int:maintenance_id>'],
                type='http', auth="public", website=True)
    def portal_my_maintenance_detail(self, maintenance_id, access_token=None, **kw):
        try:
            maintenance_sudo = self._document_check_access(
                'maintenance.request', maintenance_id, access_token
            )
        except (AccessError, MissingError):
            return request.redirect('/my')
        values = self._maintenance_get_page_view_values(maintenance_sudo, access_token, **kw)
        return request.render("custom_bi_car_repair.maintenance", values)
