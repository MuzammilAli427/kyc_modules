/** @odoo-module **/
import { LineChartView } from './line_chart';
import { PieChartView } from './pie_chart';
import { TileChartView } from './tile_view';
import { registry } from '@web/core/registry';
import { useService } from "@web/core/utils/hooks";
const { Component, onWillStart, useState } = owl;

export class LoanDashboardView extends Component {
    setup() {
         this.state = useState({
            tileData: {},
            pieData: {},
            lineData: {},
        });
        const params = {
            csrf_token: odoo.csrf_token,
        };
        this.http = useService("http");
        this.user = useService("user");
        this.companyService = useService("company");
        debugger;
        onWillStart(async ()=> {
             const dashBoardData = await this.http.post('/loandashboard', params, "json");
             this.state.tileData = dashBoardData.tile
             this.state.pieData = dashBoardData.pie
             this.state.lineData = dashBoardData.line
        })

    }


}


LoanDashboardView.template = 'loan_dashboard.loan_dashboard_template';
LoanDashboardView.components = {
    PieChartView,
    TileChartView,
    LineChartView,
};
registry.category("actions").add("loan_dashboard.loan_dashboard_view", LoanDashboardView);
