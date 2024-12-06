from odoo import models, fields, api, _


class KycRetailUbo(models.Model):
    _name = 'kyc.retail.ubos'
    _description = 'This model contains all the members of KYC Retail UBOs'
    # _rec_name = 'kyc_customer_ubo_id'

    # UBO's information section fields (retrieve from kyc retail)
    kyc_customer_ubo_id = fields.Many2one('kyc.retail', string='Customer Number',
                                          domain="[('group_role_ids.name', '=', 'UBO')]")
    ubo_name = fields.Char('Name', related='kyc_customer_ubo_id.name')
    ubo_last_name = fields.Char('Last Name', related='kyc_customer_ubo_id.last_name')
    ubo_gender = fields.Selection(related='kyc_customer_ubo_id.gender')
    ubo_id_no = fields.Char('ID number #', related='kyc_customer_ubo_id.id_no')
    ubo_driving_licence_no = fields.Char('Driving License number #', related='kyc_customer_ubo_id.driving_licence_no')
    ubo_passport_no = fields.Char('Passport number #', related='kyc_customer_ubo_id.passport_no')
    ubo_tel_home = fields.Char(related='kyc_customer_ubo_id.tel_home')
    ubo_home_code = fields.Selection(related='kyc_customer_ubo_id.home_code')
    ubo_cellular_code = fields.Selection(related='kyc_customer_ubo_id.cellular_code')
    ubo_tel_cellular = fields.Char(related='kyc_customer_ubo_id.tel_cellular')
    ubo_email = fields.Char('Email', related='kyc_customer_ubo_id.mail')
    telephone_home = fields.Char('Telephone Home')
    telephone_cellular = fields.Char('Telephone Cellular')

    # these fields create a relation with the corporate and groups model
    ubos_corporate_id = fields.Many2one('kyc.corporate')
    ubos_group_id = fields.Many2one('kyc.groups')


    def name_get(self):
        res = []
        for rec in self:
            res.append((rec.id, '%s-%s-%s' % (rec.kyc_customer_ubo_id.customer_no, rec.kyc_customer_ubo_id.name, rec.kyc_customer_ubo_id.last_name)))
        return res

    # this method combines the phone number and phone code of the record into one field
    @api.onchange('ubo_home_code')
    def combine_phone_number(self):
        if self.ubo_home_code:
            phone_code_home = [int(integer) for integer in self.ubo_home_code.split() if integer.isdigit()]
            phone_code_cellular = [int(integer) for integer in self.ubo_cellular_code.split() if
                                   integer.isdigit()]
            self.telephone_home = str(phone_code_home[0]) + ' ' + str(self.ubo_tel_home)
            self.telephone_cellular = str(phone_code_cellular[0]) + ' ' + str(self.ubo_tel_cellular)

    """
    **==================================================================================================**
    **This model is to fetch the UBOs from the retail form and pass it to the corporate and groups model**
    **==================================================================================================**
    """