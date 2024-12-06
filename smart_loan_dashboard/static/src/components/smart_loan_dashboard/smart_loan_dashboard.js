/** @odoo-module */

import { useService } from '@web/core/utils/hooks';
import { registry } from '@web/core/registry';
import { KpiCard } from '@wt_financial_dashboard/components/kpi_card/kpi_card';
import { Component, useState, onWillStart, useEffect, onMounted, useSubEnv } from "@odoo/owl";
var session = require('web.session');

export class smart_loan_dashboard extends Component {
    setup() {
        this.state = useState({
            period: 0,
            totalPortfolio: {
                    name: 'Total Portfolio Amount',
                    value: 0,
                    percentage:0,
                    total: 0
             },
            bonPortfolio: {
                    name: 'Bon Portfolio Amount',
                    value: 0,
                    percentage: 0,
                    total: 0
            }
        });
        this.actionService = useService('action');
        this.orm = useService('orm');

        onWillStart(async () => {
            await Promise.all([
                this.totalAmountPortfolio(),
            ])
        })
    }

    async totalAmountPortfolio() {
        debugger
        let domain = [];
        try {
            let count_loan = await this.env.services.orm.searchCount('account.loan', []);
            let total_amount = await this.env.services.orm.readGroup("account.loan", domain, ["loan_amount:sum"], []);
            this.state.totalPortfolio.value = count_loan;
            this.state.totalPortfolio.total = total_amount[0].loan_amount;
        } catch (error) {
            console.log(error);
        }
    }

    viewInvoice() {
        debugger
        let domain = [['move_type', '=', 'out_invoice']]
        if (this.state.period > 0) {
            domain.push(['invoice_date', '>', this.state.current_date]);
        }
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "Invoice",
            res_model: "account.move",
            domain,
            context: {},
            views: [
                [false, "list"],
                [false, "form"],
            ],
        });
    }
}

smart_loan_dashboard.template = "smart_loan_dashboard.smart_loan_dashboard";
smart_loan_dashboard.components = { KpiCard };
registry.category("actions").add("smart_loan_dashboard", smart_loan_dashboard);