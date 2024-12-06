/** @odoo-module **/

import { registry } from '@web/core/registry';
const { Component, onWillStart, useState } = owl;

export class TileChartView extends Component {
    setup() {
        this.state = useState({
            data: this.props.dataToRender
        });


    }

    get_amount(key){
        return this.state.data[key].toLocaleString();
    }
}
TileChartView.props = {
      dataToRender: { type: Object },
};
TileChartView.template = 'loan_dashboard.tile_chart_template';

registry.category("views").add("tile_chart_view", TileChartView);