from odoo import _, models, api, fields

class L10nClEdiUtilMixin(models.AbstractModel):
    _inherit = 'l10n_cl.edi.util'

    def _send_sii_claim_response(self, mode, company_vat, digital_signature, document_type_code, document_number, claim_type):
        digital_signature.last_token = False
        return super(L10nClEdiUtilMixin, self)._send_sii_claim_response(mode, company_vat, digital_signature, document_type_code, document_number, claim_type)