/** @odoo-module **/

import * as docs from "@documents/views/hooks";
import { patch } from "@web/core/utils/patch";
import { useBus, useService } from "@web/core/utils/hooks";
import { DocumentsSpreadsheetControllerMixin } from "@documents_spreadsheet/documents_view/documents_spreadsheet_controller_mixin";
debugger

patch(DocumentsSpreadsheetControllerMixin, "smart_loan_system", {

   async onClickOpenWizardsDocs() {
        debugger
        return this.action.doAction("smart_loan_system.documents_name_wizard_action", {
                additionalContext: {
                    default_partner_id: this.props.context.default_partner_id || false,
                    default_folder_id: this.env.searchModel.getSelectedFolderId(),
                    default_res_id: this.props.context.default_res_id || false,
                    default_res_model: this.props.context.default_res_model || false,
                },
        });
    },

});

