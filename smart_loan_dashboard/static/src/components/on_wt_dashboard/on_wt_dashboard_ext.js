/** @odoo-module */

import { useService } from '@web/core/utils/hooks';
import { registry } from '@web/core/registry';
import { KpiCard } from '@wt_financial_dashboard/components/kpi_card/kpi_card';
import { on_wt_dashboard } from '@wt_financial_dashboard/components/wt_dashboard';
import { Component, useState, onWillStart } from "@odoo/owl";
import { patch } from "@web/core/utils/patch";

debugger
patch(on_wt_dashboard.prototype, 'smart_loan_dashboard', {
    setup() {
        debugger
        this._super.apply(this, arguments);
        // Bind other view functions
    },
});