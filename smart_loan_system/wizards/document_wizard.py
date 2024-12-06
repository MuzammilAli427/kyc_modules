from odoo import fields, models, api
from odoo.exceptions import ValidationError


class DocumentAttachments(models.TransientModel):
    _name = 'docs.attach'
    _description = 'Docs Attach'

    attach_docs = fields.Many2one('document.wizards')
    filename = fields.Char('File Name')
    binary_field = fields.Binary('Upload Documents', attachment=True)
    is_readonly_docs = fields.Boolean()

    @api.onchange('binary_field')
    def name_of_upload_documents(self):
        for rec in self:
            if rec.binary_field:
                rec.is_readonly_docs = True


class DocumentWizardsExt(models.TransientModel):
    _name = 'document.wizards'
    _description = 'Document Wizards'

    document_name_others = fields.Char('Document Name')
    attachment_ids = fields.Many2many('ir.attachment', string='Attachments')
    partner_id = fields.Many2one('res.partner')
    folder_id = fields.Many2one('documents.folder')
    res_model = fields.Char('Resource Model')
    res_id = fields.Integer('Resource ID')
    docs_attach_ids = fields.One2many('docs.attach', 'attach_docs')

    def doc_delete_without_name(self):
        for rec in self.docs_attach_ids:
            if self.document_name_others:
                origin = self.res_model
                origin_docu = self.env[origin]
                if origin and self.res_id:
                    origin_docu = origin_docu.search([('id', '=', self.res_id)])
                attach_id = self.env['ir.attachment'].create({
                    'name': self.document_name_others + '_' + origin_docu.name if self.res_model == 'kyc.groups' and origin_docu else (self.document_name_others + '_' + self.partner_id.name if self.partner_id else self.document_name_others),
                    'type': 'binary',
                    'datas': rec.binary_field,
                    'store_fname': self.document_name_others,
                    'res_model': self.res_model,
                    'res_id': self.res_id
                })
                self.env['documents.document'].create({
                    'name': self.document_name_others + '_' + origin_docu.name if self.res_model == 'kyc.groups' and origin_docu else (self.document_name_others + '_' + self.partner_id.name if self.partner_id else self.document_name_others),
                    'attachment_id': attach_id.id,
                    'folder_id': self.folder_id.id,
                    'partner_id': self.partner_id.id if self.partner_id else False,
                })
            else:
                raise ValidationError("You need to must add a name of the document before uploading")
        if not self.docs_attach_ids and not self.document_name_others:
            raise ValidationError("You need to must add a name of the document and upload a files in lines")
        elif not self.docs_attach_ids and self.document_name_others:
            raise ValidationError("You need to must upload a files in lines")

        if self.document_name_others and self.docs_attach_ids:
            return {'type': 'ir.actions.client', 'tag': 'reload'}
