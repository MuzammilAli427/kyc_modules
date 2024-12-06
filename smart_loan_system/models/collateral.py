from odoo import models, fields, api, _
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class LoanCollateral(models.Model):
    _name = 'loan.collateral'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'This model contains the loan collateral'
    _rec_name = 'collateral_type'

    collateral_type = fields.Selection([('mortgage', 'Mortgage'),
                                        ('vehicle', 'Vehicle'),
                                        ('insurance', 'Insurance'),
                                        ('guarantee', 'Guarantee'),
                                        ('cash', 'Cash'),
                                        ('receivables', 'Receivables'),
                                        ('inventory', 'Inventory'),
                                        ('loans_subordination', 'Loans subordination'),
                                        ('general_assignment_of_income', 'General Assignment of income'),
                                        ('pledge_on_shares', 'Pledge on shares'),
                                        ('salary_assignment', 'Salary Assignment'),
                                        ],
                                       'Collateral Type', tracking=True)
    amount = fields.Float('Amount', compute='compute_amount')
    loan_id = fields.Many2one('account.loan')
    """1:For Mortgage"""
    deed_amt = fields.Float('Deed Amount', tracking=True)
    type_deed = fields.Selection([('ownership', 'Ownership'),
                                  ('land', 'Land'), ('leasehold_property', ' Leasehold property')], 'Type of deed',
                                 tracking=True)
    long_lease_expiration_date = fields.Date('Long Lease Expiration Date', tracking=True)
    appraisal_report_date = fields.Date('Appraisal Report Date', tracking=True)
    appraised_by = fields.Char('Company or person that provided the Appraised', tracking=True)
    property_address = fields.Char('Property Address', tracking=True)
    mortgage_ranking_level = fields.Selection([('1st', '1st'),
                                               ('2nd', '2nd'), ('3rd', ' 3rd'), ('4th', ' 4th')], 'Ranking',
                                              tracking=True)
    any_info = fields.Char('Description', tracking=True)
    market_value = fields.Float(string="Market Value", tracking=True)
    force_sale_Value = fields.Float(string="Forced Sale Value", tracking=True)
    mortgage_owner = fields.Text(string="Owner", tracking=True)

    """2:For Vehicle"""
    vehicle_brand = fields.Text(string="Brand", tracking=True)
    vehicle_model = fields.Text(string="Model", tracking=True)
    vehicle_year = fields.Char(string="Year", tracking=True)
    vehicle_licence_plt_no = fields.Text(string="License Plate Number", tracking=True)
    vehicle_owner = fields.Text(string="Owner", tracking=True)
    vehicle_chassisnumer = fields.Text(string="Chassisnumer", tracking=True)
    vehicle_description = fields.Text(string="Description", tracking=True)

    """3:For Insurance"""
    insurance_type = fields.Selection(
        [('fire', 'Fire'), ('life', 'Life'), ('inventory', 'Inventory'), ('personal_accident', 'Personal Accident')],
        string="Insurance Type", tracking=True)
    ins_res1_id = fields.Many2one('res.partner', 'Name', tracking=True)
    ins_res2_id = fields.Many2one('res.partner', 'Name', tracking=True)
    ins_res3_id = fields.Many2one('res.partner', 'Name', tracking=True)
    insurance_address_fire = fields.Text(string="Address", tracking=True)
    insurance_amount = fields.Float(string="Insured Amount", tracking=True)
    insurance_policy_number = fields.Text(string="Policy number", tracking=True)
    insurance_date = fields.Date('Expiration date', tracking=True)
    insurance_broker = fields.Selection(
        [
            ('guillen_insurance_consultants', 'Guillen Insurance Consultants NV'),
            ('aon_antillen', 'AON Antillen NV'),
            ('atlas_insurance', 'Atlas Insurance NV'),
            ('avidi_nsurance_Consultancy', 'Avidi BV Insurances & Consultancy'),
            ('ce_insurance_brokers', 'C&E Insurance Brokers NV'),
            ('centraleh_hypotheekbank', 'Centrale Hypotheekbank NV'),
            ('certus_insurance_brokers', 'Certus Insurance Brokers BV'),
            ('concilium_international', 'Concilium International BV'),
            ('ds_insurance_brokers', 'D’s Insurance Brokers NV'),
            ('gabian_insurance', 'Gabian Insurance'),
            ('exprinter_International_bank', 'Exprinter International Bank NV'),
            ('firstcaribbean_International_bank', 'FirstCaribbean International Bank'),
            ('gomez_agency', 'Gomez Agency'),
            ('henriquez_vornis_insurance_consultancy', 'Henriquez & Vornis Insurance Consultancy BV'),
            ('ines_management', 'Ines Management BV'),
            ('insurance_risk_management', 'Insurance Risk Management'),
            ('isenia_branch', 'Isenia Branch'),
            ('inter_assure_curacao', 'Inter-Assure Curacao NV'),
            ('kort_assurantie_adviesbureau', 'Kort Assurantie & Adviesbureau'),
            ('kos_ta_bon_pensioenen_hypotheken', 'Kos ta bon! Pensioenen & Hypotheken BV, KTB'),
            ('maduro_curiels_insurance_services', 'Maduro & Curiel s Insurance Services NV'),
            ('bsure', 'BSURE'),
            ('optimum_actuary_pension_consultancy', 'Optimum Actuary & Pension Consultancy'),
            ('optimum_pension_management_ep', 'Optimum Pension Management & Estate Planning'),
            ('orco_bank', 'Orco Bank NV'),
            ('pensioen_visie_caribe', 'Pensioen Visie Caribe NV'),
            ('pieterz_agency', 'Pieterz agency'),
            ('progressive_auto_insurance_services', 'Progressive Auto Insurance Services NV'),
            ('psb_bank', 'PSB Bank NV'),
            ('rbc_royal_bank', 'RBC Royal Bank NV'),
            ('leeward_insurance_consultants', 'Leeward Insurance Consultants NV'),
            ('navigator_insurance_consultants', 'Navigator Insurance Consultants NV'),
            ('seguros_anta', 'Seguros Anta NV'),
            ('seguros_brouwer', 'Seguros Brouwer NV'),
            ('seguros_diwan', 'Seguros Diwan'),
            ('sigura', 'Sigura BV'),
            ('sint_hill_branch', 'Sint Hill Branch'),
            ('sinot_winkel_management_group', 'Sinot-Winkel Management Group BV'),
            ('top_assurantie_en_schadebemiddelaar', 'Top Assurantie en Schadebemiddelaar'),
            ('vgks', 'VGKS'),
            ('n/a', 'N/A'),
            ('others', 'Others'),
        ], 'Broker', tracking=True)
    insurance_company = fields.Selection(
        [('ennia', 'Ennia'),
         ('aska_insurances', 'ASKA Insurances'),
         ('guardian_group_fatum', 'Guardian Group Fatum'),
         ('inter_assure', 'Inter Assure'),
         ('nagico_insurance', 'Nagico Insurance'),
         ('sagicor', 'Sagicor'),
         ('citizens_insurance', 'Citizens Insurance'),
         ('cg_united', 'CG United'),
         ('new_india_assurance', 'New India Assurance'),
         ('seguros_brouwer', 'Seguros Brouwer'),
         ('pan_american_life_insurance', 'Pan American Life Insurance'),
         ('other', 'Other'),
         ],
        'Insurance company', tracking=True)
    insurance_description = fields.Text(string="Description", tracking=True)

    """4:For Guarantee"""
    guarantee_type = fields.Selection(
        [('personal', 'Personal'), ('corporate', 'Corporate'), ('cross', 'Cross')],
        string="Guarantee Type", tracking=True)
    guarantee_name = fields.Text(string="Name", tracking=True)
    id_no = fields.Char('ID Number#', tracking=True)
    guarantee_amount = fields.Float(string="Guarantee Amount", tracking=True)
    guarantee_date = fields.Date('Signing Date', tracking=True)
    guarantee_description = fields.Text(string="Description", tracking=True)
    guarantee_name2 = fields.Text(string="Name", tracking=True)
    id_no2 = fields.Char('ID', tracking=True)

    """5:For Cash"""
    cash_amount = fields.Float(string="Cash Amount", tracking=True)
    cash_owner = fields.Text(string="Owner", tracking=True)
    cash_bank = fields.Selection(
        [('mcb', 'MCB'), ('bdc', 'BDC'), ('rbc', 'RBC'), ('vidan_nova', 'VidaNova'), ('cibc_fcib', 'CIBC FCIB'),
         ('psb', 'PSB'), ('acu', 'ACU'), ('orco', 'ORCO')],
        string="Bank", tracking=True)
    interest_rate = fields.Char('Interest Rate', tracking=True)
    cash_date = fields.Date('Expiration date', tracking=True)
    cash_description = fields.Text(string="Description", tracking=True)

    """6:For Receivables"""
    receivable_type = fields.Selection(
        [('retail_sales', 'Retail Sales'), ('project', 'Project'),
         ('rent_income_properties', ' Rent Income Properties')],
        string="Type", tracking=True)
    receivable_description = fields.Text(string="Description", tracking=True)
    # Retail Sales
    receivable_date = fields.Date('Date', tracking=True)
    receivable_for_year = fields.Float(string="For the year end (FYE)", tracking=True)
    # Project
    receivable_borrower1 = fields.Many2one('res.partner', string="For the Borrower", tracking=True)
    receivable_borrower2 = fields.Many2one('res.partner', string="For the Borrower", tracking=True)
    receivable_borrower3 = fields.Many2one('res.partner', string="For the Borrower", tracking=True)
    receivable_borrower4 = fields.Many2one('res.partner', string="For the Borrower", tracking=True)
    # Rent Income Properties
    receivable_located_at = fields.Text(string="Located at", tracking=True)
    receivable_date_rip = fields.Date('Date', tracking=True)
    receivable_mri = fields.Float(string="Monthly Rental Income", tracking=True)

    """7:For Inventory"""
    inventory_by = fields.Many2one('res.partner', 'By', tracking=True)
    inventory_date = fields.Date('Date', tracking=True)
    inventory_for_year = fields.Char(string="For the year end (FYE)", tracking=True)
    inventory_market_value = fields.Float(string="Market Value", tracking=True)
    inventory_description = fields.Text(string="Description", tracking=True)

    """8:For Loans subordination"""
    loan_by = fields.Many2one('res.partner', string="By", tracking=True)
    loan_payable_to = fields.Text(string="Payable to", tracking=True)
    loan_date = fields.Date('Date', tracking=True)
    loan_for_year = fields.Char(string="Outstanding for the year end (FYE)", tracking=True)
    loan_description = fields.Text(string="Description", tracking=True)

    """9:For General Assignment of income"""
    general_by = fields.Many2one('res.partner', 'By', tracking=True)
    general_employee = fields.Many2one('res.partner', tracking=True)
    general_employer = fields.Char('Employer', tracking=True)
    general_date = fields.Date('Date', tracking=True)
    general_description = fields.Text(string="Description", tracking=True)

    """10:For Pledge on shares"""
    pledge_by = fields.Many2one('res.partner', 'By', tracking=True)
    pledge_date = fields.Date('Date', tracking=True)
    pledge_description = fields.Text(string="Description", tracking=True)

    """11:For Salary Assignment"""
    salary_asg_by = fields.Many2one('res.partner', 'By', tracking=True)
    salary_asg_emp = fields.Many2one('res.partner', 'Employer', tracking=True)
    salary_asg_employer = fields.Char('Employer', tracking=True)
    salary_asg_date = fields.Date('Date', tracking=True)
    salary_gross = fields.Float(string="Gross Salary", tracking=True)
    salary_description = fields.Text(string="Description", tracking=True)

    """
    **================================================================**
    """
    doc_count = fields.Integer(compute='_compute_attached_docs_count', string="Number of documents attached",
                               tracking=True)
    customer_id = fields.Many2one('res.partner', 'Customer', tracking=True, required=True)
    compute_partners = fields.Many2many('res.partner', compute='_compute_kyc_partners', tracking=True)

    @api.model
    def create(self, vals_list):
        if isinstance(vals_list, dict):
            vals_list = [vals_list]

        res = super(LoanCollateral, self).create(vals_list)

        for res_record in res:
            if self._context.get('params') and self._context.get('params').get('model') == 'account.loan':
                loan = self.env['account.loan'].browse(self._context.get('active_id'))
                if loan:
                    loan.write({'loan_collateral_ids': [(4, res_record.id)]})

        return res

    def unlink(self):
        if not self.env.user.has_group('smart_loan_system.group_loan_cao') or  self.env.user.has_group('smart_loan_system.group_loan_cam'):
            raise ValidationError("Only CAO and CAM are allowed to unlink the records.")
        return super(LoanCollateral, self).unlink()



    @api.depends('collateral_type')
    def compute_amount(self):
        for rec in self:
            if rec.collateral_type == 'mortgage':
                rec.amount = rec.deed_amt
            elif rec.collateral_type == 'insurance':
                rec.amount = rec.insurance_amount
            elif rec.collateral_type == 'guarantee':
                rec.amount = rec.guarantee_amount
            elif rec.collateral_type == 'cash':
                rec.amount = rec.cash_amount
            elif rec.collateral_type == 'receivables':
                rec.amount = rec.receivable_mri
            elif rec.collateral_type == 'inventory':
                rec.amount = rec.inventory_market_value
            elif rec.collateral_type == 'salary_assignment':
                rec.amount = rec.salary_gross
            else:
                rec.amount = 0.0

    @api.onchange('vehicle_year')
    def _check_numbers_vehicle_year(self):
        for record in self:
            if record.vehicle_year and not record.vehicle_year.isdigit():
                raise ValidationError("Only numbers are allowed in Vehicle Year.")

    @api.onchange('receivable_for_year')
    def _check_numbers_receivable_for_year(self):
        for record in self:
            if record.receivable_for_year is not None and not str(record.receivable_for_year).replace('.', '',
                                                                                                      1).isdigit():
                raise ValidationError("Only numbers are allowed in 'For the year end (FYE)'.")

    @api.onchange('general_by')
    def _onchange_general_by(self):
        for rec in self:
            if rec.general_by:
                kyc_retail = self.env['kyc.retail'].search([('partner_id', '=', rec.general_by.id)], limit=1)
                if kyc_retail:
                    rec.general_employer = kyc_retail.employer
                else:
                    rec.general_employer = False
            else:
                rec.general_employer = False

    @api.onchange('salary_asg_by')
    def _onchange_salary_asg_by(self):
        for rec in self:
            if rec.salary_asg_by:
                kyc_retail = self.env['kyc.retail'].search([('partner_id', '=', rec.salary_asg_by.id)], limit=1)
                if kyc_retail:
                    rec.salary_asg_employer = kyc_retail.employer
                else:
                    rec.salary_asg_employer = False
            else:
                rec.salary_asg_employer = False

    """
        **========================================================================**
        ** Smart button will display Attachments list view of the current partner **
        **========================================================================**
        """

    def attachment_tree_view_collateral(self):
        return {
            'name': _('Attachments'),
            'domain': [('res_model', '=', 'loan.collateral'), ('res_id', '=', self.id)],
            'res_model': 'documents.document',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,kanban',
            'context': {
                'default_res_model': 'loan.collateral', 'default_res_id': self.id
            },
        }

    """
        **=============================================================================================**
        ** Count a documents according to Loan Collateral model and res_id and assign in computed field**
        **=============================================================================================**
        """

    def _compute_attached_docs_count(self):
        for record in self:
            read_group_var = self.env['documents.document'].search_count(
                [('res_model', '=', 'loan.collateral'), ('res_id', '=', record.id)])
            record.doc_count = read_group_var

    @api.onchange('customer_id')
    def kyc_partners(self):
        for rec in self:
            kyc_retail_partner = rec.env['kyc.retail'].search([]).mapped('partner_id')
            kyc_corp_partner = rec.env['kyc.corporate'].search([]).mapped('partner_id')
            partners = kyc_retail_partner + kyc_corp_partner
            domain = [('id', 'in', partners.mapped('id'))]
            return {'domain': {'customer_id': domain,
                               'ins_res1_id': domain,
                               'ins_res2_id': domain,
                               'ins_res3_id': domain,
                               'general_by': domain,
                               'pledge_by': domain,
                               'salary_asg_by': domain,
                               'salary_asg_emp': domain,
                               'inventory_by': domain,
                               'receivable_borrower1': domain,
                               'receivable_borrower2': domain,
                               'receivable_borrower3': domain,
                               'receivable_borrower4': domain,
                               'loan_by': domain
                               }}

    def _compute_kyc_partners(self):
        for rec in self:
            kyc_retail_partner = rec.env['kyc.retail'].search([]).mapped('partner_id')
            kyc_corp_partner = rec.env['kyc.corporate'].search([]).mapped('partner_id')
            rec.compute_partners = kyc_retail_partner.ids + kyc_corp_partner.ids

    """
        **=========================================**
        ** These three function for id_no field only **
        **=========================================**
    """

    @api.onchange('id_no', 'id_no2')
    def add_format(self):
        if self.id_no:
            if len(self.id_no) <= 13 and '.' not in self.id_no:
                formatting = self.id_no[:4] + '.' + self.id_no[4:6] + '.' + self.id_no[6:8] + '.' + self.id_no[8:]
                self.id_no = formatting
        elif self.id_no2:
            if len(self.id_no2) <= 13 and '.' not in self.id_no2:
                formatting = self.id_no2[:4] + '.' + self.id_no2[4:6] + '.' + self.id_no2[6:8] + '.' + self.id_no2[8:]
                self.id_no2 = formatting

    @api.onchange('id_no')
    def _check_numbers_id_no(self):
        for record in self:
            if record.id_no:
                numbers = record.id_no.replace('.', '')
                if numbers and not numbers.isdigit():
                    raise ValidationError("Only numbers are allowed in ID Number.")
            elif self.id_no2:
                if record.id_no2:
                    numbers = record.id_no2.replace('.', '')
                    if numbers and not numbers.isdigit():
                        raise ValidationError("Only numbers are allowed in ID.")

    @api.onchange('id_no')
    def check_length(self):
        if self.id_no:
            length = len(self.id_no.replace('.', ''))
            if not length == 10:
                raise ValidationError("The ID number must be 10 digits.")
        elif self.id_no2:
            if self.id_no2:
                length = len(self.id_no2.replace('.', ''))
                if not length == 10:
                    raise ValidationError("The ID number must be 10 digits.")

    """
        **============================================================================================================**
    """

    @api.onchange('interest_rate')
    def check_digit(self):
        for record in self:
            if record.interest_rate:
                if '%' in record.interest_rate:
                    rate = record.interest_rate.replace('%', '').replace('.', '')
                    if rate and not rate.isdigit():
                        raise ValidationError("Only numbers are allowed in Current Rate.")
                    number = int(rate)
                    if number > 100:
                        raise ValidationError("You cannot exceed the limit number.")
                else:
                    for rec in self:
                        if rec.interest_rate and not rec.interest_rate.replace('.', '').isdigit():
                            raise ValidationError("Only numbers are allowed in Current Rate.")
                if '%' not in record.interest_rate:
                    record.interest_rate = record.interest_rate + '%'

    """
        **=========================================**
        ** This model contains the loan collateral **
        **=========================================**
    """
