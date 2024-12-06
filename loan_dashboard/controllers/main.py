from odoo import http
from odoo.http import request
import json, datetime

class loanDashboardController(http.Controller):

    @http.route('/loandashboard', auth='public', type='http', methods=['POST'], csrf=False)
    def loan_dasboard_start(self,**kwargs):
        """ Returns the starting data for loan dashboard.
            Calculate all values and return
        """
        dashboard_data = {}

        account_loan = request.env['account.loan'].sudo().search([('state','=','posted')])

        current_currency_rate = request.env.company.currency_id.rate
        current_currency_symbol = request.env.company.currency_id.symbol
        current_rate = {'current_currency_rate':current_currency_rate}

        classified_data = self.get_classified_data(account_loan=account_loan)


        dashboard_data['tile'] = self.get_tile_data_json(account_loan=account_loan,classified_data_parent=classified_data,**current_rate)
        dashboard_data['pie'] = dashboard_data['tile']
        dashboard_data['line'] = self.get_line_data_json(account_loan=account_loan,classified_data=classified_data,**current_rate)

        meta_info = {
            "current_currency_rate": current_currency_rate,
            "current_currency_symbol": current_currency_symbol
        }
        dashboard_data['metadata'] = meta_info

        return json.dumps(dashboard_data)

    def get_tile_data_json(self, account_loan, classified_data_parent,**kwargs):

        # field_for_total_loan_amount = 'total_principal_balance'

        """
        Total Portfolio Amount and Total Portfolio Number of Loans'
        """

        total_portfolio_amount = self.calculated_amount(account_loan=account_loan,currency_rate=kwargs.get('current_currency_rate'))
        total_portfolio_number_of_loans = len(account_loan)

        """
        '"Bonaire, Sint Eustatius and Saba" Portfolio Amount / Bon Portfolio Number of Loans | Curaçao Portfolio Amount / cur Portfolio Number of Loans'
        """
        bon_portfolio_object = account_loan.filtered(lambda l: l.country_name == 'Bonaire, Sint Eustatius and Saba')
        bon_portfolio_amount = self.calculated_amount(account_loan=bon_portfolio_object,currency_rate=kwargs.get('current_currency_rate'))
        bon_portfolio_number_of_loans = len(bon_portfolio_object)

        cur_portfolio_object = account_loan.filtered(lambda l: l.country_name == 'Curaçao')
        cur_portfolio_amount = self.calculated_amount(account_loan=cur_portfolio_object,currency_rate=kwargs.get('current_currency_rate'))
        cur_portfolio_number_of_loans = len(cur_portfolio_object)

        """
            Retail Portfolio Amount
            Retail Portfolio Number of Loans
            Corporate Portfolio Amount
            Corporate Portfolio Number of Loans
        """

        retail_object = account_loan.filtered(lambda l: l.kyc_type == 'retail')
        retail_portfolio_amount = self.calculated_amount(account_loan=retail_object,currency_rate=kwargs.get('current_currency_rate'))
        retail_number_of_loans = len(retail_object)

        corporate_portfolio_object = account_loan.filtered(lambda l: l.kyc_type == 'corporate')
        corporate_portfolio_amount = self.calculated_amount(account_loan=corporate_portfolio_object,currency_rate=kwargs.get('current_currency_rate'))
        corporate_portfolio_number_of_loans = len(corporate_portfolio_object)


        first_three_tiles = {
            'total_portfolio_amount': total_portfolio_amount,
            'total_portfolio_number_of_loans': total_portfolio_number_of_loans,

            'bon_portfolio_amount': bon_portfolio_amount,
            'cur_portfolio_amount': cur_portfolio_amount,

            'bon_portfolio_number_of_loans': bon_portfolio_number_of_loans,
            'cur_portfolio_number_of_loans': cur_portfolio_number_of_loans,

            'retail_portfolio_amount': retail_portfolio_amount,
            'retail_number_of_loans': retail_number_of_loans,

            'corporate_portfolio_amount': corporate_portfolio_amount,
            'corporate_portfolio_number_of_loans': corporate_portfolio_number_of_loans,
        }

        """
            Satisfactory
            Substandard
            Special Mention
            Doubtful
            Loss
        """
        classified_data = classified_data_parent
        tile_classified_data = self.get_tile_data_as_per_classification(classified_data=classified_data, currency_rate=kwargs.get('current_currency_rate'))
        tile_data_by_product = self.get_tile_data_by_product(account_loan=account_loan,currency_rate=kwargs.get('current_currency_rate'))
        ### need to put type in loan products first
        return {
            **first_three_tiles ,
            **tile_classified_data,
            **tile_data_by_product
        }

    def get_tile_data_as_per_classification(self, classified_data,  currency_rate):
        data_tile = {}
        for key, data in classified_data.items():
            data_tile_object = self.calculated_amount(account_loan=data,currency_rate=currency_rate)
            data_tile[f'{key}_amount'] = data_tile_object
            data_tile[f'{key}_number_of_loans'] = len(data)
        return data_tile

    def get_tile_data_by_product(self, account_loan, currency_rate):
        data_by_product = {}
        criteria = {
            # 'restructured_loan': 'restructured_loan',
            'write_off': 'cancelled',
        }

        write_off_filtered_object = account_loan.filtered(lambda l: l.state == 'cancelled')
        data_by_product[f'write_off_amount'] =  self.calculated_amount(account_loan=write_off_filtered_object,currency_rate=currency_rate)
        data_by_product[f'write_off_number_of_loans'] = len(write_off_filtered_object)

        restructured_loan_filtered_object = account_loan.filtered(lambda l: l.is_restructure_loan )
        data_by_product[f'restructured_loan_amount'] = self.calculated_amount(account_loan=restructured_loan_filtered_object,currency_rate=currency_rate)
        data_by_product[f'restructured_loan_number_of_loans'] = len(restructured_loan_filtered_object)

        return data_by_product

    def get_classified_data(self, account_loan):
        classification_data = {}
        criteria = {
            'satisfactory': (0.0, 29.0),
            'substandard': (30.0, 89.0),
            'special_mention': (90.0, 119.0),
            'doubtful': (120.0, 179.0),
        }
        for key, days_range in criteria.items():
            account_filtered_objects = account_loan.filtered(
                lambda l: l.days_past_due >= days_range[0] and l.days_past_due <= days_range[1])
            classification_data[f'{key}'] = account_filtered_objects
        # 'loss': (180, MAX_NUMBER)
        loss_180_days = account_loan.filtered(lambda l: l.days_past_due >= 180)
        classification_data['loss'] = loss_180_days

        return classification_data


    def calculated_amount(self, account_loan, currency_rate):
        all_field_amounts = [
            # sum(account_loan.mapped('outstanding_bal_stored')),
            # sum(account_loan.mapped('total_insurance_interest_penalties')),
        ]
        return round(sum(all_field_amounts), 2)

    # functions having big complexity and high computing time
    # def cal_total_unpaid_intereet(self, account_loan):
    #     config_obj = request.env['ir.config_parameter']
    #     interest_prod_id = config_obj.sudo().get_param('ae_loan_manag.principal_prod_id')
    #     total_unpaid_interest = []
    #     for loan in account_loan:
    #         total_unpaid_interest.append(sum(request.env['account.move.line'].search(
    #             [('move_id.loan_id', '=', loan.id), ('product_id', '=', int(interest_prod_id)),
    #              ('fully_paid', '=', False)]).mapped('unpaid_amount')))
    #     return sum(total_unpaid_interest)
    #
    # def cal_total_penalties(self, account_loan):
    #     total_penalties = []
    #     for loan in account_loan:
    #         total_penalties.append(sum(request.env['account.move.line'].search(
    #             [('move_id.loan_id', '=', loan.id), ('product_id', '=', loan.penalty_product_id.id),
    #              ('fully_paid', '=', False)]).mapped('unpaid_amount')))
    #     return sum(total_penalties)
    #
    # def cal_total_unpaid_life_insurance(self, account_loan):
    #     total_unpaid_life_insurance = []
    #     for loan in account_loan:
    #         total_unpaid_life_insurance.append(sum(request.env['account.move.line'].search(
    #             [('move_id.loan_id', '=', loan.id), ('product_id', '=', loan.bonaire_principal_prod_id.id),
    #              ('fully_paid', '=', False)]).mapped('unpaid_amount')))
    #     return sum(total_unpaid_life_insurance)


    def get_line_data_json(self, account_loan, classified_data, **kwargs):

        """
            Amounts Per Loan Classification Per AO
        """
        currency_rate = kwargs.get('current_currency_rate')
        officers = account_loan.mapped('user_id')
        data_amounts_per_loan_classification_per_ao = {}
        for officer in officers:
            officer_key = f'{officer.name}'
            data_amounts_per_loan_classification_per_ao[officer_key] = {}
            for key, data in classified_data.items():
                filtered_object = data.filtered(lambda l: l.user_id.id == officer.id)
                data_amounts_per_loan_classification_per_ao[officer_key][f'{key}_amount'] = self.calculated_amount(account_loan=filtered_object,currency_rate=currency_rate)
                data_amounts_per_loan_classification_per_ao[officer_key][f'{key}_quantity'] = len(filtered_object)


        """
            Amounts Per Jurisdiction Per Loan Classification
        """
        amounts_per_jurisdiction_per_loan_classification = {}
        jurisdiction_criteria = [
            'Curaçao', 'Bonaire, Sint Eustatius and Saba'
        ]
        for jury in jurisdiction_criteria:
            amounts_per_jurisdiction_per_loan_classification[f'{jury}'] = {}
            for key, data in classified_data.items():
                filtered_object = data.filtered(lambda l: l.country_name == jury)
                amounts_per_jurisdiction_per_loan_classification[f'{jury}'][f'{key}_amount'] = self.calculated_amount(account_loan=filtered_object,currency_rate=currency_rate)
                amounts_per_jurisdiction_per_loan_classification[f'{jury}'][f'{key}_quantity'] = len(filtered_object)


        """
            Amounts per division per loan classification
        """
        amounts_per_division_per_loan_classification = {}
        division_criteria = [
            'retail', 'corporate'
        ]
        for division in division_criteria:
            amounts_per_division_per_loan_classification[f'{division}'] = {}
            for key, data in classified_data.items():
                filtered_object = data.filtered(lambda l: l.kyc_type == division)
                amounts_per_division_per_loan_classification[f'{division}'][f'{key}_amount'] = self.calculated_amount(account_loan=filtered_object,currency_rate=currency_rate)
                amounts_per_division_per_loan_classification[f'{division}'][f'{key}_quantity'] = len(filtered_object)


        """
            Restructured Loans Amounts Per Loan Classification
        """
        restructured_loan_amounts_per_loan_classification = {}
        year_and_month_filter = datetime.date(2021,5,1)
        date_criteria = range(datetime.datetime(2021, 5, 1).year, datetime.datetime.now().year + 1)
        for year in date_criteria:
            restructured_loan_amounts_per_loan_classification[f'{year}'] = {}
            for key, data in classified_data.items():
                data = data.filtered(lambda l: l.create_date.date() >= year_and_month_filter)
                filtered_object = data.filtered(lambda l: l.create_date.year == year and l.is_restructure_loan and len(l.old_loan_name.split(',')) == 1)
                restructured_loan_amounts_per_loan_classification[f'{year}'][f'{key}_amount'] = self.calculated_amount(account_loan=filtered_object,currency_rate=currency_rate)

        """
            Cumulative Restructured Loans Per Loan Classification Per AO Since May 1, 2021
        """
        officers = account_loan.mapped('user_id')
        date_criteria = datetime.date(2021,5,1)
        cumulative_restructured_loans_per_loan_classification = {}
        for officer in officers:
            officer_key = f'{officer.name}'
            cumulative_restructured_loans_per_loan_classification[officer_key] = {}
            for key, data in classified_data.items():
                data = data.filtered(lambda l: l.create_date.date() >= date_criteria)
                filtered_object = data.filtered(lambda l: l.user_id.id == officer.id and l.is_restructure_loan and len(l.old_loan_name.split(',')) > 1)
                cumulative_restructured_loans_per_loan_classification[officer_key][f'{key}_amount'] = self.calculated_amount(account_loan=filtered_object,currency_rate=currency_rate)


        return {
            'data_amounts_per_loan_classification_per_ao': {**data_amounts_per_loan_classification_per_ao},
            'amounts_per_jurisdiction_per_loan_classification': {**amounts_per_jurisdiction_per_loan_classification},
            'amounts_per_division_per_loan_classification': {**amounts_per_division_per_loan_classification},
            'restructured_loan_amounts_per_loan_classification': {**restructured_loan_amounts_per_loan_classification},
            'cumulative_restructured_loans_per_loan_classification': {**cumulative_restructured_loans_per_loan_classification}
        }
