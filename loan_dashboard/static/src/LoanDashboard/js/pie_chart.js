/** @odoo-module **/

import { registry } from '@web/core/registry';
import { Component, onWillStart, useEffect, onMounted,useRef } from "@odoo/owl";


const type_pie_chart = {
    'amount_share_by_division': 'Amount Share by Division',
    'amount_share_by_jurisdiction': 'Amount Share by Jurisdiction',
    'amount_share_by_loan_classification': 'Amount Share by Loan Classification',
    'amount_share_by_loan_product': 'Amount Share by loan Product',
    'quantity_share_by_division': 'Quantity Share by Division',
    'quantity_share_by_jurisdiction': 'Quantity Share by Jurisdiction',
    'quantity_share_by_loan_classification': 'Quantity Share by Loan Classification',
    'quantity_share_by_loan_product': 'Quantity Share by Loan Product'
}
const StandardValueAttributesPie = {
    label: {formatter:'{d}%'}
}

export class PieChartView extends Component {
    setup() {
        this.pie_chart_ref = useRef('pie_chart_ref')
        onWillStart( () => {
        });
        onMounted(() => {
            this.load_pie_chart()
        });
    }

    load_pie_chart(){

      let myChart = echarts.init(this.pie_chart_ref.el);

      let option = {
      title: {
        text: this.getName(this.props.type),
        left: 'center',
            textStyle:{
              fontSize:12,
            }
      },
      tooltip: {
        trigger: 'item'
      },
      legend: {
        orient: 'horizontal',
        bottom: 'left',

      },
      series: [
        {
          name: 'Access From',
          type: 'pie',
          radius: '50%',
          data: this.getDataToRender(this.props.type),
//          [
//            { value: 10, name: 'Search Engine', label: {formatter:'{d}%'} },
//            { value: 15, name: 'Direct', label: {formatter:'{d}%'} },
//            { value: 25, name: 'Email', label: {formatter:'{d}%'} },
//            { value: 45, name: 'Union Ads', label: {formatter:'{d}%'} },
//            { value: 5, name: 'Video Ads', label: {formatter:'{d}%'} }
//          ],
          emphasis: {
            itemStyle: {
              shadowBlur: 10,
              shadowOffsetX: 0,
              shadowColor: 'rgba(0, 0, 0, 0.5)'
            }
          }
        }
      ]
    };

    myChart.setOption(option);

    }

    getName(type_key){
        return type_pie_chart[type_key]
    }

    getAmountShareByDivision_pie(){
            const pieData = this.props.pieData
            return [{
                    value: pieData.retail_portfolio_amount,
                    name: "Retail",
                    ...StandardValueAttributesPie
                    },{
                    value: pieData.corporate_portfolio_amount,
                    name: "Corporate",
                    ...StandardValueAttributesPie
                    }
                ]
    }

    getDataToRender(type_pie_chart_name){
        const pieData = this.props.dataToRender
        switch (type_pie_chart_name){
            case type_pie_chart_name = 'amount_share_by_division':

                        return [{
                        value: pieData.retail_portfolio_amount,
                        name: "Retail",
                        ...StandardValueAttributesPie
                        },{
                        value: pieData.corporate_portfolio_amount,
                        name: "Corporate",
                        ...StandardValueAttributesPie
                        }
                    ]

            case type_pie_chart_name = 'amount_share_by_jurisdiction':

                    return [{
                        value: pieData.bon_portfolio_amount,
                        name: "Bonaire",
                        ...StandardValueAttributesPie
                        },{
                        value: pieData.cur_portfolio_amount,
                        name: "Curaçao",
                        ...StandardValueAttributesPie
                        }
                    ]

            case type_pie_chart_name = 'amount_share_by_loan_classification':

                    return [{
                        value: pieData.satisfactory_amount,
                        name: "Satisfactory",
                        ...StandardValueAttributesPie
                        },{
                        value: pieData.substandard_amount,
                        name: "Substandard",
                        ...StandardValueAttributesPie
                        },{
                        value: pieData.special_mention_amount,
                        name: "Special Mention",
                        ...StandardValueAttributesPie
                        },{
                        value: pieData.doubtful_amount,
                        name: "Doubtful",
                        ...StandardValueAttributesPie
                        },{
                        value: pieData.loss_amount,
                        name: "Loss",
                        ...StandardValueAttributesPie
                        },
                    ]

            case type_pie_chart_name = 'amount_share_by_loan_product':

                    return [{
                        value: pieData.write_off_amount,
                        name: "Write Off",
                        ...StandardValueAttributesPie
                        }
                    ]

            case type_pie_chart_name = 'quantity_share_by_division':

                    return  [{
                        value: pieData.corporate_portfolio_number_of_loans,
                        name: "Corporate # Loans",
                        ...StandardValueAttributesPie
                        },{
                        value: pieData.retail_number_of_loans,
                        name: "Retail # Loans",
                        ...StandardValueAttributesPie
                        }
                    ]

            case type_pie_chart_name = 'quantity_share_by_jurisdiction':

                    return  [{
                        value: pieData.bon_portfolio_number_of_loans,
                        name: "Bonaire # Loans",
                        ...StandardValueAttributesPie
                        },{
                        value: pieData.cur_portfolio_number_of_loans,
                        name: "Curaçao # Loans",
                        ...StandardValueAttributesPie
                        }
                    ]

            case type_pie_chart_name = 'quantity_share_by_loan_classification':

                    return  [{
                        value: pieData.satisfactory_number_of_loans,
                        name: "Satisfactory",
                        ...StandardValueAttributesPie
                        },{
                        value: pieData.substandard_number_of_loans,
                        name: "Substandard",
                        ...StandardValueAttributesPie
                        },{
                        value: pieData.special_mention_number_of_loans,
                        name: "Special Mention",
                        ...StandardValueAttributesPie
                        },{
                        value: pieData.doubtful_number_of_loans,
                        name: "Doubtful",
                        ...StandardValueAttributesPie
                        },{
                        value: pieData.loss_number_of_loans,
                        name: "Loss",
                        ...StandardValueAttributesPie
                        },
                    ]

            case type_pie_chart_name = 'quantity_share_by_loan_product':
                return  [{
                        value: pieData.write_off_number_of_loans,
                        name: "Write Off # Loans",
                        ...StandardValueAttributesPie
                        }
                    ]

        }


    }
}
PieChartView.props = {
    type: String,
    dataToRender: { type: Object },
};
PieChartView.template = 'loan_dashboard.pie_chart_template';
