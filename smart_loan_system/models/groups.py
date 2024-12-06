import re
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class KycGroups(models.Model):
    _name = 'kyc.groups'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Assign groups to Retail and Corporate customers'
    _order = 'standard_group_name asc'
    # _rec_name = 'group_number'

    # by selecting a value in this field you will see the fields for a Standard group or a Legal Group
    group_type = fields.Selection(
        [('standard', 'Standard Group'),
         ('legal', 'Legal Group')],
        'Group Type', tracking=True
    )

    state = fields.Selection(
        [('draft', 'Draft'),
         ('waiting_approval', 'Waiting On Approval'),
         ('approved', 'Approved')
         ],
        'Approval State', tracking=True)

    # Standard group Fields
    status = fields.Selection(
        [('active', 'Active'),
         ('unactive', 'None Active')],
        'Status', tracking=True)
    standard_group_name = fields.Char('Group Name', tracking=True)
    group_number = fields.Char('Group Number', tracking=True, store=True, default='New')
    description = fields.Text('Description', tracking=True)

    # these fields take count for the retail and corporate
    rec_count_retail = fields.Integer(compute='_compute_attached_docs_count_retail',
                                      string="Number of documents attached")
    rec_count_corporate = fields.Integer(compute='_compute_attached_docs_count_corporate',
                                         string="Number of documents attached")
    partner_id = fields.Many2one('res.partner', tracking=True)
    loan_collateral_count = fields.Integer(compute='_compute_loan_collateral_count')
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


    def approve_group(self):
        for rec in self:
            rec.write({'state': 'approved'})

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

    # these constraints are for validations and making a pattern
    # @api.constrains('group_number')
    # def _check_group_number(self):
    #     length = len(str(self.group_number))
    #     if length < 4 or length > 8:
    #         raise ValidationError(_('Group Number digits must be between 4 and 8'))

    # @api.onchange('group_number')
    # def _check_numbers_group_no(self):
    #     for record in self:
    #         if record.group_number and not record.group_number.isdigit():
    #             raise ValidationError("Only numbers are allowed in Group Number.")

    # count for the attached retail records with the same group
    def _compute_attached_docs_count_retail(self):
        Attachment = self.env['kyc.retail']
        for rec in self:
            rec.rec_count_retail = Attachment.search_count([('group_ids.id', '=', rec.id)])

    # count for the attached corporate records with the same group
    def _compute_attached_docs_count_corporate(self):
        Attachment = self.env['kyc.corporate']
        for rec in self:
            rec.rec_count_corporate = Attachment.search_count([('group_ids.id', '=', rec.id)])

    # tree view for the attached retail records with the same group
    def retail_group_tree_view(self):
        domain = [('group_ids', 'in', self.ids)]
        return {
            'name': _('KYC Retail'),
            'domain': domain,
            'res_model': 'kyc.retail',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'tree,form',
            'view_type': 'tree',
        }

    # tree view for the attached corporate records with the same group
    def corporate_group_tree_view(self):
        domain = [('group_ids', 'in', self.ids)]
        return {
            'name': _('KYC Corporate'),
            'domain': domain,
            'res_model': 'kyc.corporate',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'tree,form',
            'view_type': 'tree',
        }

    #### Legal Group fields ####
    # Group Information Section
    customer_no = fields.Char('Customer Number', tracking=True, store=True)
    name = fields.Char('Legal Name', tracking=True)
    trade_name = fields.Char('Trade Name', tracking=True)
    kvk_no = fields.Char('KVK number #', tracking=True)
    kvk_issue_date = fields.Date('KVK Issue Date', tracking=True)
    date_of_incorporation = fields.Date('Date of Incorporation', tracking=True)
    kvk_status = fields.Selection(
        [('active', 'Active'),
         ('unactive', 'None Active'),
         ('liquidated', 'Liquidated')],
        'KVK Status', tracking=True)
    tel_office1 = fields.Char('Telephone Office 1', tracking=True)
    tel_office2 = fields.Char('Telephone Office 2', tracking=True)
    office_code1 = fields.Selection(selection=lambda self: self._get_phone_code(), default='599 CW', tracking=True)
    office_code2 = fields.Selection(selection=lambda self: self._get_phone_code(), default='599 CW', tracking=True)
    cellular_code = fields.Selection(selection=lambda self: self._get_phone_code(), default='599 CW', tracking=True)
    tel_cellular = fields.Char('Telephone Cellular', tracking=True)
    email = fields.Char('Email', tracking=True)

    # Business address Section
    business_address = fields.Char('Address', tracking=True)
    business_neighbourhood = fields.Char('Neighbourhood', tracking=True)
    business_city = fields.Char('City', tracking=True)
    business_country_id = fields.Many2one('res.country', string='Country')

    # Mailing address Section
    mailing_address = fields.Char('Address', tracking=True)
    mailing_neighbourhood = fields.Char('Neighbourhood', tracking=True)
    mailing_city = fields.Char('City', tracking=True)
    mailing_country_id = fields.Many2one('res.country', string='Country')

    # this field create a relation with the signers model to fetch the values
    retail_signer_ids = fields.One2many('kyc.retail.signers', 'signers_group_id')

    # this field create a relation with the directors model to fetch the values
    retail_director_ids = fields.One2many('kyc.retail.directors', 'directors_group_id')

    # this field create a relation with the ubos model to fetch the values
    retail_ubo_ids = fields.One2many('kyc.retail.ubos', 'ubos_group_id')
    doc_count = fields.Integer(compute='_compute_attached_docs_count', string="Number of documents attached")

    retail_contact_per_ids = fields.One2many('kyc.contact.person', 'contact_per_group_id')

    # these are the constraints to get unique value
    _sql_constraints = [
        ('group_name_uniq', 'unique (standard_group_name)', 'Group name must be unique.'),
        ('customer_no_uniq', 'unique (customer_no)', 'Customer number must be unique.'),
        ('standard_group_number_uniq', 'unique (group_number)', 'Group number must be unique.'),
        ('legal_name_uniq', 'unique (name)', 'Legal Name must be unique.'),
        ('trade_name_uniq', 'unique (trade_name)', 'Trade Name must be unique.'),
        ('kvk_no_uniq', 'unique (kvk_no)', 'KVK number must be unique.')
    ]

    @api.model
    def kyc_group_partner_creation(self):
        kyc_groups = self.env['kyc.groups'].search([])
        for group in kyc_groups:
            if group.partner_id:
                name = group.standard_group_name or group.name
                group.partner_id.write({'kyc_customer_number': group.group_number,
                                        'name': group.standard_group_name + 'a' if group.standard_group_name else group.name + 'a',
                                        'kyc_type': 'group',
                                        'status': group.status})
                group.partner_id.write({'name': name})
        kyc_retails = self.env['kyc.retail'].search([])
        for retail in kyc_retails:
            name = ''
            if retail.name and retail.middle_name and retail.last_name:
                name = retail.name + ' ' + retail.middle_name + ' ' + retail.last_name
            elif retail.name and retail.last_name:
                name = retail.name + ' ' + retail.last_name
            if retail.partner_id:
                retail.partner_id.write({'kyc_customer_number': retail.customer_no,
                                         'name': retail.partner_id.name + 'a',
                                         'kyc_type': 'retail',
                                         'status': retail.status})
                retail.partner_id.write({'name': name})
        kyc_corporate = self.env['kyc.corporate'].search([])
        for corporate in kyc_corporate:
            name = corporate.name
            if corporate.partner_id:
                corporate.partner_id.write({'kyc_customer_number': corporate.customer_no,
                                            'name': corporate.name + 'a',
                                            'kyc_type': 'corporate',
                                            'status': corporate.status})
                corporate.partner_id.write({'name': name})

    def name_get(self):
        res = []
        for rec in self:
            # if rec.env.context.get('params') and rec.env.context.get('params').get('model') and rec.env.context.get(
            #         'params').get('model') == rec._name:
            #     res.append((rec.id, '%s' % (rec.group_number)))
            # else:
            res.append((rec.id, '%s / %s' % (rec.group_number, rec.standard_group_name)))
        return res

    # this method calculates the phone codes of each country
    def _get_phone_code(self):
        phone_codes = []
        countries = self.env['res.country'].search([])
        for country in countries:
            phone_codes.append(
                (f'{str(country.phone_code)} {country.code}', f'({str(country.phone_code)})'))
        return phone_codes

    # This method is to validate the email pattern
    @api.onchange('email')
    def validate_email(self):
        if self.email:
            match = re.match(r'^[A-Za-z0-9+/_.]+@[A-Za-z0-9-]+\.[A-Za-z0-9-.]+$', self.email)
            if match == None:
                raise ValidationError(_('Not a valid E-mail'))

    """
    **==========================================================================================**
    **The methods below are constraints to check that only integers are entered in number fields**
    **==========================================================================================**
    """

    # @api.constrains('customer_no')
    # def _check_numbers_customer_no(self):
    #     for record in self:
    #         if record.customer_no and not record.customer_no.isdigit():
    #             raise ValidationError("Only numbers are allowed in Customer Number.")

    @api.constrains('kvk_no')
    def _check_numbers_kvk_no(self):
        for record in self:
            if record.kvk_no and not record.kvk_no.isdigit():
                raise ValidationError("Only numbers are allowed in KVK Number.")

    @api.constrains('tel_cellular')
    def _check_numbers_tel_cellular(self):
        for record in self:
            if record.tel_cellular:
                tel_cellular = record.tel_cellular.replace(' ', '').replace('-', '')
                if not tel_cellular.isdigit():
                    raise ValidationError("Only numbers are allowed in Cellular Telephone.")

    @api.constrains('tel_office1')
    def _check_numbers_tel_office1(self):
        for record in self:
            if record.tel_office1:
                tel_office1 = record.tel_office1.replace(' ', '').replace('-', '')
                if not tel_office1.isdigit():
                    raise ValidationError("Only numbers are allowed in Cellular Telephone.")

    @api.constrains('tel_office2')
    def _check_numbers_tel_office2(self):
        for record in self:
            if record.tel_office2:
                tel_office2 = record.tel_office2.replace(' ', '').replace('-', '')
                if not tel_office2.isdigit():
                    raise ValidationError("Only numbers are allowed in Cellular Telephone.")

    """
    **=============================================================================**
    **These methods verify if the length of the integers fields entered by the user**
    **=============================================================================**
    """

    # This will give an error if the customer number is not between 4 and 8
    # @api.constrains('customer_no')
    # def _check_customer_no(self):
    #     length = len(str(self.customer_no))
    #     if length < 4 or length > 8:
    #         raise ValidationError(_('Customer Number digits must be between 4 and 8'))

    # This will give an error if the KVK number is not between 4 and 6
    @api.constrains('kvk_no')
    def _check_kvk_no(self):
        length = len(str(self.kvk_no))
        if length < 4 or length > 6:
            raise ValidationError(_('KVK number must be between 4 and 6'))

    # This will give an error if the cellular phone number and phone code combined exceed the limit of 12
    @api.onchange('tel_cellular', 'cellular_code')
    def _cellular_tel_combined_length(self):
        if self.cellular_code and self.tel_cellular:
            tel_cellular = self.tel_cellular.replace(' ', '').replace('-', '')
            cellular_code = re.findall(r'\d+', self.cellular_code)
            combined_digits = cellular_code[0] + tel_cellular
            if len(combined_digits) > 12:
                raise ValidationError(
                    "The length of phone number cannot exceed 12 digits.")

    # This will give an error if the office 1 phone number and phone code combined exceed the limit of 12
    @api.onchange('tel_office1', 'office_code1')
    def _tel_office1_combined_length(self):
        if self.office_code1 and self.tel_office1:
            tel_office1 = self.tel_office1.replace(' ', '').replace('-', '')
            office_code1 = re.findall(r'\d+', self.office_code1)
            combined_digits = office_code1[0] + tel_office1
            if len(combined_digits) > 12:
                raise ValidationError(
                    "The length of phone number cannot exceed 12 digits.")

    # This will give an error if the Office 2 phone number and phone code combined exceed the limit of 12
    @api.onchange('tel_office2', 'office_code2')
    def _tel_office2_combined_length(self):
        if self.office_code2 and self.tel_office2:
            tel_office2 = self.tel_office2.replace(' ', '').replace('-', '')
            office_code2 = re.findall(r'\d+', self.office_code2)
            combined_digits = office_code2[0] + tel_office2
            if len(combined_digits) > 12:
                raise ValidationError(
                    "The length of phone number cannot exceed 12 digits.")

    def _cellular_tel_length(self):
        if self.tel_cellular:
            tel_cellular = self.tel_cellular.replace(' ', '').replace('-', '')
            if not len(tel_cellular) > 6 and self.group_type == 'legal':
                raise ValidationError("The length of Telephone Cellular must be between 7 and 12 digits.")

    # This will give an error if the office 1 phone number and phone code combined exceed the limit of 12
    def _tel_office1_length(self):
        if self.tel_office1:
            tel_office1 = self.tel_office1.replace(' ', '').replace('-', '')
            if not len(tel_office1) > 6 and self.group_type == 'legal':
                raise ValidationError("The length of Telephone Office 1 must be between 7 and 12 digits.")

    # This will give an error if the Office 2 phone number and phone code combined exceed the limit of 12
    def _tel_office2_length(self):
        if self.tel_office2:
            tel_office2 = self.tel_office2.replace(' ', '').replace('-', '')
            if not len(tel_office2) > 0 and self.group_type == 'legal':
                raise ValidationError("The length of Telephone Office 2 must be between 7 and 12 digits.")

    """
        **===========================================================================================**
        These methods will add '9 ' at the start of the phone number id phone code CW (599) is selected
        **********      and also remove the phone number if any other value is selected      **********
        **===========================================================================================**
        """

    @api.onchange('office_code1')
    def set_tel_office1_default_value(self):
        if self.office_code1 == '599 CW':
            self.tel_office1 = '9 '
        else:
            self.tel_office1 = ''

    @api.onchange('cellular_code')
    def set_tel_cellular_default_value(self):
        if self.cellular_code == '599 CW':
            self.tel_cellular = '9 '
        else:
            self.tel_cellular = ''

    @api.onchange('office_code2')
    def set_tel_office2_default_value(self):
        if self.office_code2 == '599 CW':
            self.tel_office2 = '9 '
        else:
            self.tel_office2 = ''

    def document_view_for_group(self):
        return {
            'name': _('Documents'),
            'domain': [('res_model', '=', 'kyc.groups'), ('res_id', '=', self.id)],
            'res_model': 'documents.document',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,kanban',
            'context': {
                'default_res_model': 'kyc.groups', 'default_res_id': self.id, "searchpanel_default_folder_id": False,
                'default_legal_name': self.name,
                # "searchpanel_default_folder_id": self.env.ref('smart_loan_system.document_folder_kvk').id
            },
        }

    def _compute_attached_docs_count(self):
        read_group_var = self.env['documents.document'].search_count(
            [('res_model', '=', 'kyc.groups'), ('res_id', '=', self.id)])
        for record in self:
            record.doc_count = read_group_var

    @api.onchange('name')
    def legal_name_to_group(self):
        for rec in self:
            if rec.group_type == 'legal':
                rec.standard_group_name = rec.name

    @api.model_create_multi
    def create(self, vals):
        res = super(KycGroups, self).create(vals)
        name = ''
        for rec in res:
            if rec.group_number == 'New':
                rec.group_number = self.env['ir.sequence'].next_by_code('kyc.groups') or 'New'
            if  rec.group_type == 'legal':
                rec.customer_no = self.env['ir.sequence'].next_by_code('kyc.groups.cust')
            rec.state = 'waiting_approval'
            rec._cellular_tel_length()
            rec._tel_office1_length()
            rec._tel_office2_length()
            if not rec.partner_id:
                if rec.group_type == 'standard' and rec.standard_group_name:
                    name = rec.standard_group_name
                elif rec.group_type == 'legal' and rec.name:
                    name = rec.name
                if name:
                    partner = rec.env['res.partner'].create({'name': name,
                                                             'kyc_customer_number': rec.group_number,
                                                             'kyc_type': 'group'})
                    rec.partner_id = partner
        return res

    def write(self, vals):
        old_sig_customer_num = self.retail_signer_ids.mapped('kyc_retail_signers_id.customer_no')
        old_dir_customer_num = self.retail_director_ids.mapped('customer_no_directors_id.customer_no')
        old_ubo_customer_num = self.retail_ubo_ids.mapped('kyc_customer_ubo_id.customer_no')
        old_contact_per_num = self.retail_contact_per_ids.mapped('kyc_contact_person_id.customer_no')
        if self.flag_state:
            vals['state'] = 'waiting_approval'
            vals['flag_state'] = False
        if vals.get('state') == 'approved' and self.state =='waiting_approval':
            vals['flag_state'] = True

        res = super(KycGroups, self).write(vals)

        new_sig_customer_num = self.retail_signer_ids.mapped('kyc_retail_signers_id.customer_no')
        new_dir_customer_num = self.retail_director_ids.mapped('customer_no_directors_id.customer_no')
        new_ubo_customer_num = self.retail_ubo_ids.mapped('kyc_customer_ubo_id.customer_no')
        new_contact_per_num = self.retail_contact_per_ids.mapped('kyc_contact_person_id.customer_no')

        if old_sig_customer_num != new_sig_customer_num:
            old_customers, new_customers = self.get_old_new_values(old_sig_customer_num, new_sig_customer_num)
            self.message_post(
                body='<b>OLD SIGNER CUSTOMERS NO:</b> %s <br> <b>OLD SIGNER CUSTOMERS NO:</b> %s' % (
                    old_customers, new_customers))
        if old_dir_customer_num != new_dir_customer_num:
            old_dir, new_dir = self.get_old_new_values(old_dir_customer_num, new_dir_customer_num)
            self.message_post(
                body='<b>OLD DIRECTOR CUSTOMERS NO:</b> %s <br> <b>OLD DIRECTOR CUSTOMERS NO:</b> %s' % (
                    old_dir, new_dir))
        if old_ubo_customer_num != new_ubo_customer_num:
            old_ubo, new_ubo = self.get_old_new_values(old_ubo_customer_num, new_ubo_customer_num)
            self.message_post(
                body='<b>OLD UBOs CUSTOMERS NO:</b> %s <br> <b>OLD UBOs CUSTOMERS NO:</b> %s' % (
                    old_ubo, new_ubo))
        if old_contact_per_num != new_contact_per_num:
            old_cp, new_cp = self.get_old_new_values(old_contact_per_num, new_contact_per_num)
            self.message_post(
                body='<b>Old contact customer NO:</b> %s <br> <b>New contact customers NO:</b> %s' % (
                    old_cp, new_cp))
        if 'tel_cellular' in vals:
            self._cellular_tel_length()
        if 'tel_office1' in vals:
            self._tel_office1_length()
        if 'tel_office2' in vals:
            self._tel_office2_length()
        return res

    def get_old_new_values(self, old, new):
        old_list = []
        new_list = []
        for new_line in new:
            new_list.append(new_line)
        new_str = ', '.join(new_list)
        for old_line in old:
            old_list.append(old_line)
        old_str = ', '.join(old_list)
        return old_str, new_str
