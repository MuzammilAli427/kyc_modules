from odoo import http
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)

class SmartLoanDashboard(http.Controller):
    def _get_loan_totals(self, domain):
        """Helper method to get loan totals based on domain"""
        loans = request.env['account.loan'].sudo().search(domain)
        return sum(loans.mapped('loan_amount')) or 0

    def _get_unpaid_totals(self, field_name):
        """Helper method to get unpaid totals for a specific field"""
        domain = [
            ('state', '=', 'posted'),
            (field_name, '>', 0)
        ]
        loans = request.env['account.loan'].sudo().search(domain)
        return sum(loans.mapped(field_name)) or 0

    @http.route('/smart_loan_dashboard', auth='public', type='json', methods=['GET'])
    def smart_loan_dashboard(self, **kwargs):
        """Returns the aggregated loan dashboard data"""
        dashboard_data = {
            # Basic loan totals
            'total_loans': self._get_loan_totals([('state', '=', 'posted')]),
            'total_bon': self._get_loan_totals([
                ('state', '=', 'posted'),
                ('country_id', '=', request.env.ref('base.bq').id)
            ]),
            'total_cw': self._get_loan_totals([
                ('state', '=', 'posted'),
                ('country_id', '=', request.env.ref('base.cw').id)
            ]),

            # Loan classification totals
            'total_retail': self._get_loan_totals([
                ('state', '=', 'posted'),
                ('kyc_type', '=', 'retail')
            ]),
            'total_corporate': self._get_loan_totals([
                ('state', '=', 'posted'),
                ('kyc_type', '=', 'corporate')
            ]),

            # Days past due classification
            'total_satisfactory': self._get_loan_totals([
                ('state', '=', 'posted'),
                ('days_past_due', '>=', 0),
                ('days_past_due', '<=', 29)
            ]),
            'total_substandard': self._get_loan_totals([
                ('state', '=', 'posted'),
                ('days_past_due', '>=', 90),
                ('days_past_due', '<=', 119)
            ]),
            'total_special': self._get_loan_totals([
                ('state', '=', 'posted'),
                ('days_past_due', '>=', 30),
                ('days_past_due', '<=', 89)
            ]),
            'total_doubtful': self._get_loan_totals([
                ('state', '=', 'posted'),
                ('days_past_due', '>=', 120),
                ('days_past_due', '<=', 179)
            ]),
            'total_loss': self._get_loan_totals([
                ('state', '=', 'posted'),
                ('days_past_due', '>', 180)
            ]),

            # Product code based classifications
            'total_collateral': self._get_loan_totals([
                ('state', '=', 'posted'),
                ('product_code', 'in', ['CLWC002', 'CRLWC002', 'RLWC002', 'RRLWC002', 'BRLWC002', 'BRRLWC002', 'BCLWC002'])
            ]),
            'total_restructured': self._get_loan_totals([
                ('state', '=', 'posted'),
                ('product_code', 'in', ['CRLWC002', 'RRLWC002', 'BRRLWC002', 'BCLWC002'])
            ]),
            'total_non_collateral': self._get_loan_totals([
                ('state', '=', 'posted'),
                ('product_code', 'in', ['CLWC001', 'RLWC001', 'BRLWC001', 'BCLWC001'])
            ]),
            'total_restructured_non_collateral': self._get_loan_totals([
                ('state', '=', 'posted'),
                ('product_code', 'in', ['CRLWC001', 'RRLWC001', 'BRRLWC001', 'BCLWC001'])
            ]),
            'total_zero_interest': self._get_loan_totals([
                ('state', '=', 'posted'),
                ('product_code', 'in', ['CZIL001', 'RZIL001', 'BRZIL001', 'BCZIL001'])
            ]),

            # Unpaid amounts
            'total_principal_due': self._get_unpaid_totals('unpaid_amount'),
            'total_interest_due': self._get_unpaid_totals('unpaid_interest'),
            'total_late_charges': self._get_unpaid_totals('unpaid_penalty'),
            'total_fire_insurance': self._get_unpaid_totals('unpaid_fire_insurance'),
            'total_life_insurance': self._get_unpaid_totals('unpaid_life_insurance'),
            'total_lease': self._get_unpaid_totals('unpaid_long_lease'),

            # Write-offs
            'total_writeoff': self._get_loan_totals([('state', '=', 'write_off')])
        }

        return dashboard_data
