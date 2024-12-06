from odoo import models, fields, api, _


class KycRetailSigners(models.Model):
    _name = 'kyc.retail.signers'
    _description = 'This model contains all the members of KYC Retail Signers'
    # _rec_name = 'kyc_retail_signers_id'

    # signers information section fields (retrieve from kyc retail)
    kyc_retail_signers_id = fields.Many2one('kyc.retail', string='Customer Number',
                                            domain="[('group_role_ids.name', '=', 'Signer')]")
    signers_name = fields.Char('Name', related='kyc_retail_signers_id.name')
    signers_last_name = fields.Char('Last Name', related='kyc_retail_signers_id.last_name')
    signers_gender = fields.Selection(related='kyc_retail_signers_id.gender')
    signers_id_no = fields.Char('ID number #', related='kyc_retail_signers_id.id_no')
    signers_driving_licence_no = fields.Char('Driving License number #',
                                             related='kyc_retail_signers_id.driving_licence_no')
    signers_passport_no = fields.Char('Passport number #', related='kyc_retail_signers_id.passport_no')
    signers_tel_home = fields.Char(related='kyc_retail_signers_id.tel_home')
    signers_home_code = fields.Selection(related='kyc_retail_signers_id.home_code')
    telephone_home = fields.Char('Telephone Home')
    telephone_cellular = fields.Char('Telephone Cellular')
    signers_cellular_code = fields.Selection(related='kyc_retail_signers_id.cellular_code')
    signers_tel_cellular = fields.Char(related='kyc_retail_signers_id.tel_cellular')
    signers_email = fields.Char('Email', related='kyc_retail_signers_id.mail')

    # these fields create a relation with the corporate and groups model
    signers_corporate_id = fields.Many2one('kyc.corporate')
    signers_group_id = fields.Many2one('kyc.groups')

    # this method combines the phone number and phone code of the record into one field
    @api.onchange('signers_home_code')
    def combine_phone_number(self):
        if self.signers_home_code:
            phone_code_home = [int(integer) for integer in self.signers_home_code.split() if integer.isdigit()]
            phone_code_cellular = [int(integer) for integer in self.signers_cellular_code.split() if integer.isdigit()]
            self.telephone_home = str(phone_code_home[0]) + ' ' + str(self.signers_tel_home)
            self.telephone_cellular = str(phone_code_cellular[0]) + ' ' + str(self.signers_tel_cellular)

    """
    **=====================================================================================================**
    **This model is to fetch the Signers from the retail form and pass it to the corporate and groups model**
    **=====================================================================================================**
    """