from odoo import models, fields, api, _


class KycRetailDirectors(models.Model):
    _name = 'kyc.retail.directors'
    _description = 'This model contains all the members of KYC Retail Directors'
    # _rec_name = 'customer_no_directors_id'

    # Directors information section fields (retrieve from kyc retail)
    customer_no_directors_id = fields.Many2one('kyc.retail', string='Customer Number',
                                               domain="[('group_role_ids.name', '=', 'Director')]")
    directors_name = fields.Char('Name', related='customer_no_directors_id.name')
    directors_last_name = fields.Char('Last Name', related='customer_no_directors_id.last_name')
    directors_gender = fields.Selection(related='customer_no_directors_id.gender')
    directors_id_no = fields.Char('ID number #', related='customer_no_directors_id.id_no')
    directors_driving_licence_no = fields.Char('Driving License number #',
                                               related='customer_no_directors_id.driving_licence_no')
    directors_passport_no = fields.Char('Passport number #', related='customer_no_directors_id.passport_no')
    directors_tel_home = fields.Char(related='customer_no_directors_id.tel_home')
    directors_home_code = fields.Selection(related='customer_no_directors_id.home_code')
    directors_cellular_code = fields.Selection(related='customer_no_directors_id.cellular_code')
    directors_tel_cellular = fields.Char(related='customer_no_directors_id.tel_cellular')
    telephone_home = fields.Char('Telephone Home')
    telephone_cellular = fields.Char('Telephone Cellular')
    directors_email = fields.Char('Email', related='customer_no_directors_id.mail')

    # these fields create a relation with the corporate and groups model
    directors_corporate_id = fields.Many2one('kyc.corporate')
    directors_group_id = fields.Many2one('kyc.groups')

    # this method combines the phone number and phone code of the record into one field
    @api.onchange('directors_home_code')
    def combine_phone_number(self):
        if self.directors_home_code:
            phone_code_home = [int(integer) for integer in self.directors_home_code.split() if integer.isdigit()]
            phone_code_cellular = [int(integer) for integer in self.directors_cellular_code.split() if
                                   integer.isdigit()]
            self.telephone_home = str(phone_code_home[0]) + ' ' + str(self.directors_tel_home)
            self.telephone_cellular = str(phone_code_cellular[0]) + ' ' + str(self.directors_tel_cellular)

    """
    **=======================================================================================================**
    **This model is to fetch the Directors from the retail form and pass it to the corporate and groups model**
    **=======================================================================================================**
    """
