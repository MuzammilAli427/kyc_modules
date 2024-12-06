from odoo import api, fields, models,_
from ast import literal_eval

class ResConfigSettings(models.TransientModel):

    _inherit = 'res.config.settings'

    write_off_account_id = fields.Many2one('account.account', string='Write-Off Account')
    principal_prod_id = fields.Many2one('product.product', string='Principal Product',
            help='Product used to invoice as principal of the loans.')
    interest_prod_id = fields.Many2one('product.product', string='Interest Product',
            help='Product used to invoice as interest of the loans.')
    bonaire_principal_prod_id = fields.Many2one('product.product', string='Bonaire Principal Product',
            help='Bonaire Product used to invoice as principal of the loans.')
    bonaire_interest_prod_id = fields.Many2one('product.product', string='Bonaire Interest Product',
                                                help='Bonaire Product used to invoice as interest of the loans.')
    penalty_prod_id = fields.Many2one('product.product', string='Penalty Product',
                                                help='Product used to invoice as penalty of the loans.')
    processing_fee_prod_id = fields.Many2one('product.product', string='Processing Fee',
           help='Product used as Processing fee of the loans.')
    acc_rec_id = fields.Many2one('account.account', string="Loan Account Receivable")
    income_acc_id = fields.Many2one('account.account', string="Loan Income Account")
    loan_jou_id = fields.Many2one('account.journal', string="Loans Journal")
    disbursement_acc_id = fields.Many2one('account.account', string="Disbursement Account")
    difference_acc_id = fields.Many2one('account.account', string="Difference Account")
    fee_commission_acc_id = fields.Many2one('account.account', string="Difference Account")
    loan_suspense_acc_id = fields.Many2one('account.account', string="Loan Suspense Account")
    early_payment_prod_id = fields.Many2one('product.product', string='Early Payment Product',
                                                help='Early Payment Product used to invoice as early payment of the loans.')
    early_partial_payment_prod_id = fields.Many2one('product.product', string='Early Partial Payment Product',
                                            help='Early Partial Payment Product used to invoice as early partial payment of the loans.')
    restructuring_prod_id = fields.Many2one('product.product', string='Restructuring Product',
                                            help='Restructuring Product used to invoice as restructuring fee of the loans.')
    ob_tax_prod_id = fields.Many2one('product.product', string='OB Tax Product',
                                            help='OB Tax Product used to invoice as OB Tax of Restructuring  of the loans.')
    ground_lease_product_id = fields.Many2one('product.product', string='Ground Lease Product',
                                     help='Ground Lease Product used to invoice as Ground Lease of the loans.')
    max_delinquent_period = fields.Integer()

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        write_off_account_id = literal_eval(ICPSudo.get_param('ae_loan_manag.write_off_account_id','False'))
        principal_prod_id = literal_eval(ICPSudo.get_param('ae_loan_manag.principal_prod_id','False'))
        interest_prod_id = literal_eval(ICPSudo.get_param('ae_loan_manag.interest_prod_id','False'))
        bonaire_principal_prod_id = literal_eval(ICPSudo.get_param('ae_loan_manag.bonaire_principal_prod_id', 'False'))
        bonaire_interest_prod_id = literal_eval(ICPSudo.get_param('ae_loan_manag.bonaire_interest_prod_id', 'False'))
        processing_fee_prod_id = literal_eval(ICPSudo.get_param('ae_loan_manag.processing_fee_prod_id','False'))
        penalty_prod_id = literal_eval(ICPSudo.get_param('ae_loan_manag.penalty_prod_id','False'))
        acc_rec_id = literal_eval(ICPSudo.get_param('ae_loan_manag.acc_rec_id', 'False'))
        income_acc_id = literal_eval(ICPSudo.get_param('ae_loan_manag.income_acc_id', 'False'))
        loan_jou_id = literal_eval(ICPSudo.get_param('ae_loan_manag.loan_jou_id', 'False'))
        disbursement_acc_id = literal_eval(ICPSudo.get_param('ae_loan_manag.disbursement_acc_id', 'False'))
        difference_acc_id = literal_eval(ICPSudo.get_param('ae_loan_manag.difference_acc_id', 'False'))
        fee_commission_acc_id = literal_eval(ICPSudo.get_param('ae_loan_manag.fee_commission_acc_id', 'False'))
        loan_suspense_acc_id = literal_eval(ICPSudo.get_param('ae_loan_manag.loan_suspense_acc_id', 'False'))
        early_payment_prod_id = literal_eval(ICPSudo.get_param('ae_loan_manag.early_payment_prod_id', 'False'))
        early_partial_payment_prod_id = literal_eval(ICPSudo.get_param('ae_loan_manag.early_partial_payment_prod_id', 'False'))
        restructuring_prod_id = literal_eval(ICPSudo.get_param('ae_loan_manag.restructuring_prod_id', 'False'))
        ob_tax_prod_id = literal_eval(ICPSudo.get_param('ae_loan_manag.ob_tax_prod_id', 'False'))
        ground_lease_product_id = literal_eval(ICPSudo.get_param('ae_loan_manag.ground_lease_product_id', 'False'))
        max_delinquent_period = literal_eval(ICPSudo.get_param('ae_loan_manag.max_delinquent_period', 'False'))

        res.update(
            write_off_account_id = write_off_account_id,
            principal_prod_id = principal_prod_id,
            interest_prod_id = interest_prod_id,
            bonaire_principal_prod_id = bonaire_principal_prod_id,
            bonaire_interest_prod_id = bonaire_interest_prod_id,
            processing_fee_prod_id = processing_fee_prod_id,
            penalty_prod_id = penalty_prod_id,
            acc_rec_id = acc_rec_id,
            income_acc_id = income_acc_id,
            loan_jou_id = loan_jou_id,
            disbursement_acc_id = disbursement_acc_id,
            early_payment_prod_id = early_payment_prod_id,
            early_partial_payment_prod_id = early_partial_payment_prod_id,
            difference_acc_id = difference_acc_id,
            fee_commission_acc_id = fee_commission_acc_id,
            loan_suspense_acc_id = loan_suspense_acc_id,
            restructuring_prod_id = restructuring_prod_id,
            ob_tax_prod_id = ob_tax_prod_id,
            ground_lease_product_id = ground_lease_product_id,
            max_delinquent_period = max_delinquent_period
        )
        return res

    # @api.multi
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        ICPSudo.set_param("ae_loan_manag.write_off_account_id", self.write_off_account_id.id)
        ICPSudo.set_param("ae_loan_manag.principal_prod_id", self.principal_prod_id.id)
        ICPSudo.set_param("ae_loan_manag.interest_prod_id", self.interest_prod_id.id)
        ICPSudo.set_param("ae_loan_manag.bonaire_principal_prod_id", self.bonaire_principal_prod_id.id)
        ICPSudo.set_param("ae_loan_manag.bonaire_interest_prod_id", self.bonaire_interest_prod_id.id)
        ICPSudo.set_param("ae_loan_manag.processing_fee_prod_id", self.processing_fee_prod_id.id)
        ICPSudo.set_param("ae_loan_manag.penalty_prod_id", self.penalty_prod_id.id)
        ICPSudo.set_param("ae_loan_manag.acc_rec_id", self.acc_rec_id.id)
        ICPSudo.set_param("ae_loan_manag.income_acc_id", self.income_acc_id.id)
        ICPSudo.set_param("ae_loan_manag.loan_jou_id", self.loan_jou_id.id)
        ICPSudo.set_param("ae_loan_manag.disbursement_acc_id", self.disbursement_acc_id.id)
        ICPSudo.set_param("ae_loan_manag.difference_acc_id", self.difference_acc_id.id)
        ICPSudo.set_param("ae_loan_manag.fee_commission_acc_id", self.fee_commission_acc_id.id)
        ICPSudo.set_param("ae_loan_manag.loan_suspense_acc_id", self.loan_suspense_acc_id.id)
        ICPSudo.set_param("ae_loan_manag.early_payment_prod_id", self.early_payment_prod_id.id)
        ICPSudo.set_param("ae_loan_manag.early_partial_payment_prod_id", self.early_partial_payment_prod_id.id)
        ICPSudo.set_param("ae_loan_manag.restructuring_prod_id", self.restructuring_prod_id.id)
        ICPSudo.set_param("ae_loan_manag.ob_tax_prod_id", self.ob_tax_prod_id.id)
        ICPSudo.set_param("ae_loan_manag.ground_lease_product_id", self.ground_lease_product_id.id)
        ICPSudo.set_param("ae_loan_manag.max_delinquent_period", self.max_delinquent_period)