# -*- coding: utf-8 -*-
from odoo import models, fields, api, _, osv

class DashboardAccountReport(models.Model):
	_inherit = 'account.report'


	def dashboard_get_report_informations(self,previous_options):
		report_id = self.env.ref(previous_options.get("report_id"))
		if previous_options.get('date_filter') == 'custom':
			if previous_options['start_date'] != '' and previous_options['end_date'] != '':
				previous_options['date'] = {
					'string': '', 
					'period_type': 'custom', 
					'mode': 'range', 
					'date_from': previous_options['start_date'], 
					'date_to': previous_options['end_date'], 
					'filter': 'custom'
					}
			else:
				report_id.default_opening_date_filter = 'this_year'
			previous_options.pop('date_filter')
		elif previous_options.get('date_filter'):
			report_id.default_opening_date_filter = previous_options.get('date_filter')
			previous_options.pop('date_filter')

		if previous_options.get("report_id") == "account_reports.partner_ledger_report":
			# selected account optin selected is True
			if previous_options.get('account_filter'):
				account_filter = previous_options.get('account_filter')
				previous_options['account_type'] = [
					{'id': 'trade_receivable', 'name': 'Receivable', 'selected': True if 'trade_receivable' in account_filter else False}, 
					{'id': 'non_trade_receivable', 'name': 'Non Trade Receivable', 'selected': True if 'non_trade_receivable' in account_filter else False}, 
					{'id': 'trade_payable', 'name': 'Payable', 'selected': True if 'trade_payable' in account_filter else False}, 
					{'id': 'non_trade_payable', 'name': 'Non Trade Payable', 'selected': True if 'non_trade_payable' in account_filter else False}
					]
				previous_options.pop('account_filter')


		if report_id.filter_partner:
			previous_options['partner_ids'] = [eval(p) for p in previous_options.get('partner_filter')]
			previous_options.pop('partner_filter')
			previous_options['partner_categories'] = [eval(pt) for pt in previous_options.get('partner_tag_filter')]
			previous_options.pop('partner_tag_filter')

		if report_id.filter_period_comparison:
			
			previous_options['comparison'] = {
				'filter': previous_options.get('filter'), 
				'number_period':int(previous_options.get('period'))  if int(previous_options.get('period'))   else 1  , 
				'date_from':  previous_options.get('comp_date_from'), 
				'date_to': previous_options.get('comp_date_end'), 
				'periods': []
				}

		if report_id.filter_journals:
			list_of_journal_ids = previous_options.get('journal_ids') or []
			Journals_ids = self.env['account.journal'].sudo().search([])
			previous_options['journals'] = []
			for jurnal_id in Journals_ids:
				previous_options['journals'].append({
					'id': jurnal_id.id,
					'model': 'account.journal',
					'name': jurnal_id.name,
					'title': jurnal_id.name+' - '+jurnal_id.code,
					'selected': True if jurnal_id.id in list_of_journal_ids else False,
					'type': jurnal_id.type
					})

			if previous_options.get('journal_group_id'):
				Journals_group_id = self.env['account.journal.group'].sudo().browse(int(previous_options.get('journal_group_id')))
				previous_options['__journal_group_action'] = {'action': 'add', 'id': Journals_group_id.id}
			else:
				previous_options['__journal_group_action'] = None

		res = report_id.get_report_informations(previous_options)
		options = report_id._get_options(previous_options)
		all_column_groups_expression_totals = report_id._compute_expression_totals_for_each_column_group(report_id.line_ids.expression_ids, options)
		lines = report_id._get_lines(options, all_column_groups_expression_totals)
		res.update({'lines': lines})
		return res