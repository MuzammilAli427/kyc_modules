import re
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class KycCorporate(models.Model):
    _name = 'kyc.corporate'
    _description = 'This model contains all the members of KYC Corporate'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name asc'
    # _rec_name = 'customer_no'

    # corporate information section fields
    customer = fields.Char(string='Customer Name', compute='_compute_customer', readonly=True, tracking=True)
    partner_id = fields.Many2one('res.partner')
    currency_id = fields.Many2one('res.currency', related='partner_id.currency_id')
    status = fields.Selection(
        [('active', 'Active'),
         ('unactive', 'None Active')],
        'Status', tracking=True)
    state = fields.Selection(
        [('draft', 'Draft'),
         ('waiting_approval', 'Waiting On Approval'),
         ('approved', 'Approved')
         ],
        'Approval State', tracking=True)
    customer_no = fields.Char('Customer Number', tracking=True, store=True, default='New')
    group_ids = fields.Many2many('kyc.groups', string='Group Number')
    name = fields.Char('Legal Name', tracking=True)
    trade_name = fields.Char('Trade Name', tracking=True)
    kvk_status = fields.Selection(
        [('active', 'Active'),
         ('unactive', 'None Active'),
         ('liquidated', 'Liquidated')],
        'KVK Status', tracking=True)
    kvk_no = fields.Char('KVK number #', tracking=True)
    kvk_issue_date = fields.Date('KVK Issue Date', tracking=True)
    business_start_date = fields.Date('Date of Incorporation', tracking=True)
    tel_office1 = fields.Char('Telephone Office 1', required=True, tracking=True)
    tel_office2 = fields.Char('Telephone Office 2', required=False, tracking=True)
    office_code1 = fields.Selection(selection=lambda self: self._get_phone_code(), default='599 CW', tracking=True)
    office_code2 = fields.Selection(selection=lambda self: self._get_phone_code(), default='599 CW', tracking=True)
    cellular_code = fields.Selection(selection=lambda self: self._get_phone_code(), default='599 CW', tracking=True)
    tel_cellular = fields.Char('Telephone Cellular', required=True, tracking=True)
    email = fields.Char('Email', tracking=True)

    # business address section fields
    business_address = fields.Char('Address', tracking=True)
    business_neighborhood = fields.Char('Neighborhood', tracking=True)
    business_city = fields.Char('City', tracking=True)
    business_country_id = fields.Many2one('res.country', string='Country')

    # mailing address section fields
    mail_address = fields.Char('Address', tracking=True)
    mail_neighborhood = fields.Char('Neighborhood', tracking=True)
    mail_city = fields.Char('City', tracking=True)
    mail_country_id = fields.Many2one('res.country', string='Country')

    # this field create a relation with the signers model to fetch the values
    retail_signer_ids = fields.One2many('kyc.retail.signers', 'signers_corporate_id')

    # this field create a relation with the directors model to fetch the values
    retail_director_ids = fields.One2many('kyc.retail.directors', 'directors_corporate_id')

    # this field create a relation with the ubos model to fetch the values
    retail_ubo_ids = fields.One2many('kyc.retail.ubos', 'ubos_corporate_id')

    # this field create a relation with the contact_person model to fetch the values
    retail_contact_per_ids = fields.One2many('kyc.contact.person', 'contact_per_corp_id')

    image = fields.Binary('Image')
    comment = fields.Html(tracking=True)

    # This is the counter of number of documents attached to the record
    doc_count = fields.Integer(compute='_compute_attached_docs_count', string="Number of documents attached")
    loan_count = fields.Integer(string='Loans', compute="get_loan_count")
    total_payment_amount = fields.Float('Total Payment Amount', compute='cal_payment_amt')
    total_invoiced = fields.Monetary(compute='_invoice_total', string="Total Invoiced")
    total_due = fields.Monetary(compute='_compute_total_due')
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


    # these are the constraints to get unique value
    _sql_constraints = [
        ('customer_no_uniq', 'unique (customer_no)', 'Customer number must be unique.'),
        ('legal_name_uniq', 'unique (name)', 'Legal Name must be unique.'),
        ('trade_name_uniq', 'unique (trade_name)', 'Trade Name must be unique.'),
        ('kvk_no_uniq', 'unique (kvk_no)', 'KVK number must be unique.')
    ]

    def approve_corporate(self):
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
            res.append((rec.id, '%s / %s' % (rec.customer_no, rec.name)))
        return res

    @api.depends('name')
    def _compute_customer(self):
        for rec in self:
            if rec.name:
                rec.customer = rec.name
            else:
                rec.customer = ' '

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

    # This will give an error if the KVK number is not between 4 and 6
    @api.onchange('kvk_no')
    def _check_kvk_no(self):
        length = len(str(self.kvk_no))
        if length < 4 or length > 6:
            raise ValidationError(_('KVK number must be between 4 and 6'))

    # This will give an error if the cellular phone number and phone code combined exceed the limit of 12
    @api.onchange('tel_cellular', 'cellular_code')
    def _cellular_tel_combined_length(self):
        if self.cellular_code and self.tel_cellular:
            tel_cellular = self.tel_cellular.replace(' ', '').replace('-', '')
            cellular_code = re.findall('\d+', self.cellular_code)
            combined_digits = cellular_code[0] + tel_cellular
            if len(combined_digits) > 12:
                raise ValidationError("The length of phone number cannot exceed 12 digits.")

    # This will give an error if the office 1 phone number and phone code combined exceed the limit of 12
    @api.onchange('tel_office1', 'office_code1')
    def _tel_office1_combined_length(self):
        if self.office_code1 and self.tel_office1:
            tel_office1 = self.tel_office1.replace(' ', '').replace('-', '')
            office_code1 = re.findall('\d+', self.office_code1)
            combined_digits = office_code1[0] + tel_office1
            if len(combined_digits) > 12:
                raise ValidationError("The length of phone number cannot exceed 12 digits.")

    # This will give an error if the Office 2 phone number and phone code combined exceed the limit of 12
    @api.onchange('tel_office2', 'office_code2')
    def _tel_office2_combined_length(self):
        if self.office_code2 and self.tel_office2:
            tel_office2 = self.tel_office2.replace(' ', '').replace('-', '')
            office_code2 = re.findall('\d+', self.office_code2)
            combined_digits = office_code2[0] + tel_office2
            if len(combined_digits) > 12:
                raise ValidationError("The length of phone number cannot exceed 12 digits.")

    def _cellular_tel_length(self):
        if self.cellular_code:
            tel_cellular = self.tel_cellular.replace(' ', '').replace('-', '')
            if not len(tel_cellular) > 6:
                raise ValidationError("The length of Telephone Cellular must be between 7 and 12 digits.")

    # This will give an error if the office 1 phone number and phone code combined exceed the limit of 12
    def _tel_office1_length(self):
        if self.tel_office1:
            tel_office1 = self.tel_office1.replace(' ', '').replace('-', '')
            if not len(tel_office1) > 6:
                raise ValidationError("The length of Telephone Office 1 must be between 7 and 12 digits.")

    # This will give an error if the Office 2 phone number and phone code combined exceed the limit of 12
    def _tel_office2_length(self):
        if self.tel_office2:
            tel_office2 = self.tel_office2.replace(' ', '').replace('-', '')
            if not len(tel_office2) > 0:
                raise ValidationError("The length of Telephone Office 2 must be between 7 and 12 digits.")

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

    @api.onchange('kvk_no')
    def _check_numbers_kvk_no(self):
        for record in self:
            if record.kvk_no and not record.kvk_no.isdigit():
                raise ValidationError("Only numbers are allowed in KVK Number.")

    @api.onchange('tel_cellular')
    def _check_numbers_tel_cellular(self):
        for record in self:
            if record.tel_cellular:
                tel_cellular = record.tel_cellular.replace(' ', '').replace('-', '')
                if not tel_cellular.isdigit():
                    raise ValidationError("Only numbers are allowed in Cellular Telephone.")

    @api.onchange('tel_office1')
    def _check_numbers_tel_office1(self):
        for record in self:
            if record.tel_office1:
                tel_office1 = record.tel_office1.replace(' ', '').replace('-', '')
                if not tel_office1.isdigit():
                    raise ValidationError("Only numbers are allowed in Cellular Telephone.")

    @api.onchange('tel_office2')
    def _check_numbers_tel_office2(self):
        for record in self:
            if record.tel_office2:
                tel_office2 = record.tel_office2.replace(' ', '').replace('-', '')
                if not tel_office2.isdigit():
                    raise ValidationError("Only numbers are allowed in Cellular Telephone.")

    """
                                                 END
        ##########################################################################################
    
    """

    # This method will create a new contact based on the legal name if there isn't already a contact for that record
    @api.model_create_multi
    def create(self, vals):
        res = super(KycCorporate, self).create(vals)
        name = ''
        for rec in res:
            if rec.customer_no == 'New':
                rec.customer_no = self.env['ir.sequence'].next_by_code('kyc.corporate') or 'New'
            rec.state = 'waiting_approval'
            rec._cellular_tel_length()
            rec._tel_office1_length()
            rec._tel_office2_length()
            if not rec.partner_id.name:
                if rec.name:
                    name = rec.name
                if name:
                    customer = rec.env['res.partner'].create({'name': name,
                                                              'kyc_customer_number': rec.customer_no,
                                                              'kyc_type': 'corporate',
                                                              'status': rec.status})
                    rec.customer = customer.name
                    rec.partner_id = customer
        return res

    def write(self, vals):
        old_num = self.mapped('group_ids.group_number')
        old_sig_customer_num = self.retail_signer_ids.mapped('kyc_retail_signers_id.customer_no')
        old_dir_customer_num = self.retail_director_ids.mapped('customer_no_directors_id.customer_no')
        old_ubo_customer_num = self.retail_ubo_ids.mapped('kyc_customer_ubo_id.customer_no')
        old_cp_customer_num = self.retail_contact_per_ids.mapped('kyc_contact_person_id.customer_no')
        if self.flag_state:
            vals['state'] = 'waiting_approval'
            vals['flag_state'] = False
        if vals.get('state') == 'approved' and self.state =='waiting_approval':
            vals['flag_state'] = True
            
        res = super(KycCorporate, self).write(vals)
        new_sig_customer_num = self.retail_signer_ids.mapped('kyc_retail_signers_id.customer_no')
        new_dir_customer_num = self.retail_director_ids.mapped('customer_no_directors_id.customer_no')
        new_ubo_customer_num = self.retail_ubo_ids.mapped('kyc_customer_ubo_id.customer_no')
        new_cp_customer_num = self.retail_contact_per_ids.mapped('kyc_contact_person_id.customer_no')
        new_num = self.mapped('group_ids.group_number')
        if new_num != old_num:
            old_value, new_value = self.get_old_new_values(old_num, new_num)
            self.message_post(body='<b>OLD GROUP No:</b> %s <br> <b>NEW GROUP No:</b> %s' % (old_value, new_value))
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
        if old_cp_customer_num != new_cp_customer_num:
            old_cp, new_cp = self.get_old_new_values(old_cp_customer_num, new_cp_customer_num)
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

    """
    **=====================================================================**
    ** Smart button will display document list view of the current partner **
    **=====================================================================**
    """

    def attachment_tree_view_corporate(self):
        return {
            'name': _('Documents'),
            'domain': [('res_model', '=', 'kyc.corporate'), ('res_id', '=', self.id)],
            'res_model': 'documents.document',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,kanban',
            'context': {
                "default_partner_id": self.partner_id.id,
                'default_res_model': 'kyc.corporate', 'default_res_id': self.id, "searchpanel_default_folder_id": False
                # "searchpanel_default_folder_id": self.env.ref('smart_loan_system.document_folder_kvk').id
            },
        }

    """
        **========================================================================================**
        ** Count a documents according to Kyc Retail model and res_id and assign in computed field**
        **========================================================================================**
        """

    def _compute_attached_docs_count(self):
        read_group_var = self.env['documents.document'].search_count(
            [('res_model', '=', 'kyc.corporate'), ('res_id', '=', self.id)])
        for record in self:
            record.doc_count = read_group_var
