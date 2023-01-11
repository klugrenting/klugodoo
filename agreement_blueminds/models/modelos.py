# © 2022 (Jamie Escalante <jescalante@blueminds.cl>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, models, fields
from datetime import timedelta
from datetime import date
from dateutil.relativedelta import relativedelta
import calendar
import time
from datetime import timedelta, datetime
from dateutil.relativedelta import relativedelta
import calendar
from odoo.exceptions import UserError, ValidationError


class AgreementModelos(models.Model):
    _name = "agreement.modelos"
    _description = "Agreement Modelos"

    def _get_default_parties(self):
        deftext = """
        <h3>Company Information</h3>
        <p>
        ${object.company_id.partner_id.name or ''}.<br>
        ${object.company_id.partner_id.street or ''} <br>
        ${object.company_id.partner_id.state_id.code or ''}
        ${object.company_id.partner_id.zip or ''}
        ${object.company_id.partner_id.city or ''}<br>
        ${object.company_id.partner_id.country_id.name or ''}.<br><br>
        Represented by <b>${object.company_contact_id.name or ''}.</b>
        </p>
        <p></p>
        <h3>Partner Information</h3>
        <p>
        ${object.partner_id.name or ''}.<br>
        ${object.partner_id.street or ''} <br>
        ${object.partner_id.state_id.code or ''}
        ${object.partner_id.zip or ''} ${object.partner_id.city or ''}<br>
        ${object.partner_id.country_id.name or ''}.<br><br>
        Represented by <b>${object.partner_contact_id.name or ''}.</b>
        </p>
        """
        return deftext

    @api.model
    def _compute_dynamic_content(self):
        MailTemplates = self.env["mail.template"]
        for agreement in self:
            lang = (
                    agreement.id
                    and agreement.partner_id.lang
                    or "en_US")
            content = MailTemplates.with_context(lang=lang)._render_template(
                agreement.content, "agreement", agreement.id)
            agreement.dynamic_content = content

    # General
    name = fields.Char(
        string="Nombre",
        required=True)
    content = fields.Html(string="Content")
    dynamic_content = fields.Html(
        compute="_compute_dynamic_content",
        string="Dynamic Content",
        help="compute dynamic Content")
    field_domain = fields.Char(string='Field Expression',
                               default='[["active", "=", True]]')
    default_value = fields.Char(
        string="Default Value",
        help="Optional value to use if the target field is empty.")
    copyvalue = fields.Char(
        string="Placeholder Expression",
        help="""Final placeholder expression, to be copy-pasted in the desired
                 template field.""")

    @api.onchange("field_domain", "default_value")
    def onchange_copyvalue(self):
        self.copyvalue = False
        if self.field_domain:
            string_list = self.field_domain.split(",")
            if string_list:
                field_domain = string_list[0][3:-1]
                self.copyvalue = "${{object.{} or {}}}".format(
                    field_domain,
                    self.default_value or "''")