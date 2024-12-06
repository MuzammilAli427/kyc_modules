from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, AccessError

class Document(models.Model):
    _inherit = "documents.document"

    kyc_date = fields.Date(string="Expiration Date")
    action_by_date = fields.Date(string="Action By Date")

    @api.model_create_multi
    def create(self, vals_list):
        # Define main folders and subfolder categories
        folder_id = self.env.ref('smart_loan_system.document_folder_id_ext').id
        folder_passport = self.env.ref('smart_loan_system.document_folder_passport').id
        folder_driving = self.env.ref('smart_loan_system.document_folder_driving_license').id
        folder_others = self.env.ref('smart_loan_system.document_folder_others').id
        folder_kvk = self.env.ref('smart_loan_system.document_folder_kvk').id
        folder_artical = self.env.ref('smart_loan_system.document_folder_artical_incorp').id
        folder_share_reg = self.env.ref('smart_loan_system.document_folder_share_reg').id
        folder_company_doc = self.env.ref('smart_loan_system.document_folder_company_doc').id
        collateral_folder = self.env.ref('smart_loan_system.document_folder_collaterals').id
        loan_docu_folder = self.env.ref('smart_loan_system.documents_loan').id

        models = ['kyc.retail', 'kyc.corporate', 'kyc.groups']
        res_models = [mod.get('res_model') for mod in vals_list]
        folders = [fold.get('folder_id') for fold in vals_list]
        check_model = False

        # Process the document upload and archive the previous versions
        if not all(non is None for non in res_models):
            for model, folder in zip(models, folders):
                if model in res_models and folder in [folder_id, folder_passport, folder_driving, folder_kvk, folder_artical, folder_share_reg]:
                    check_model = True
            if len(vals_list) > 1 and check_model:
                vals_list.clear()
            else:
                for vals in vals_list:
                    if vals.get('res_model') in ['account.loan', 'loan.collateral']:
                        check_model = True
                        current_model = False
                        partner_id = False
                        if vals.get('partner_id'):
                            partner_id = self.env['res.partner'].search([('id', '=', vals.get('partner_id'))])
                        elif vals.get('res_model') and vals.get('res_id'):
                            current_model = self.env[vals.get('res_model')].search(
                                [('id', '=', int(vals.get('res_id')))])
                            if vals.get('res_model') == 'account.loan':
                                partner_id = current_model.partner_id
                            elif vals.get('res_model') == 'loan.collateral':
                                partner_id = current_model.customer_id
                            else:
                                partner_id = False
                        else:
                            partner_id = False

                        # if vals.get('res_model') == 'account.loan' and current_model:
                        #     if current_model.type == 'laf' and current_model.laf_state == 'pre_draft' and not self.env.user.has_group('smart_loan_system.group_loan_account_officer') or not self.env.user.has_group('studio_customization.loans_app_account_of_64b8400d-59df-41d5-a2ae-0f4b12c9efe6'):
                        #         raise AccessError(
                        #             "You do not have the necessary permissions to create documents for loans")
                        #     elif current_model.type == 'laf' and current_model.laf_state == 'review_edit' and not self.env.user.has_group('smart_loan_system.group_loan_cao'):
                        #         raise AccessError(
                        #             "You do not have the necessary permissions to create documents for loans")
                        #     elif current_model.state == 'posted':
                        #         raise AccessError(
                        #             "You do not have the necessary permissions to create documents for loans")
                        #     elif current_model.state == 'draft'  and not self.env.user.has_group('smart_loan_system.group_loan_cao'):
                        #         raise AccessError(
                        #             "You do not have the necessary permissions to create documents for loans")


                        current_folder = self.env['documents.folder'].search([('id', '=', vals.get('folder_id'))])
                        parent_folder = False
                        parent_parent_folder = False
                        if current_folder and current_folder.parent_folder_id:
                            parent_folder = current_folder.parent_folder_id
                            if parent_folder and parent_folder.parent_folder_id:
                                parent_parent_folder = parent_folder.parent_folder_id
                        if any(folder.id in [collateral_folder, loan_docu_folder] for folder in
                               (current_folder, parent_folder, parent_parent_folder)):
                            file_name = vals.get('name').split('.')
                            if partner_id and current_folder and parent_folder:
                                file_name[
                                    0] = parent_folder.name + "_" + current_folder.name + "_" + partner_id.name + "."
                                vals.update({'name': "".join(file_name)})

                            # Archive any existing active documents for the same record and folder
                            existing_documents = self.env['documents.document'].search([
                                ('res_id', '=', vals.get('res_id')),
                                ('res_model', '=', vals.get('res_model')),
                                ('folder_id', '=', vals.get('folder_id')),
                                ('active', '=', True),
                            ])
                            if current_folder.name != 'Other' and existing_documents:
                                existing_documents.write({'active': False})

                    # Handle other folders for document naming
                    elif vals.get('folder_id') not in [folder_others, folder_company_doc]:
                        partner_id = self.env['res.partner'].browse(vals.get('partner_id'))
                        file_name = vals.get('name').split('.')
                        doc_folder = self.env['documents.folder'].browse(vals.get('folder_id'))
                        folder_display_name = doc_folder.name  # Use the folder's display name
                        if partner_id and doc_folder:
                            file_name[0] = f"{folder_display_name}_{partner_id.name}."
                            vals.update({'name': "".join(file_name)})
                        elif not partner_id and vals.get('res_model') in res_models:
                            group_obj = self.env['kyc.groups'].search([('id', '=', (vals.get('res_id')))])
                            for_group_num = group_obj.name if group_obj.name else group_obj.standard_group_name
                            if for_group_num:
                                file_name[0] = f"{folder_display_name}_{for_group_num}."
                                vals.update({'name': "".join(file_name)})

        # Create new documents
        documents = super(Document, self).create(vals_list)
        if all(doc in models for doc in documents.mapped('res_model')):
            docs = self.env['documents.document']
            for rec in documents:
                fetch_record = self.env['kyc.retail'].browse(rec.res_id)
                
                # Set specific expiration dates based on folder type
                if rec.folder_id.id == folder_id:
                    if rec.res_model == 'kyc.retail':
                        rec.kyc_date = fetch_record.id_expiration
                elif rec.folder_id.id == folder_passport:
                    if rec.res_model == 'kyc.retail':
                        rec.kyc_date = fetch_record.pass_expiration
                elif rec.folder_id.id == folder_driving:
                    if rec.res_model == 'kyc.retail':
                        rec.kyc_date = fetch_record.driving_expiration
                
                # Archive any older active document records
                existing_documents = docs.search([
                    ('res_id', '=', rec.res_id),
                    ('folder_id', '=', rec.folder_id.id),
                    ('res_model', 'in', models),
                    ('id', '!=', rec.id),
                    ('active', '=', True),
                ])
                if rec.folder_id.name != 'Others' and existing_documents:
                    existing_documents.write({'active': False})

        return documents

    def write(self, vals):
        # Check if 'active' is being set to False and log it in the chatter
        if 'active' in vals and vals['active'] is False:
            for record in self:
                record.message_post(body=_("Document has been archived."))

        # Continue with the standard write operation
        return super(Document, self).write(vals)
