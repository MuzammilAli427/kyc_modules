from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import re
import datetime


class KycRetail(models.Model):
    _name = 'kyc.retail'
    _description = 'This model contains all the members of KYC Retail'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name asc'
    # _rec_name = 'customer_no'

    # Fields for personal information section
    customer_name = fields.Char(string='Customer Name', compute='_compute_customer_name', readonly=True, tracking=True)
    partner_id = fields.Many2one('res.partner', tracking=True)
    currency_id = fields.Many2one('res.currency', related='partner_id.currency_id')
    state = fields.Selection(
        [('draft', 'Draft'),
         ('waiting_approval', 'Waiting On Approval'),
         ('approved', 'Approved')
         ],
        'Approval State', tracking=True)
    status = fields.Selection(
        [('active', 'Active'),
         ('unactive', 'None Active')],
        'Status', tracking=True)
    pep = fields.Selection(
        [('yes', 'Yes'),
         ('no', 'No')],
        'PEP', tracking=True)
    customer_no = fields.Char('Customer Number', tracking=True, store=True, default='New')
    group_ids = fields.Many2many('kyc.groups', string='Group Number', tracking=True)
    group_role_ids = fields.Many2many('kyc.group.roles', string='Group Roles', tracking=True)
    dob = fields.Date('Date of Birth', tracking=True)
    birth_place = fields.Char('Place of Birth', tracking=True)
    name = fields.Char('Name', tracking=True)
    middle_name = fields.Char('Middle Name', tracking=True)
    last_name = fields.Char('Last Name', tracking=True)
    gender = fields.Selection(
        [('male', 'Male'),
         ('female', 'Female'), ('x_gender', 'X')],
        'Gender', tracking=True)
    marital_status = fields.Selection(
        [('married', 'Married'),
         ('single', 'Single'),
         ('divorced', 'Divorced'),
         ('widowed', 'Widowed'),
         ('cohabited', 'Cohabited')],
        'Marital Status', tracking=True)
    id_no = fields.Char('ID number #', tracking=True)
    id_expiration = fields.Date('ID Exp. date', tracking=True)
    driving_licence_no = fields.Char('Driving License number #', tracking=True)
    driving_expiration = fields.Date('Driving License Exp. date', tracking=True)
    passport_no = fields.Char('Passport number #', tracking=True)
    issued_by = fields.Char('Issued by', tracking=True)
    pass_expiration = fields.Date('Exp. Date Passport', tracking=True)
    tel_home = fields.Char('Telephone Home', required=True, tracking=True)
    home_code = fields.Selection(selection=lambda self: self._get_phone_code(), default='599 CW', tracking=True)
    cellular_code = fields.Selection(selection=lambda self: self._get_phone_code(), default='599 CW', tracking=True)
    tel_cellular = fields.Char('Telephone Cellular', required=True, tracking=True)
    mail = fields.Char('Email', tracking=True)

    # home address section fields
    home_address = fields.Char('Address', tracking=True)
    home_neighborhood = fields.Char('Neighborhood', tracking=True)
    home_city = fields.Char('City', tracking=True)
    home_country_id = fields.Many2one('res.country', string='Country')

    # mailing address section fields
    mail_address = fields.Char('Address', tracking=True)
    mail_neighborhood = fields.Char('Neighborhood', tracking=True)
    mail_city = fields.Char('City', tracking=True)
    mail_country_id = fields.Many2one('res.country', string='Country')

    # employer info section fields
    employer = fields.Char('Employer', tracking=True)
    department = fields.Char('Department', tracking=True)
    employer_address = fields.Char('Address', tracking=True)
    employer_city = fields.Char('City', tracking=True)
    employer_country_id = fields.Many2one('res.country', string='Country')
    tel_employer = fields.Char('Telephone', tracking=True)
    employer_code = fields.Selection(selection=lambda self: self._get_phone_code(), default='599 CW', tracking=True)

    image = fields.Binary('Image')
    comment = fields.Html(tracking=True)

    # This field is the counter of number of documents attached to the record
    doc_count = fields.Integer(compute='_compute_attached_docs_count', string="Number of documents attached")
    doc_corp_count = fields.Integer(compute='_compute_attached_docs_corp_count')
    kyc_groups_count = fields.Integer(compute='_compute_kyc_groups_count')
    loan_collateral_count = fields.Integer(compute='_compute_loan_collateral_count')
    loan_count = fields.Integer(string='Loans', compute="get_loan_count")
    total_payment_amount = fields.Float('Total Payment Amount', compute='cal_payment_amt')
    total_invoiced = fields.Monetary(compute='_invoice_total', string="Total Invoiced")
    total_due = fields.Monetary(compute='_compute_total_due')
    is_require = fields.Boolean(compute='_compute_is_required')
    flag_state = fields.Boolean(default=False)
    is_approver = fields.Boolean(compute='_compute_is_approver')

    @api.depends('state')
    def _compute_is_approver(self):
        for rec in self:
            if rec.state == 'waiting_approval' and (self.env.user.has_group('smart_loan_system.kyc_approver_group')):
                rec.is_approver = True
            elif rec.state == 'approved' and (self.env.user.has_group('smart_loan_system.kyc_approver_group')):
                rec.is_approver = True
            elif rec.state == 'approved' and not (self.env.user.has_group('smart_loan_system.kyc_create_write_group')):
                rec.is_approver = False
            else:
                rec.is_approver = False

    # these are the constraints to get unique value
    _sql_constraints = [
        ('customer_no_uniq', 'unique (customer_no)', 'Customer number must be unique.'),
        ('id_no_uniq', 'unique (id_no)', 'ID number must be unique.'),
        ('driving_licence_no_uniq', 'unique (driving_licence_no)', 'Driving License number must be unique.'),
        ('passport_no_uniq', 'unique (passport_no)', 'Passport number must be unique.')
    ]
    def approve_retail(self):
        for rec in self:
            rec.write({'state': 'approved'})

    @api.depends('id_no', 'driving_licence_no', 'passport_no')
    def _compute_is_required(self):
        for rec in self:
            list = [rec.id_no, rec.driving_licence_no, rec.passport_no]
            if any(list):
                rec.is_require = True
            else:
                rec.is_require = False

    @api.depends('partner_id.unreconciled_aml_ids', 'partner_id.followup_next_action_date')
    @api.depends_context('partner_id.company', 'partner_id.allowed_company_ids')
    def _compute_total_due(self):
        for partner in self.partner_id:
            total_due = 0
            for aml in partner.unreconciled_aml_ids:
                if aml.company_id == self.env.company and not aml.blocked:
                    total_due += aml.amount_residual
            self.total_due = total_due

    def show_partner_due_invoices(self):
        self.ensure_one()
        return {
            'name': _("Overdue Payments for %s", self.partner_id.display_name),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'views': [[self.env.ref('account_followup.customer_statements_form_view').id, 'form']],
            'res_model': 'res.partner',
            'res_id': self.partner_id.id,
        }

    def open_partner_ledger(self):
        return {
            'type': 'ir.actions.client',
            'name': _('Partner Ledger'),
            'tag': 'account_report',
            'params': {
                'options': {'partner_ids': [self.partner_id.id]},
                'ignore_session': 'both',
            },
            'context': {
                'report_id': self.env.ref('account_reports.partner_ledger_report').id
            }
        }

    def _invoice_total(self):
        self.total_invoiced = 0
        if not self.partner_id:
            return True

        all_partners_and_children = {}
        all_partner_ids = []
        for partner in self.partner_id:
            # price_total is in the company currency
            all_partners_and_children[partner] = self.env['res.partner'].with_context(active_test=False).search(
                [('id', 'child_of', partner.id)]).ids
            all_partner_ids += all_partners_and_children[partner]

        domain = [
            ('partner_id', 'in', all_partner_ids),
            ('state', 'not in', ['draft', 'cancel']),
            ('move_type', 'in', ('out_invoice', 'out_refund')),
        ]
        price_totals = self.env['account.invoice.report'].read_group(domain, ['price_subtotal'], ['partner_id'])
        for partner, child_ids in all_partners_and_children.items():
            partner.total_invoiced = sum(
                price['price_subtotal'] for price in price_totals if price['partner_id'][0] in child_ids)

    def show_partner_invoices(self):
        pass
        all_child = self.env['res.partner'].with_context(active_test=False).search(
            [('id', 'child_of', self.partner_id.ids)])

        return {
            'name': _('Invoices'),
            'domain': [('move_type', 'in', ('out_invoice', 'out_refund')),
                       ('partner_id', 'in', all_child.ids)],
            'res_model': 'account.move',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
        }
        # action['context'] = {'default_move_type': 'out_invoice', 'move_type': 'out_invoice', 'journal_type': 'sale',
        #                     'search_default_unpaid': 1, 'active_test': False}

    def cal_payment_amt(self):
        """
        Calculate total payment amount of loan.
        :return:
        """
        pay_his_obj = self.env['account.payment.history']
        for record in self:
            histories = pay_his_obj.search([('partner_id', '=', record.partner_id.id), ('state', '=', 'running')])
            record.total_payment_amount = sum(history.amount for history in histories)

    def show_partner_loan_payments(self):
        return {
            'name': _('Loan Payments'),
            'domain': [('partner_id', '=', self.partner_id.id), ('state', '=', 'running')],
            'res_model': 'account.payment.history',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
        }

    def get_loan_count(self):
        """
        Count total loan of partner.
        :return:
        """
        loan = self.env['account.loan']
        for record in self:
            record.loan_count = len(loan.search([('partner_id', '=', record.partner_id.id)]))

    def _compute_loan_collateral_count(self):
        collateral = self.env['loan.collateral']
        for rec in self:
            rec.loan_collateral_count = len(collateral.search([('customer_id', '=', rec.partner_id.id)]))

    def open_collateral_record(self):
        return {
            'name': _('Collaterals'),
            'domain': [('customer_id', '=', self.partner_id.id)],
            'res_model': 'loan.collateral',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'context': {'default_customer_id': self.partner_id.id}
        }

    def show_partner_loan(self):
        return {
            'name': _('Loans'),
            'domain': [('partner_id', '=', self.partner_id.id)],
            'res_model': 'account.loan',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
        }

    def name_get(self):
        res = []
        for rec in self:
            # if rec.env.context.get('params') and rec.env.context.get('params').get('model') and rec.env.context.get(
            #         'params').get('model') == rec._name:
            #     res.append((rec.id, '%s' % (rec.customer_no)))
            # else:
            res.append((rec.id, '%s / %s %s' % (rec.customer_no, rec.name, rec.last_name)))
        return res

    @api.depends('name', 'middle_name', 'last_name')
    def _compute_customer_name(self):
        for rec in self:
            if rec.name and rec.middle_name and rec.last_name:
                rec.customer_name = rec.name + ' ' + rec.middle_name + ' ' + rec.last_name
            elif rec.name and rec.last_name:
                rec.customer_name = rec.name + ' ' + rec.last_name
            else:
                rec.customer_name = ' '

    # this method calculates the phone codes of each country
    def _get_phone_code(self):
        phone_codes = []
        countries = self.env['res.country'].search([])
        for country in countries:
            phone_codes.append((f'{str(country.phone_code)} {country.code}', f'({str(country.phone_code)})'))
        return phone_codes

    # This method is to validate the email pattern
    @api.onchange('mail')
    def validate_mail(self):
        if self.mail:
            match = re.match(r'^[A-Za-z0-9+/_.]+@[A-Za-z0-9-]+\.[A-Za-z0-9-.]+$', self.mail)
            if match == None:
                raise ValidationError(_('Not a valid E-mail'))

    """
    **=============================================================================**
    **These methods verify if the length of the integers fields entered by the user**
    **=============================================================================**
    """

    # This will give an error if the customer number is not between 4 and 8
    # @api.onchange('customer_no')
    # def _check_customer_no(self):
    #     length = len(str(self.customer_no))
    #     if length < 4 or length > 8:
    #         raise ValidationError(_('Customer Number digits must be between 4 and 8'))

    # This will give an error if the driving license number is not between 4 and 8
    @api.onchange('driving_licence_no')
    def _check_license_no(self):
        if self.driving_licence_no:
            length = len(str(self.driving_licence_no))
            if length < 4 or length > 8:
                raise ValidationError(_('Driving License digits must be between 4 and 8'))

    # This will give an error if the home phone number and phone code combined exceed the limit of 12
    @api.onchange('tel_home')
    def _home_telephone_combined_length(self):
        if self.home_code and self.tel_home:
            tel_home = self.tel_home.replace(' ', '').replace('-', '')
            home_code = re.findall('\d+', self.home_code)
            combined_digits = home_code[0] + tel_home
            if len(combined_digits) > 12:
                raise ValidationError("The length of phone number cannot exceed 12 digits.")

    # This will give an error if the cellular phone number and phone code combined exceed the limit of 12
    @api.onchange('tel_cellular', 'cellular_code')
    def _cellular_tel_combined_length(self):
        if self.cellular_code and self.tel_cellular:
            tel_cellular = self.tel_cellular.replace(' ', '').replace('-', '')
            cellular_code = re.findall('\d+', self.cellular_code)
            combined_digits = cellular_code[0] + tel_cellular
            if len(combined_digits) > 12:
                raise ValidationError("The length of phone number cannot exceed 12 digits.")

    # This will give an error if the home phone number and phone code combined exceed the limit of 12

    def _home_telephone_length(self):
        if self.tel_home:
            tel_home = self.tel_home.replace(' ', '').replace('-', '')
            if not len(tel_home) > 6:
                raise ValidationError("The length of phone number must be between 7 and 12 digits.")

    # This will give an error if the cellular phone number and phone code combined exceed the limit of 12
    def _cellular_tel_length(self):
        if self.tel_cellular:
            tel_cellular = self.tel_cellular.replace(' ', '').replace('-', '')
            if not len(tel_cellular) > 6:
                raise ValidationError("The length of Telephone Cellular must be between 7 and 12 digits.")
        if self.employer_code and self.tel_employer:
            tel_employer = self.tel_employer.replace(' ', '').replace('-', '')
            employer_code = re.findall('\d+', self.employer_code)
            combined_digits = employer_code[0] + tel_employer
            if not len(combined_digits) > 10:
                raise ValidationError("The length of employer phone number must be between 7 and 12 digits.")

    # This will give an error if the employer's phone number and phone code combined exceed the limit of 12
    @api.onchange('tel_employer', 'employer_code')
    def _employer_tel_combined_length(self):
        if self.employer_code and self.tel_employer:
            tel_employer = self.tel_employer.replace(' ', '').replace('-', '')
            employer_code = re.findall('\d+', self.employer_code)
            combined_digits = employer_code[0] + tel_employer
            if len(combined_digits) > 12:
                raise ValidationError("The length of employer phone number must be between 7 and 12 digits.")

    # This will give an error if the id number exceed the limit of 10
    @api.onchange('id_no')
    def check_length(self):
        if self.id_no:
            length = len(self.id_no.replace('.', ''))
            if not length == 10:
                raise ValidationError("The ID number must be 10 digits.")

    """
    **==========================================================================================**
    **The methods below are constraints to check that only integers are entered in number fields**
    **==========================================================================================**
    """

    # @api.onchange('customer_no')
    # def _check_numbers_customer_no(self):
    #     for record in self:
    #         if record.customer_no and not record.customer_no.isdigit():
    #             raise ValidationError("Only numbers are allowed in Customer Number.")

    @api.onchange('driving_licence_no')
    def _check_numbers_driving_licence_no(self):
        for record in self:
            if record.driving_licence_no and not record.driving_licence_no.isdigit():
                raise ValidationError("Only numbers are allowed in Driving License.")

    @api.onchange('id_no')
    def _check_numbers_id_no(self):
        for record in self:
            if record.id_no:
                numbers = record.id_no.replace('.', '')
                if numbers and not numbers.isdigit():
                    raise ValidationError("Only numbers are allowed in ID Number.")

    @api.onchange('tel_home')
    def _check_numbers_tel_home(self):
        for record in self:
            if record.tel_home:
                tel_home = record.tel_home.replace(' ', '').replace('-', '')
                if not tel_home.isdigit():
                    raise ValidationError("Only numbers are allowed in Home Telephone.")

    @api.onchange('tel_cellular')
    def _check_numbers_tel_cellular(self):
        for record in self:
            if record.tel_cellular:
                tel_cellular = record.tel_cellular.replace(' ', '').replace('-', '')
                if not tel_cellular.isdigit():
                    raise ValidationError("Only numbers are allowed in Cellular Telephone.")

    @api.onchange('tel_employer')
    def _check_numbers_tel_employer(self):
        for record in self:
            if record.tel_employer:
                tel_employer = record.tel_employer.replace(' ', '').replace('-', '')
                if not tel_employer.isdigit():
                    raise ValidationError("Only numbers are allowed in Employer Telephone.")

    """
                                             END
    ##########################################################################################

    """

    # This method adds '.' to the id number entered by the user
    @api.onchange('id_no')
    def add_format(self):
        if self.id_no:
            if len(self.id_no) <= 13 and '.' not in self.id_no:
                formatting = self.id_no[:4] + '.' + self.id_no[4:6] + '.' + self.id_no[6:8] + '.' + self.id_no[8:]
                self.id_no = formatting

    # This method will create a new contact based on the first name, middle name, last name when you create a new record
    # if there isn't already a contact of that record
    @api.model_create_multi
    def create(self, vals):
        res = super(KycRetail, self).create(vals)
        name = ''
        for rec in res:
            if rec.customer_no == 'New':
                rec.customer_no = self.env['ir.sequence'].next_by_code('kyc.retail') or 'New'
            rec.state = 'waiting_approval'
            rec._home_telephone_length()
            rec._cellular_tel_length()
            if not rec.partner_id.name:
                if rec.name and rec.middle_name and rec.last_name:
                    name = rec.name + ' ' + rec.middle_name + ' ' + rec.last_name
                elif rec.name and rec.last_name:
                    name = rec.name + ' ' + rec.last_name
                if name:
                    customer = rec.env['res.partner'].create({'name': name,
                                                              'kyc_customer_number': rec.customer_no,
                                                              'kyc_type': 'retail',
                                                              'status': rec.status})
                    rec.customer_name = customer.name
                    rec.partner_id = customer
        return res

    """
    **===============================================================================**
    **      During update a Group name and number field will post message in chatter **
    **===============================================================================**
    """

    def write(self, vals):
        old_num = self.mapped('group_ids.group_number')
        old_role = self.mapped('group_role_ids.name')
        if self.flag_state:
            vals['state'] = 'waiting_approval'
            vals['flag_state'] = False
        if vals.get('state') == 'approved' and self.state =='waiting_approval':
            vals['flag_state'] = True
            

            # import pdb;pdb.set_trace();


        res = super(KycRetail, self).write(vals)
        if 'tel_home' in vals:
            self._home_telephone_length()
        if 'tel_cellular' in vals or 'tel_employer' in vals:
            self._cellular_tel_length()
        new_num = self.mapped('group_ids.group_number')
        new_role = self.mapped('group_role_ids.name')
        value_num = []
        old_number = []
        value_role = []
        old_roles_groups = []
        if new_num != old_num:
            for val in new_num:
                value_num.append(val)
            new_value = ', '.join(value_num)
            for old in old_num:
                old_number.append(old)
            old_value = ', '.join(old_number)
            self.message_post(body='<b>OLD GROUP No:</b> %s <br> <b>NEW GROUP No:</b> %s' % (old_value, new_value))
        if new_role != old_role:
            for role in new_role:
                value_role.append(role)
            new_roles = ', '.join(value_role)
            for old_rol in old_role:
                old_roles_groups.append(old_rol)
            old_roles = ', '.join(old_roles_groups)
            self.message_post(body='<b>OLD ROLE: </b> %s <br> <b>NEW ROLE:</b> %s' % (old_roles, new_roles))
        return res

    """
    **===========================================================================================**
    These methods will add '9 ' at the start of the phone number id phone code CW (599) is selected
    **********      and also remove the phone number if any other value is selected      **********
    **===========================================================================================**
    """

    @api.onchange('home_code')
    def set_tel_home_default_value(self):
        if self.home_code == '599 CW':
            self.tel_home = '9 '
        else:
            self.tel_home = ''

    @api.onchange('cellular_code')
    def set_tel_cellular_default_value(self):
        if self.cellular_code == '599 CW':
            self.tel_cellular = '9 '
        else:
            self.tel_cellular = ''

    @api.onchange('employer_code')
    def set_tel_employer_default_value(self):
        if self.employer_code == '599 CW':
            self.tel_employer = '9 '
        else:
            self.tel_employer = ''

    """
    **=====================================================================**
    ** Smart button will display document list view of the current partner **
    **=====================================================================**
    """

    def attachment_tree_view(self):
        return {
            'name': _('Documents'),
            'domain': [('res_model', '=', 'kyc.retail'), ('res_id', '=', self.id)],
            'res_model': 'documents.document',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,kanban',
            'context': {
                "default_partner_id": self.partner_id.id,
                'default_res_model': 'kyc.retail', 'default_res_id': self.id, "searchpanel_default_folder_id": False
                # "searchpanel_default_folder_id": self.env.ref('smart_loan_system.document_folder_id_ext').id
            },
        }

    """
    **========================================================================================**
    ** Count a documents according to Kyc Retail model and res_id and assign in computed field**
    **========================================================================================**
    """

    def _compute_attached_docs_count(self):
        read_group_var = self.env['documents.document'].search_count(
            [('res_model', '=', 'kyc.retail'), ('res_id', '=', self.id)])
        for record in self:
            record.doc_count = read_group_var

    """
    **========================================================================================**
    **      Count a Records according to Groups and Number and assign in computed field       **
    **========================================================================================**
    """

    def _compute_attached_docs_corp_count(self):
        corp_count = []
        for corp in self:
            # groups = corp.mapped('group_ids').ids
            corporates = corp.env['kyc.corporate'].search([])
            for line in corporates:
                ubo = line.mapped('retail_ubo_ids.kyc_customer_ubo_id').ids
                directors = line.mapped('retail_director_ids.customer_no_directors_id').ids
                signers = line.mapped('retail_signer_ids.kyc_retail_signers_id').ids
                contact_persons = line.mapped('retail_contact_per_ids.kyc_contact_person_id').ids
                if corp.id in ubo or corp.id in directors or corp.id in signers or corp.id in contact_persons:
                    corp_count.append(line.id)
        corp.doc_corp_count = len(corp_count)
        return corp_count

    def open_corporate_record(self):
        corp_ids = self._compute_attached_docs_corp_count()
        return {
            'name': _('Corporate'),
            'domain': [('id', 'in', corp_ids)],
            'res_model': 'kyc.corporate',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form,kanban',
        }

    def open_groups_record(self):
        group_ids = self._compute_kyc_groups_count()
        return {
            'name': _('Groups'),
            'domain': [('id', 'in', group_ids)],
            'res_model': 'kyc.groups',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
        }

    def _compute_kyc_groups_count(self):
        group_count = []
        for group in self:
            # groups = group.mapped('group_ids').ids
            kyc_groups = group.env['kyc.groups'].search([])
            for line in kyc_groups:
                ubo = line.mapped('retail_ubo_ids.kyc_customer_ubo_id').ids
                directors = line.mapped('retail_director_ids.customer_no_directors_id').ids
                signers = line.mapped('retail_signer_ids.kyc_retail_signers_id').ids
                contacts = line.mapped('retail_contact_per_ids.kyc_contact_person_id').ids
                if group.id in ubo or group.id in directors or group.id in signers or group.id in contacts:
                    group_count.append(line.id)
                # else:
                #     group_count.append(line.id)
        group.kyc_groups_count = len(group_count)
        return group_count
