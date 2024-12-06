/** @odoo-module **/

import { registry } from '@web/core/registry';
import { Component, onWillStart, useEffect, onMounted,useRef, useState } from "@odoo/owl";

const type_line_chart = {
    'amount_per_loan_classification_per_ao': 'Amount Per Loan Classification Per AO',
    'quantities_per_loan_classification_per_ao': 'Quantities Per Loan Classification Per AO',
    'amount_per_jurisdiction_per_loan_classification':'Amount Per Jurisdiction Per Loan classification',
    'quantities_per_jurisdiction_per_loan_classification': 'Quantities Per Jurisdiction Per Loan Classification',
    'amounts_per_division_per_loan_classification': 'Amounts Per Division Per Loan Classification',
    'quantities_per_division_per_loan_classification': 'Quantities Per division Per Loan classification',
    'restructured_loans_amounts_per_loan_classification_since': 'Restructured Loans Amounts Per Loan classification',
    'cumulative_restructured_loans_per_loan_classification_per_ao_since': 'Cumulative Restructured Loans Per Loan Classification Per AO'
}

export class LineChartView extends Component {
    setup() {
        this.line_chart_ref = useRef("line_chart_ref")
         onMounted(() => {
            this.line_chart()
        });
        this.state = useState({
            rotation: 0
        });
    }

    line_chart(){

      let lineChart = echarts.init(this.line_chart_ref.el);

      let option = {
          legend: {},
          tooltip: {},
          dataset: {
            dimensions: ['product', 'statisfactory', 'substandard', 'special mention', 'Doubtful', 'Loss'],
            source: this.getDataToRender(this.props.type),
//            [
//              { product: '012 Gaddiel', statisfactory: 43.3, substandard: 85.8, 'special mention': 93.7 },
//            ]
          },
          xAxis: { type: 'category', axisLabel:{rotate: this.state.rotation}

          },
          yAxis: {},

          series: [
          { type: 'bar', label:{show:true, position:'top'} },
          { type: 'bar',  label:{show:true, position:'top'}},
          { type: 'bar',  label:{show:true, position:'top'}},
          { type: 'bar',  label:{show:true, position:'top'}},
          { type: 'bar',  label:{show:true, position:'top'}},

          ],

          axisPointer:{
            label:{
              color: '#FF5733',
            }
          }

        };


    lineChart.setOption(option);

    }


    getName(type_key){
        return type_line_chart[type_key]
    }

     getDataToRender(type_pie_chart_name){
        const lineData = this.props.dataToRender
        switch (type_pie_chart_name){
            case type_pie_chart_name = 'amount_per_loan_classification_per_ao':
                    return this.getAmountArray(lineData.data_amounts_per_loan_classification_per_ao)


            case type_pie_chart_name = 'quantities_per_loan_classification_per_ao':
                    return this.getQuantityArray(lineData.data_amounts_per_loan_classification_per_ao)


            case type_pie_chart_name = 'amount_per_jurisdiction_per_loan_classification':
                return this.getAmountArray(lineData.amounts_per_jurisdiction_per_loan_classification)


            case type_pie_chart_name = 'quantities_per_jurisdiction_per_loan_classification':
                return this.getQuantityArray(lineData.amounts_per_jurisdiction_per_loan_classification)


            case type_pie_chart_name = 'amounts_per_division_per_loan_classification':
                return  this.getAmountArray(lineData.amounts_per_division_per_loan_classification)


            case type_pie_chart_name = 'quantities_per_division_per_loan_classification':
                return  this.getQuantityArray(lineData.amounts_per_division_per_loan_classification)


            case type_pie_chart_name = 'restructured_loans_amounts_per_loan_classification_since':
                return  this.getAmountArray(lineData.restructured_loan_amounts_per_loan_classification)


            case type_pie_chart_name = 'cumulative_restructured_loans_per_loan_classification_per_ao_since':
                return this.getAmountArray(lineData.cumulative_restructured_loans_per_loan_classification)

        }


    }

    getAmountArray(objectAmount){
        const data = []
        for (const [key, value] of Object.entries(objectAmount)) {
                  data.push({
                     product: key,
                    'statisfactory': value.satisfactory_amount,
                    'substandard': value.substandard_amount,
                    'special mention': value.special_mention_amount,
                    'Doubtful': value.doubtful_amount,
                    'Loss': value.loss_amount
                  })
                }
        if (data.length > 5){
            this.state.rotation = 32
        }
        return data
    }

    getQuantityArray(objectQuantity){
        const data = []
        for (const [key, value] of Object.entries(objectQuantity)) {
                  data.push({
                     product: key,
                    'statisfactory': value.satisfactory_quantity,
                    'substandard': value.substandard_quantity,
                    'special mention': value.special_mention_quantity,
                    'Doubtful': value.doubtful_quantity,
                    'Loss': value.loss_quantity
                  })
                }
        if (data.length > 5){
            this.state.rotation = 32
        }
        return data
    }

}
LineChartView.props = {
    type: String,
    dataToRender: { type: Object },
};
LineChartView.template = 'loan_dashboard.line_chart_template';

registry.category("views").add("line_chart_view", LineChartView);