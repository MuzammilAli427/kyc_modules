/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import {
    inspectorFields,
    DocumentsInspector,
} from "@documents/views/inspector/documents_inspector";

debugger
inspectorFields.push("kyc_date", "action_by_date")
debugger
//patch(DocumentsInspector.prototype, "smart_loan_system", {
//    /**
//     * @override
//     */
//    setup() {
//        debugger
//        this._super(...arguments);
//    }
//
//    });