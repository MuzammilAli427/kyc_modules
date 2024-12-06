from odoo import fields, models, api


class KycContactPerson(models.Model):
    _name = 'kyc.contact.person'
    _description = 'Kyc Contact Person'
    _rec_name = 'kyc_contact_person_id'

    kyc_contact_person_id = fields.Many2one('kyc.retail', string='Customer Number',
                                            domain="[('group_role_ids.name', '=', 'Contact Person')]")

    contact_per_name = fields.Char('Name', related='kyc_contact_person_id.name')
    contact_per_lastname = fields.Char('Last Name', related='kyc_contact_person_id.last_name')
    contact_per_gender = fields.Selection(related='kyc_contact_person_id.gender')
    contact_per_id_no = fields.Char('ID number #', related='kyc_contact_person_id.id_no')
    contact_per_driving_lic_no = fields.Char('Driving License number #',
                                             related='kyc_contact_person_id.driving_licence_no')
    contact_per_passport_no = fields.Char('Passport number #', related='kyc_contact_person_id.passport_no')
    contact_per_tel_home = fields.Char(related='kyc_contact_person_id.tel_home')
    contact_per_home_code = fields.Selection(related='kyc_contact_person_id.home_code')
    telephone_home = fields.Char('Telephone Home')
    telephone_cellular = fields.Char('Telephone Cellular')
    contact_per_cell_code = fields.Selection(related='kyc_contact_person_id.cellular_code')
    contact_per_tel_cell = fields.Char(related='kyc_contact_person_id.tel_cellular')
    contact_per_email = fields.Char('Email', related='kyc_contact_person_id.mail')

    # these fields create a relation with the corporate and groups model
    contact_per_corp_id = fields.Many2one('kyc.corporate')
    contact_per_group_id = fields.Many2one('kyc.groups')




    @api.onchange('contact_per_home_code')
    def combine_phone_number(self):
        if self.contact_per_home_code:
            phone_code_home = [int(integer) for integer in self.contact_per_home_code.split() if integer.isdigit()]
            phone_code_cellular = [int(integer) for integer in self.contact_per_cell_code.split() if
                                   integer.isdigit()]
            self.telephone_home = str(phone_code_home[0]) + ' ' + str(self.contact_per_tel_home)
            self.telephone_cellular = str(phone_code_cellular[0]) + ' ' + str(self.contact_per_tel_cell)

    """
    **============================================================================================================**
    **This model is to fetch the Contact Person from the retail form and pass it to the corporate and groups model**
    **============================================================================================================**
    """