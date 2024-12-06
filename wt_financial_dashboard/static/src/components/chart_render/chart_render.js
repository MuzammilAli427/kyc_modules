/** @odoo-module */
import { Component, useState, useRef, onMounted, onWillStart, onWillUnmount, useEffect } from "@odoo/owl";
import { useService } from '@web/core/utils/hooks';
import { loadJS } from '@web/core/assets';
import { getColor } from "@web/views/graph/colors";
import { browser } from '@web/core/browser/browser';
import { routeToUrl } from "@web/core/browser/router_service";
var session = require('web.session');

export class ChartRender extends Component {
    setup() {
        this.state = useState({
            chartType:'bar',
            selectValue: '',
        })
        this.chartRef = useRef("wt_chart");

        const router = useService("router");
        const old_chartjs = document.querySelector('script[src="/web/static/lib/Chart/Chart.js"]');

        if(old_chartjs){
            old_chartjs.remove();
            let {search , hash} = router.current;
            search.wt = old_chartjs != null ? "0" : "1";
            hash.action =  this.env.config.actionId;
            browser.location.href = browser.location.origin + routeToUrl(router.current);
        }

        onWillStart(async () => {
            await loadJS("https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.0/chart.umd.min.js");
        });

        useEffect(() => {
                this.renderChart();
        }, () => [this.props.monthlyData,...this.state.chartType,])

        onMounted(() => {
            this.renderChart();
        }
        );
        onWillUnmount(() => {
            if (this.chart) {
                this.chart.destroy()
            }
        })
    }

        // Setting The Graph Type View
        getGraphType(state,type){
            state.chartType = type;
        }

    renderChart() {
        const old_chartjs = document.querySelector('script[src="/web/static/lib/Chart/Chart.js"]');
        if(old_chartjs){
            old_chartjs.remove();
            return
        }
        const configDataSet = this.props.compData;
        const dateConfig = this.props.dateConfig;
        const expenseLabel = this.props.expenseLabel;
        const datasets = [];

        // Adjusting datasets as Chart Wise 
        if(this.state.chartType === 'line' || this.state.chartType  === 'bar'){
            
            //Expense data 
            if(dateConfig.length >1){
                const colorMapping = {};
                let temp_i = 0;
                expenseLabel.forEach((index)=>{
                    colorMapping[index] = getColor(temp_i);
                    temp_i += 1;
                })
               for(let expenlabel of expenseLabel){
                let temp_list = [];
                for(let i=0 ; i<dateConfig.length; i++){
                    dateConfig[i].count[expenlabel];
                    if(!dateConfig[i].count[expenlabel]){
                        temp_list.push(0);
                    }else{
                        temp_list.push(dateConfig[i].count[expenlabel]);
                    }
                }
                // Adding base color in bar graph because of bydefault light color 
                if(this.state.chartType === 'line'){
                    datasets.push({
                        label: expenlabel,
                        data: temp_list,
                        hoverOffset:10,
                    })
                }else{
                    datasets.push({
                        label: expenlabel,
                        data: temp_list,
                        hoverOffset:10,
                        backgroundColor: colorMapping[expenlabel]
                    })
                }
               }
                
            }else{
                // ConfigDateset is for Comparison Data is for Comparison Data
                if(configDataSet.length > 1){
                    const colorMapping = {};
                    configDataSet[0].col_count.forEach((col, index) => {
                        let label = configDataSet[0].col_count[index].month;
                        colorMapping[label] = getColor(index);
                    });
        
                    for(let i= 0; i< configDataSet[0].col_count.length; i++){
                        // Adding Dark Color in bar
                        if(this.state.chartType === 'bar'){
                            datasets.push({
                                // label: configDataSet.map(item => item.line_label),
                                data:configDataSet.map(item => item.col_count[i].count),
                                label: configDataSet.map(item => item.col_count[i].month).filter((month, index, array) => array.indexOf(month) === index),
                                hoverOffset: 10,
                                backgroundColor: colorMapping[configDataSet.map(item => item.col_count[i].month).filter((month, index, array) => array.indexOf(month) === index)],
                            })
                        }else{
                            // Adjust Line Graph background color as it is
                            datasets.push({
                                // label: configDataSet.map(item => item.line_label),
                                data:configDataSet.map(item => item.col_count[i].count),
                                label: configDataSet.map(item => item.col_count[i].month).filter((month, index, array) => array.indexOf(month) === index),
                                hoverOffset: 10,
                            })
                        }
                    }
                }else{
                    // Else We will Push single Data line
                        datasets.push({
                            label: this.props.label,
                            data: this.props.monthlyData.map(item => item.count),
                            hoverOffset: 10,
                            backgroundColor: this.props.monthlyData.map((_, index) => getColor(index)),
                        })
                    
                }
            }
        }else{
            // This else Condition is for other graph
            if(dateConfig.length >1){
                 for(let expenlabel of expenseLabel){
                let temp_list = [];
                for(let i=0 ; i<dateConfig.length; i++){
                    dateConfig[i].count[expenlabel];
                    if(!dateConfig[i].count[expenlabel]){
                        temp_list.push(0);
                    }else{
                        temp_list.push(dateConfig[i].count[expenlabel]);
                    }
                }
                datasets.push({
                    label: expenlabel,
                    data: temp_list,
                    hoverOffset:10, 
                })
               }
            }else{
                if(configDataSet.length > 1){
                    for(let i= 0; i< configDataSet[0].col_count.length; i++){
                        datasets.push({
                            // label: configDataSet.map(item => item.line_label),
                            data:configDataSet.map(item => item.col_count[i].count),
                            label: configDataSet.map(item => item.col_count[i].month).filter((month, index, array) => array.indexOf(month) === index),
                            hoverOffset: 10,
                            backgroundColor: this.props.monthlyData.map((_, index) => getColor(index)),
                        })
                    }
                }else{
                    datasets.push({
                        label: this.props.label,
                        data: this.props.monthlyData.map(item => item.count),
                        hoverOffset: 10,
                        backgroundColor: this.props.monthlyData.map((_, index) => getColor(index)),
                    })
                }
            }
        }

        if (this.chart) {
            this.chart.destroy()
        } 
        if(this.state.chartType === 'line' || this.state.chartType  === 'bar'){

            this.chart =  new Chart(
                      this.chartRef.el,
                      {
                          type: this.state.chartType,
                          data: {
                              labels: this.props.monthlyData.map(item => item.month.length < 20 ? item.month: item.month.substring(0,20) + ".."),
                              datasets:datasets,
                          },
                          options: {
                              responsive: true,
                              maintainAspectRatio: false,
                              scales: {
                                  x: {
                                   stacked: true
                                 },
                                 y: {
                                   stacked: true
                                 }
                               },
                              transitions: {
                                  show: {
                                      animations: {
                                          x: {
                                              from: 0
                                          },
                                          y: {
                                              from: 0
                                          }
                                      },
                                      tension:1,
                                  },
                                  hide: {
                                      animations: {
                                          x: {
                                              to: 0
                                          },
                                          y: {
                                              to: 0
                                          },
                                          tension:1,
                                      }
                                  }
                              },
                              plugins: {
                                  legend: {
                                      isplay: true,
                                      position: 'bottom',
                                  },
                                  title: {
                                      display: true,
                                      position: 'bottom',
                                  },
                              }
                          }
                      }
                  )
        }else{
            this.chart =  new Chart(
                this.chartRef.el,
                {
                    type: this.state.chartType,
                    data: {
                        labels: this.props.monthlyData.map(item => item.month),
                        datasets:datasets,
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        transitions: {
                            show: {
                                animations: {
                                    x: {
                                        from: 0
                                    },
                                    y: {
                                        from: 0
                                    }
                                },
                                tension:1,
                            },
                            hide: {
                                animations: {
                                    x: {
                                        to: 0
                                    },
                                    y: {
                                        to: 0
                                    },
                                    tension:1,
                                }
                            }
                        },
                        plugins: {
                            legend: {
                                isplay: true,
                                position: 'bottom',
                            },
                            title: {
                                display: true,
                                position: 'bottom',
                            },
                        }
                    }
                }
            )
        }
    }
}

ChartRender.template = "warlock_financial_dashboard_financial_dashboard.wt_chart_component";