/** @odoo-module */

import { useService } from '@web/core/utils/hooks';
import { registry } from '@web/core/registry';
import { Component, useState, onWillStart, useEffect, onMounted, useSubEnv } from "@odoo/owl";
import { KpiCard } from './kpi_card/kpi_card';
import { Chartfiter } from './filter_row/filter';
import { ChartRender } from './chart_render/chart_render';
import { DashBoardTable } from './table_component/table';
var session = require('web.session');

export class on_wt_dashboard extends Component {
    setup() {
        this.state = useState({
            invoice: {
                value: 10,
                percentage: 0.00,
                invoiceTotal: 0
            },
            paidInvoice: {
                value: 10,
                percentage: 0.00,
                PaymentTotal: 0
            },
            wtbill: {
                billCount: 0,
                billTotal: 0,
                BillPerCent: 0.00,
            },
            wtCredit: {
                CreditCount: 0,
                CreditPercent: 0.00,
                totalCredit: 0,
            },
            wtDebit: {
                DebitCount: 0,
                DebitPercent: 0.00,
                totalDebit: 0
            },
            period: 0,
            toggleOpen: false,
            isSidebarActive: false,
            activeItem: localStorage.getItem('item') ? localStorage.getItem('item') : 'item1',
            monthlyData: [],
            chartLabel: 'Label',
            reportAction: '',
            dSelect: true,
            selectOption: [],
            accountChild: '',
            accountConfig: [],
            activeTable: false,
            table_config: [],
            expenseConfig: [],
            modelState: "",
            fields:[],
            tableChildData:false,
            tableHead:[],
            expenseLabels: new Set(), //I am Adding ExpenseLabels for the seaching Label wise Data
            tableLabel:'',
            dateDomain:[],
            wtDropdown: {
                IsDateFilter: true,
                IsAccountFilter: false,
                IsPartnerFilter: false,
                jouranalItems: false,
                comparisonState: false,
                start_date: '',
                end_date: '',

                wtDateFilter: 'this_year',
                dropDownLabel: 'This Year',

                wtAccountFilter: ['trade_receivable', 'trade_payable'],
                dropDownAccountLabel: 'Account',
                wtPartnerFilter: [],
                wtPartnerTagFilter: [],
                wtPartnerFilterOption: true,
                wtJouranlItemId: [{
                    'journals': [],
                    'journal_group_id': [],
                }],
                journalOption: '',
                journalLabels: [],
                wtComparison: 'no_comparison',
                wtComparisonLabel: '',
                comparePeriod: 1,
                comparisonFrom: '',
                comparisonTo: '',
                groupBy: false,
                groupState:sessionStorage.getItem('group_id')? sessionStorage.getItem('group_id'):'employee_id',
                groupDate: '',
                dateState: '',
                groupByRevenue: false,
                groupStateRevenue: 'user_id',
                groupDate1: '',
                dateState1: '',
                customDate:false,
                dateSelect: false
            }
        });

        // Using This useService hook we can fetch the data from model
        this.actionService = useService('action');
        this.orm = useService('orm');
        useEffect(() => {
            this.fetchDemoData();
        }, () => [
            ...this.state.activeItem,
            this.state.wtDropdown.wtDateFilter,
            this.state.wtDropdown.IsCustomFilter,
            ...this.state.wtDropdown.wtAccountFilter,
            ...this.state.wtDropdown.wtPartnerFilter,
            ...this.state.wtDropdown.wtPartnerTagFilter,
            this.state.wtDropdown.wtPartnerFilterOption,
            this.state.period
        ])

        onWillStart(async () => {
            this.getDate();
            await Promise.all([
                this.getInvoice(),
                this.getPaidInvoice(),
                this.BillDetails(),
                this.CreditNotes(),
                this.DebitNotes()
            ])
        })


    }

    async fetchChildData() {
        if (!this.state.accountChild) {
            this.state.reportAction = '';
        }
        await this.fetchDemoData();
    }

    // Adding Method for selecting Custom Date
   async CustomRevExp(){
        this.state.current_date = $('input[name="exrev_start_date"]').val();
        this.state.today = $('input[name="exrev_end_date"]').val();
        if(this.state.today === ''){
            this.state.today = moment().subtract(0, 'days').format('YYYY-MM-DD');
        }

        if(this.state.current_date === ''){
            this.state.current_date = moment().subtract(356,'days').format('YYYY-MM-DD');
        }
        this.state.wtDropdown.dateSelect = true;
        this.state.period = 0;
        if(this.state.wtDropdown.groupDate1 || this.state.wtDropdown.groupDate1){
            this.state.wtDropdown.groupDate1 = '';
            this.state.wtDropdown.groupDate1 = '';
        }
        this.state.wtDropdown.wtPartnerFilterOption = !this.state.wtDropdown.wtPartnerFilterOption;
        await Promise.all([
            this.getInvoice(),
            this.getPaidInvoice(),
            this.BillDetails(),
            this.CreditNotes(),
            this.DebitNotes()
        ])
    }

    async fetchDemoData() {
        let dataList = []; //This is my normal Flow
        let demoDataList = []; //This is for comparison Data OF balanceSheet
        let dateExpenseList = []; //I created separete list for expense because I need hr.expense data which is not available in account.repoprt
        var context = session.user_context;//Using Context We are passing base filter data state selcted by user

        // Conditions for date filter is custom or selected 
        context['date_filter'] = this.state.wtDropdown.wtDateFilter;
        if (this.state.wtDropdown.wtDateFilter === 'custom') {
            context['start_date'] = this.state.wtDropdown.start_date;
            context['end_date'] = this.state.wtDropdown.end_date;
        } else {
            this.state.wtDropdown.wtDateFilter === 'this_year';
        }
        // Conditions for the is filter journla_id_item or journals
        if (this.state.wtDropdown.journalOption === 'journal_group_id') {
            context['journal_group_id'] = this.state.wtDropdown.wtJouranlItemId[0]['journal_group_id'][0];
        } else {
            context['journal_ids'] = this.state.wtDropdown.wtJouranlItemId[0]['journals'];
        }
        // Conditions for the getting The Comparison Line in
        if (this.state.wtDropdown.wtComparison) {
            // I am analayzing data on it
            context['filter'] = this.state.wtDropdown.wtComparison;
            context['period'] = this.state.wtDropdown.comparePeriod;
            if (this.state.wtDropdown.comparisonFrom && this.state.wtDropdown.comparisonTo) {
                context['comp_date_from'] = this.state.wtDropdown.comparisonFrom;
                context['comp_date_end'] = this.state.wtDropdown.comparisonTo;
            }
        }
        context['account_filter'] = this.state.wtDropdown.wtAccountFilter;
        context['partner_filter'] = this.state.wtDropdown.wtPartnerFilter;
        context['partner_tag_filter'] = this.state.wtDropdown.wtPartnerTagFilter;
        if (this.state.activeItem === 'item1') {
            this.state.dSelect = true;
            context['report_id'] = 'account_reports.partner_ledger_report'
            let data = await this.env.services.orm.call('account.report', 'dashboard_get_report_informations', [""], {
                previous_options: context
            });
            for (let i = 0; i < data['lines'].length - 1; i++) {
                dataList.push({
                    month: data['lines'][i]['name'],
                    count: data['lines'][i]['columns'][8]['no_format'],
                })
            }
            this.state.reportAction = 'account_reports.action_account_report_partner_ledger';
            this.state.chartLabel = 'Partner Ledger';

            this.state.wtDropdown.IsAccountFilter = true;
            this.state.wtDropdown.IsPartnerFilter = true;
            this.state.wtDropdown.jouranalItems = false;
            this.state.wtDropdown.comparisonState = false;
            this.state.wtDropdown.IsDateFilter = true;
            this.state.wtDropdown.groupBy = false;
            this.state.activeTable = true;
            this.state.wtDropdown.groupByRevenue = false;
            this.state.wtDropdown.customDate = false;
        } else if (this.state.activeItem === 'item2') {
            this.state.dSelect = true;
            context['report_id'] = 'account_reports.profit_and_loss';
            let data = await this.env.services.orm.call('account.report', 'dashboard_get_report_informations', [""], {
                previous_options: context,
            })
            for (let i = 0; i < data['lines'].length; i++) {
                if (data.lines[i].columns.length > 1) {
                    let temp_object = [];
                    for (let j = 0; j < data.lines[i].columns.length; j++) {
                        //Extracting Date Label
                        const regex = /'string', '([^']+)'/;
                        let match = data.lines[i].columns[j].column_group_key.match(regex);
                        temp_object.push({
                            month: match[1],
                            count: data.lines[i].columns[j]['no_format'].toFixed(2)
                        });
                    }
                    demoDataList.push({
                        line_label: data['lines'][i]['name'],
                        col_count: temp_object,
                    });
                } else {
                    //Push here here a normal flow dataList if columns length is less than 
                }
                // ------------dataList is normal Flow Remeber it-----------//
                dataList.push({
                    month: data['lines'][i]['name'],
                    count: data['lines'][i]['columns'][0]['no_format'].toFixed(2)
                })
            }
            this.state.chartLabel = 'Profit & Loss';
            this.state.reportAction = 'account_reports.action_account_report_pl';

            this.state.wtDropdown.IsAccountFilter = false;
            this.state.wtDropdown.IsPartnerFilter = false;
            this.state.wtDropdown.jouranalItems = true;
            this.state.wtDropdown.comparisonState = true;
            this.state.wtDropdown.IsDateFilter = true;
            this.state.wtDropdown.groupBy = false;
            this.state.activeTable = true;
            this.state.wtDropdown.groupByRevenue = false;
            this.state.wtDropdown.customDate = false;
        } else if (this.state.activeItem === 'item3') {
            context['report_id'] = 'account_reports.balance_sheet';
            let data = await this.env.services.orm.call('account.report', 'dashboard_get_report_informations', [""], {
                previous_options: context,
            })
            // data.options.comparison.periods[2] getting date periods
            if (this.state.reportAction === 'account_reports.action_account_report_bs' && this.state.accountChild) {
                for (let i = 0; i < data['lines'].length; i++) {
                    if ((data.lines[i].id.split("|")[0] === this.state.accountChild) && data['lines'][i]['columns'][0]['no_format']) {
                        if (data.lines[i].columns.length > 1) {
                            let temp_object = [];
                            for (let j = 0; j < data.lines[i].columns.length; j++) {
                                //Extracting Date Label
                                const regex = /'string', '([^']+)'/;
                                let match = data.lines[i].columns[j].column_group_key.match(regex);
                                temp_object.push({
                                    month: match[1],
                                    count: data.lines[i].columns[j]['no_format'].toFixed(2)
                                });
                            }
                            demoDataList.push({
                                line_label: data['lines'][i]['name'],
                                col_count: temp_object,
                            });
                        } else {
                            //Push here here a normal flow dataList if columns length is less than 
                        }
                        // ------------dataList is normal Flow Remeber it-----------//
                        dataList.push({
                            month: data['lines'][i]['name'],
                            count: data['lines'][i]['columns'][0]['no_format'].toFixed(2),
                        })
                    }
                }
            } else {
                let optionValue = [];
                for (let i = 0; i < data['lines'].length; i++) {
                    if (data.lines[i].id.split("|").length === 1) {
                        if (data.lines[i].columns.length > 1) {
                            let temp_object = [];
                            for (let j = 0; j < data.lines[i].columns.length; j++) {
                                //Extracting Date Label
                                const regex = /'string', '([^']+)'/;
                                let match = data.lines[i].columns[j].column_group_key.match(regex);
                                temp_object.push({
                                    month: match[1],
                                    count: data.lines[i].columns[j]['no_format'].toFixed(2)
                                });
                            }
                            demoDataList.push({
                                line_label: data['lines'][i]['name'],
                                col_count: temp_object,
                            });
                        } else {
                            //Push here here a normal flow dataList if columns length is less than 
                        }
                        // ------------dataList is normal Flow Remeber it-----------//
                        dataList.push({
                            month: data['lines'][i]['name'],
                            count: data['lines'][i]['columns'][0]['no_format'].toFixed(2),
                            id: data.lines[i].id
                        })
                    }
                    if (data.lines[i].id.split("|").length === 1) {
                        optionValue.push({
                            name: data['lines'][i]['name'],
                            id: data.lines[i].id
                        })
                    }
                }
                this.state.selectOption = optionValue;
            }
            this.state.chartLabel = 'Balance Sheet';
            this.state.wtDropdown.jouranalItems = true;
            this.state.reportAction = 'account_reports.action_account_report_bs';
            this.state.dSelect = false;
            this.state.wtDropdown.IsAccountFilter = false;
            this.state.wtDropdown.IsPartnerFilter = false;
            this.state.wtDropdown.comparisonState = true;
            this.state.wtDropdown.IsDateFilter = true;
            this.state.wtDropdown.groupBy = false;
            this.state.activeTable = true;
            this.state.wtDropdown.groupByRevenue = false;
            this.state.wtDropdown.customDate = false;
        } else if (this.state.activeItem === 'item4') {
            context['report_id'] = 'account_reports.executive_summary';
            let data = await this.env.services.orm.call('account.report', 'dashboard_get_report_informations', [""], {
                previous_options: context,
            })
            if (this.state.reportAction === 'account_reports.action_account_report_exec_summary' && this.state.accountChild) {
                for (let i = 0; i < data['lines'].length; i++) {
                    if ((data.lines[i].id.split("|")[0] === this.state.accountChild) && data['lines'][i]['columns'][0]['no_format']) {
                        if (data.lines[i].columns.length > 1) {
                            let temp_object = [];
                            for (let j = 0; j < data.lines[i].columns.length; j++) {
                                //Extracting Date Label
                                const regex = /'string', '([^']+)'/;
                                let match = data.lines[i].columns[j].column_group_key.match(regex);
                                temp_object.push({
                                    month: match[1],
                                    count: data.lines[i].columns[j]['no_format'].toFixed(2)
                                });
                            }
                            demoDataList.push({
                                line_label: data['lines'][i]['name'],
                                col_count: temp_object,
                            });
                        } else {
                            //Push here here a normal flow dataList if columns length is less than 
                        }
                        // ------------dataList is normal Flow Remeber it-----------//
                        dataList.push({
                            month: data['lines'][i]['name'],
                            count: data['lines'][i]['columns'][0]['no_format'].toFixed(2),
                        })
                    }
                }
            } else {
                let optionValue = [];
                for (let i = 0; i < data['lines'].length; i++) {
                    if ((data.lines[0].id.split("|")[0] === data.lines[i].id.split("|")[0]) && data['lines'][i]['columns'][0]['no_format']) {
                        if (data.lines[i].columns.length > 1) {
                            let temp_object = [];
                            for (let j = 0; j < data.lines[i].columns.length; j++) {
                                //Extracting Date Label
                                const regex = /'string', '([^']+)'/;
                                let match = data.lines[i].columns[j].column_group_key.match(regex);
                                temp_object.push({
                                    month: match[1],
                                    count: data.lines[i].columns[j]['no_format'].toFixed(2)
                                });
                            }
                            demoDataList.push({
                                line_label: data['lines'][i]['name'],
                                col_count: temp_object,
                            });
                        } else {
                            //Push here here a normal flow dataList if columns length is less than 
                        }
                        // ------------dataList is normal Flow Remeber it-----------//

                        dataList.push({
                            month: data['lines'][i]['name'],
                            count: data['lines'][i]['columns'][0]['no_format'].toFixed(2),
                        })
                    }
                    if (data.lines[i].id.split("|").length === 1) {
                        optionValue.push({
                            name: data['lines'][i]['name'],
                            id: data.lines[i].id
                        })
                    }
                }
                this.state.selectOption = optionValue;
            }
            this.state.chartLabel = 'Executive Summary';
            this.state.reportAction = 'account_reports.action_account_report_exec_summary';
            this.state.dSelect = false;


            this.state.wtDropdown.IsAccountFilter = false;
            this.state.wtDropdown.IsPartnerFilter = false;
            this.state.wtDropdown.comparisonState = true;
            this.state.wtDropdown.IsDateFilter = true;
            this.state.wtDropdown.groupBy = false;
            this.state.activeTable = true;
            this.state.wtDropdown.groupByRevenue = false;
            this.state.wtDropdown.customDate = false;
        } else if (this.state.activeItem === 'item5') {
            this.state.dSelect = true;
            context['report_id'] = 'account.generic_tax_report';
            let data = await this.env.services.orm.call('account.report', 'dashboard_get_report_informations', [""], {
                previous_options: context,
            })

            for (let i = 0; i < data['lines'].length; i++) {
                if (data['lines'][i]['columns'][0]['no_format']) {
                    if (Object.entries(data.column_groups_totals).length > 1) {
                        let temp_object = [];
                        for (let j = 0; j < Object.entries(data.column_groups_totals).length; j++) {
                            //Extracting Date Label
                            const regex = /'string', '([^']+)'/;
                            let match = Object.entries(data.column_groups_totals)[j][0].match(regex);
                            temp_object.push({
                                month: match[1],
                                count: data['lines'][i]['columns'][j]['no_format'].toFixed(2)
                            });
                        }
                        demoDataList.push({
                            line_label: data['lines'][i]['name'],
                            col_count: temp_object,
                        });
                    }
                    dataList.push({
                        month: data['lines'][i]['name'],
                        count: data['lines'][i]['columns'][0]['no_format'].toFixed(2),
                    })
                }
            }
            this.state.reportAction = 'account_reports.action_account_report_gt';
            this.state.chartLabel = 'Tax Report';

            this.state.wtDropdown.jouranalItems = false;
            this.state.wtDropdown.IsAccountFilter = false;
            this.state.wtDropdown.IsPartnerFilter = false;
            this.state.wtDropdown.comparisonState = true;
            this.state.wtDropdown.IsDateFilter = true;
            this.state.wtDropdown.groupBy = false;
            this.state.activeTable = true;
            this.state.wtDropdown.groupByRevenue = false;
            this.state.wtDropdown.customDate = false;
        } else if (this.state.activeItem === 'item6') {
            this.state.dSelect = true;
            context['report_id'] = 'account_reports.cash_flow_report';
            let data = await this.env.services.orm.call('account.report', 'dashboard_get_report_informations', [""], {
                previous_options: context,
            })
            for (let i = 0; i < data['lines'].length; i++) {
                if (data['lines'][i]['columns'][0]['no_format']) {
                    dataList.push({
                        month: data['lines'][i]['name'],
                        count: data['lines'][i]['columns'][0]['no_format'].toFixed(2),
                    })
                }
            }
            this.state.chartLabel = 'Cash Flow Statement';
            this.state.wtDropdown.jouranalItems = true;
            this.state.reportAction = 'account_reports.action_account_report_cs';


            this.state.wtDropdown.IsAccountFilter = false;
            this.state.wtDropdown.IsPartnerFilter = false;
            this.state.wtDropdown.comparisonState = false;
            this.state.wtDropdown.IsDateFilter = true;
            this.state.wtDropdown.groupBy = false;
            this.state.activeTable = true;
            this.state.wtDropdown.groupByRevenue = false;
            this.state.wtDropdown.customDate = false;
        } else if (this.state.activeItem === 'item7') {
            this.state.dSelect = true;
            this.state.tableChildData = false;
            this.state.tableLabel = "Employee";
            let label = ['Expense','Date','Employee','Total']
            this.state.tableHead = label;
            let domain = [];
            if(this.state.wtDropdown.dateState){
            }else if(this.state.wtDropdown.dateSelect){
                domain.push(['date', '>', this.state.current_date], ['date', '<', this.state.today]);
            }
            let table_fields = ['name','date','employee_id','total_amount_company'];
            this.state.fields = table_fields;
            if (this.state.wtDropdown.groupDate === 'Date') {
                let groupbyField = [`date:${this.state.wtDropdown.dateState}`];
                let fields = ['date', 'total_amount'];
                let result = await this.env.services.orm.readGroup("hr.expense", domain, fields, groupbyField);
                let stateLabel = new Set(); //Creating New Sets for Labels 
                for (let entry of result) {
                    if (this.state.wtDropdown.groupState) {
                        let desired_ids = await this.env.services.orm.search("hr.expense", [entry.__domain[1], entry.__domain[2]]);
                        let expense_data = await this.env.services.orm.read("hr.expense", desired_ids, [this.state.wtDropdown.groupState, 'date', 'total_amount', 'state']);
                        const labelSums = {};

                        if (this.state.wtDropdown.groupState === 'state') {
                            expense_data.forEach(item => {
                                const { state, total_amount } = item;
                                if (labelSums[state]) {
                                    labelSums[state] += total_amount;
                                } else {
                                    labelSums[state] = total_amount;
                                }
                                if (!stateLabel.has(state)) {
                                    stateLabel.add(state);
                                }
                            })
                        } else if (this.state.wtDropdown.groupState === 'employee_id') {
                            expense_data.forEach(item => {
                                const { employee_id, total_amount } = item;
                                const employee_label = employee_id[1];
                                if (labelSums[employee_label]) {
                                    labelSums[employee_label] += total_amount;
                                } else {
                                    labelSums[employee_label] = total_amount;
                                }
                                if (!stateLabel.has(employee_label)) {
                                    stateLabel.add(employee_label);
                                }
                            })
                        } else if (this.state.wtDropdown.groupState === 'product_id') {
                            expense_data.forEach(item => {
                                const { product_id, total_amount } = item;
                                const product_label = product_id[1];
                                if (labelSums[product_label]) {
                                    labelSums[product_label] += total_amount;
                                } else {
                                    labelSums[product_label] = total_amount;
                                }
                                if (!stateLabel.has(product_label)) {
                                    stateLabel.add(product_label);
                                }
                            })
                        }
                        dateExpenseList.push({
                            month: entry[groupbyField],
                            count: labelSums,
                        })
                    }
                    dataList.push({
                        month: entry[groupbyField],
                        count: entry.total_amount,
                        id:[entry.__domain[1],entry.__domain[2]]
                    })
                }
                this.state.expenseLabels = stateLabel;
            } else {
                let groupbyField = [this.state.wtDropdown.groupState];
                let fields = [this.state.wtDropdown.groupState, 'total_amount'];
                // Calulate the result as a  wise
                let result = await this.env.services.orm.readGroup("hr.expense", domain, fields, groupbyField);
                for (let entry of result) {
                    dataList.push({
                        month: entry[this.state.wtDropdown.groupState] ? (this.state.wtDropdown.groupState === 'state' ? entry[this.state.wtDropdown.groupState] : entry[this.state.wtDropdown.groupState][1]) : entry[this.state.wtDropdown.groupState][1],
                        count: entry.total_amount,
                        id:entry[this.state.wtDropdown.groupState] ? (this.state.wtDropdown.groupState === 'state' ? entry[this.state.wtDropdown.groupState] : entry[this.state.wtDropdown.groupState][0]) : entry[this.state.wtDropdown.groupState][0]
                    })
                }
            }
            // Assigning State for what filter will display or what data display on the secreen Remember it 
            // this.state.table_config = temp_array;
            this.state.activeTable = true
            this.state.chartLabel = 'Expenses'
            this.state.wtDropdown.jouranalItems = false;
            this.state.wtDropdown.IsAccountFilter = false;
            this.state.wtDropdown.IsPartnerFilter = false;
            this.state.wtDropdown.comparisonState = false;
            this.state.wtDropdown.IsDateFilter = false;
            this.state.wtDropdown.groupBy = true;
            this.state.modelState = "hr.expense"
            this.state.wtDropdown.groupByRevenue = false;
            this.state.wtDropdown.customDate = true;
        } else if (this.state.activeItem === 'item8') {
            this.state.dSelect = true;
            this.state.tableChildData = false;
            this.state.tableLabel = "Salesperson";
            let label = ['Sale Ref','Date','SalesPerson','Taxed','Untaxed']
            let table_fields = ['order_id','date','user_id','price_total','price_subtotal'];
            this.state.fields = table_fields;
            this.state.tableHead = label;

            let domain = [];
            if(this.state.wtDropdown.dateState1){
            }else if(this.state.wtDropdown.dateSelect){
                domain.push(['date', '>', this.state.current_date], ['date', '<', this.state.today]);
            }
            if (this.state.wtDropdown.groupDate1 === 'Group_Date') {
                let groupbyField = [`date:${this.state.wtDropdown.dateState1}`];
                let fields = ['date', 'price_subtotal'];
                // Calulate the result as a  wise
                let result = await this.env.services.orm.readGroup("sale.report", domain, fields, groupbyField);
                let stateLabel = new Set(); //Creating New Sets for Labels 
                for (let entry of result) {
                    if(this.state.wtDropdown.groupStateRevenue){
                        let desired_ids = await this.env.services.orm.search("sale.report", [entry.__domain[1], entry.__domain[2]]);
                        let expense_data = await this.env.services.orm.read("sale.report", desired_ids, [this.state.wtDropdown.groupStateRevenue, 'date', 'price_subtotal', 'state']);
                        const labelSums = {};

                        if (this.state.wtDropdown.groupStateRevenue === 'state') {
                            expense_data.forEach(item => { 
                                const { state, price_subtotal } = item;
                                if (labelSums[state]) {
                                    labelSums[state] += price_subtotal;
                                } else {
                                    labelSums[state] = price_subtotal;
                                    if (!stateLabel.has(state)) {
                                }
                                    stateLabel.add(state);
                                }
                            })
                        }else{
                           for(let i=0; i < expense_data.length; i++){
                            let my_label = expense_data[i][this.state.wtDropdown.groupStateRevenue][1];
                            let price_subtotal = expense_data[i]['price_subtotal'];
                            if (labelSums[my_label]) {
                                labelSums[my_label] += price_subtotal;
                            } else {
                                labelSums[my_label] = price_subtotal;
                            }
                            if (!stateLabel.has(my_label)) {
                                stateLabel.add(my_label);
                            }
                           }   
                        }
                        dateExpenseList.push({
                            month: entry[groupbyField],
                            count: labelSums,
                        })
                    }
                    dataList.push({
                        month: entry[groupbyField] ,
                        count: entry.price_subtotal,
                        id:[entry.__domain[1],entry.__domain[2]]
                    })
                    this.state.expenseLabels = stateLabel;
                }
            }else{

                // Displaying Graph Data
                let groupbyField = [this.state.wtDropdown.groupStateRevenue];
                let fields = [this.state.wtDropdown.groupStateRevenue, 'price_subtotal'];
                // Calulate the result as a  wise
                let result = await this.env.services.orm.readGroup("sale.report", domain, fields, groupbyField);
                for (let entry of result) {
                    if(entry[this.state.wtDropdown.groupStateRevenue] === false){
                        break;
                    }else{
                        dataList.push({
                            month: entry[this.state.wtDropdown.groupStateRevenue] ? (this.state.wtDropdown.groupStateRevenue === 'state' ? entry[this.state.wtDropdown.groupStateRevenue] : entry[this.state.wtDropdown.groupStateRevenue][1]) : entry[this.state.wtDropdown.groupStateRevenue][1],
                            count: entry.price_subtotal,
                            id:entry[this.state.wtDropdown.groupStateRevenue] ? (this.state.wtDropdown.groupStateRevenue === 'state' ? entry[this.state.wtDropdown.groupStateRevenue] : entry[this.state.wtDropdown.groupStateRevenue][1]) : entry[this.state.wtDropdown.groupStateRevenue][1],
                        })
                    }
                }
            }

            this.state.activeTable = true;
            this.state.chartLabel = 'Revenue'
            this.state.wtDropdown.jouranalItems = false;
            this.state.wtDropdown.IsAccountFilter = false;
            this.state.wtDropdown.IsPartnerFilter = false;
            this.state.wtDropdown.comparisonState = false;
            this.state.wtDropdown.IsDateFilter = false;
            this.state.wtDropdown.groupBy = false;
            this.state.modelState = "sale.report";
            this.state.wtDropdown.groupByRevenue = true;
            this.state.wtDropdown.customDate = true;
        }
        this.state.monthlyData = dataList;
        this.state.expenseConfig = dateExpenseList;
        this.state.accountConfig = demoDataList;
        this.state.dateDomain = [['date', '>', this.state.current_date], ['date', '<', this.state.today]]
        if(!window.onload){
            if(document.querySelector('.dactive')){
                this.state.tableLabel = document.querySelector('.dactive').childNodes[1].textContent;
            }else if(document.querySelector('.hactive')){
                this.state.tableLabel = document.querySelector('.hactive').lastChild.textContent;
            }
        }
    }

    resetTable(){
        this.state.wtDropdown.wtPartnerFilterOption = !this.state.wtDropdown.wtPartnerFilterOption;
    }

    setActiveItem(itemId, state) {
        state.toggleOpen = !state.toggleOpen;
        state.activeItem = itemId;
        localStorage.setItem('item', itemId);
    }
    async wtOnChangePeriod() {
        this.getDate();
        await Promise.all([
            this.getInvoice(),
            this.getPaidInvoice(),
            this.BillDetails(),
            this.CreditNotes(),
            this.DebitNotes()
        ])
        this.state.wtDropdown.dateSelect = false;
        if (this.state.period === '30') {
            this.state.wtDropdown.wtDateFilter === 'this_month';
            this.state.wtDropdown.dropDownLabel = 'This Month';
        } else if (this.state.period === '90') {
            this.state.wtDropdown.wtDateFilter === 'this_quarter';
            this.state.wtDropdown.dropDownLabel = 'This Quarter';
        } else if (this.state.period === '365') {
            this.state.wtDropdown.wtDateFilter === 'this_year';
            this.state.wtDropdown.dropDownLabel = 'This Year';
        }
    }

    // Getting The invoice 
    async getInvoice() {
        let domain = []
        if (this.state.period > 0) {
            domain.push(['invoice_date', '>', this.state.current_date]);
        }
        try {
            domain.push(['move_type', '=', 'out_invoice']);
            let data = await this.env.services.orm.searchCount("account.move", domain);
            let total_amount = await this.env.services.orm.readGroup("account.move", domain, ["amount_total_signed:sum"], [])

            if (!total_amount[0].amount_total_signed) {
                total_amount[0].amount_total_signed = 0;
            }
            if (isNaN(data) || isNaN(this.state.invoice.value)) {
                throw new Error('InValid Data');
            }

            let prev_domain = [['move_type', '=', 'out_invoice']];
            if (this.state.period > 0) {
                prev_domain.push(['invoice_date', '>', this.state.prev_date], ['invoice_date', '<=', this.state.current_date]);
            }

            let prev_data = await this.env.services.orm.searchCount("account.move", prev_domain);
            let percentage = ((data - prev_data) / prev_data) * 100;


            this.state.invoice = {
                value: data,
                percentage: percentage.toLocaleString(undefined, {
                    maximumFractionDigits: 2,
                    minimumFractionDigits: 2
                }),
                invoiceTotal: `$${total_amount[0].amount_total_signed}`,
            }
        } catch (error) {
            console.log("Error", error);
        }

    }

    // For Getting Payments
    async getPaidInvoice() {
        let domain = [];
        if (this.state.period > 0) {
            domain.push(['date', '>', this.state.current_date]);
        }

        try {
            let data = await this.env.services.orm.searchCount("account.payment", domain);
            if (isNaN(data) || isNaN(this.state.invoice.value)) {
                throw new Error("Invalid Payment Data");
            }
            let total_amount = await this.env.services.orm.readGroup("account.payment", domain, ["amount:sum"], []);

            if (!total_amount[0].amount) {
                total_amount[0].amount = 0;
            }

            let prev_domain = [['state', 'in', ['draft', 'posted']]];
            if (this.state.period > 0) {
                prev_domain.push(['date', '<=', this.state.current_date], ['date', '>', this.state.prev_date]);
            }

            let prev_data = await this.env.services.orm.searchCount("account.payment", prev_domain);

            let percentage = ((data - prev_data) / prev_data) * 100

            this.state.paidInvoice = {
                value: data,
                percentage: percentage.toLocaleString(undefined, {
                    maximumFractionDigits: 2,
                    minimumFractionDigits: 2
                }),
                PaymentTotal: `$${total_amount[0].amount}`,
            }

        } catch (error) {
            console.log("Error", error);
        }
    }

    //Getting The Bill Details
    async BillDetails() {
        let domain = []
        if (this.state.period > 0) {
            domain.push(['invoice_date', '>', this.state.current_date]);
        }
        try {
            domain.push(['move_type', '=', 'in_invoice']);
            let data = await this.env.services.orm.searchCount("account.move", domain);
            let total_amount = await this.env.services.orm.readGroup("account.move", domain, ["amount_total_signed:sum"], []);

            if (!total_amount[0].amount_total_signed) {
                total_amount[0].amount_total_signed = 0;
            }

            if (isNaN(data) || isNaN(this.state.invoice.value)) {
                throw new Error('InValid Data');
            }

            let prev_domain = [['move_type', '=', 'in_invoice']];
            if (this.state.period > 0) {
                prev_domain.push(['invoice_date', '>', this.state.prev_date], ['invoice_date', '<=', this.state.current_date]);
            }

            let prev_data = await this.env.services.orm.searchCount("account.move", prev_domain);
            let percentage = ((data - prev_data) / prev_data) * 100

            this.state.wtbill = {
                billCount: data,
                billTotal: `$${total_amount[0].amount_total_signed}`,
                BillPerCent: percentage.toLocaleString(undefined, {
                    maximumFractionDigits: 2,
                    minimumFractionDigits: 2
                })
            }
        } catch (error) {
            console.log("Error", error);
        }
    }

    // Counting The credit Notes
    async CreditNotes() {
        let domain = []
        if (this.state.period > 0) {
            domain.push(['invoice_date', '>', this.state.current_date]);
        }
        try {
            domain.push(['move_type', '=', 'out_refund']);
            let data = await this.env.services.orm.searchCount("account.move", domain);

            if (isNaN(data) || isNaN(this.state.invoice.value)) {
                throw new Error('InValid Data');
            }

            let total_amount = await this.env.services.orm.readGroup("account.move", domain, ["amount_total_signed:sum"], []);

            if (!total_amount[0].amount_total_signed) {
                total_amount[0].amount_total_signed = 0;
            }

            let prev_domain = [['move_type', '=', 'out_refund']];
            if (this.state.period > 0) {
                prev_domain.push(['invoice_date', '>', this.state.prev_date], ['invoice_date', '<=', this.state.current_date]);
            }
            let prev_data = await this.env.services.orm.searchCount("account.move", prev_domain);
            let percentage = ((data - prev_data) / prev_data) * 100


            this.state.wtCredit = {
                CreditCount: data,
                CreditPercent: percentage.toLocaleString(undefined, {
                    maximumFractionDigits: 2,
                    minimumFractionDigits: 2
                }),
                totalCredit: `$${total_amount[0].amount_total_signed}`,
            }
        } catch (error) {
            console.log("Error", error);
        }
    }

    // Counting The Debit Notes
    async DebitNotes() {
        let domain = []
        if (this.state.period > 0) {
            domain.push(['invoice_date', '>', this.state.current_date]);
        }
        try {
            domain.push(['move_type', '=', 'in_refund']);
            let data = await this.env.services.orm.searchCount("account.move", domain);

            if (isNaN(data) || isNaN(this.state.invoice.value)) {
                throw new Error('InValid Data');
            }
            let total_amount = await this.env.services.orm.readGroup("account.move", domain, ["amount_total_signed:sum"], []);

            if (!total_amount[0].amount_total_signed) {
                total_amount[0].amount_total_signed = 0;
            }
            let prev_domain = [['move_type', '=', 'in_refund']];
            if (this.state.period > 0) {
                prev_domain.push(['invoice_date', '>', this.state.prev_date], ['invoice_date', '<=', this.state.current_date]);
            }
            let prev_data = await this.env.services.orm.searchCount("account.move", prev_domain);

            let percentage = ((data - prev_data) / prev_data) * 100

            this.state.wtDebit = {
                DebitCount: data,
                DebitPercent: percentage.toLocaleString(undefined, {
                    maximumFractionDigits: 2,
                    minimumFractionDigits: 2
                }),
                totalDebit: `$${total_amount[0].amount_total_signed}`,
            }
        } catch (error) {
            console.log("Error", error);
        }
    }

    toggleSidebar() {
        var self = this;
        this.state.toggleOpen = !this.state.toggleOpen;
    }

    // Action Function Which Shows use External Id of The Page and Display The Desired Data
    viewInvoice() {
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

    viewPayement() {
        let domain = [];
        if (this.state.period > 0) {
            domain.push(['date', '>', this.state.current_date]);
        }

        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "Payment",
            res_model: "account.payment",
            domain,
            context: {},
            views: [
                [false, "list"],
                [false, "form"],
            ]
        });
    }

    viewBills() {
        let domain = [['move_type', '=', 'in_invoice']]
        if (this.state.period > 0) {
            domain.push(['invoice_date', '>', this.state.current_date]);
        }
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "Bills",
            res_model: "account.move",
            domain,
            context: {},
            views: [
                [false, "list"],
                [false, "form"],
            ]
        });
    }

    viewCreditNotes() {
        let domain = [['move_type', '=', 'out_refund']]
        if (this.state.period > 0) {
            domain.push(['invoice_date', '>', this.state.current_date]);
        }
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "Credit Notes",
            res_model: "account.move",
            domain,
            context: {},
            views: [
                [false, "list"],
                [false, "form"],
            ]
        });
    }

    viewDebitNotes() {
        let domain = [['move_type', '=', 'in_refund']]
        if (this.state.period > 0) {
            domain.push(['invoice_date', '>', this.state.current_date]);
        }
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "Debit Notes",
            res_model: "account.move",
            domain,
            context: {},
            views: [
                [false, "list"],
                [false, "form"],
            ]
        });
    }

    getDropdown(filter, value, option, name) {
        if (filter === 'DateFilter') {
            this.state.wtDropdown.wtDateFilter = value;
            if (this.state.wtDropdown.wtDateFilter === 'this_month') {
                this.state.wtDropdown.dropDownLabel = 'This Month';
            } else if (this.state.wtDropdown.wtDateFilter === 'this_quarter') {
                this.state.wtDropdown.dropDownLabel = 'This Quarter';
            } else if (this.state.wtDropdown.wtDateFilter === 'this_year') {
                this.state.wtDropdown.dropDownLabel = 'This Year';
            } else if (this.state.wtDropdown.wtDateFilter === 'today') {
                this.state.wtDropdown.dropDownLabel = 'Today';
            } else if (this.state.wtDropdown.wtDateFilter === 'last_month') {
                this.state.wtDropdown.dropDownLabel = 'Last Month';
            } else if (this.state.wtDropdown.wtDateFilter === 'last_quarter') {
                this.state.wtDropdown.dropDownLabel = 'Last Quarter';
            } else if (this.state.wtDropdown.wtDateFilter === 'last_year') {
                this.state.wtDropdown.dropDownLabel = 'Last Year';
            } else if (this.state.wtDropdown.wtDateFilter === 'custom') {
                this.state.wtDropdown.start_date = $('input[name="date_start"]').val();
                this.state.wtDropdown.end_date = $('input[name="date_end"]').val();
                if (this.state.wtDropdown.start_date && this.state.wtDropdown.end_date) {
                    this.state.wtDropdown.dropDownLabel = `From:${this.state.wtDropdown.start_date},
                   End:${this.state.wtDropdown.end_date}`
                } else {
                    this.state.wtDropdown.wtDateFilter === 'this_year';
                }
                this.state.wtDropdown.wtPartnerFilterOption = !this.state.wtDropdown.wtPartnerFilterOption;
            }
        } else if (filter === 'AccountFilter') {
            let wtAccountFilter = this.state.wtDropdown.wtAccountFilter
            if (wtAccountFilter.includes(value)) {
                const index = wtAccountFilter.indexOf(value);
                if (index > -1) {
                    wtAccountFilter.splice(index, 1);
                }
            } else {
                wtAccountFilter.push(value);
            }
            this.state.wtDropdown.wtAccountFilter = wtAccountFilter;
        } else if (filter === 'PartnerFilter') {
            this.state.wtDropdown.wtPartnerFilter = $('select[name="selectionPartner"]').val();
            this.state.wtDropdown.wtPartnerTagFilter = $('select[name="selectionTag"]').val();
            this.state.wtDropdown.wtPartnerFilterOption = !this.state.wtDropdown.wtPartnerFilterOption;
        } else if (filter === 'jouranalItems') {
            let journal_item = this.state.wtDropdown.wtJouranlItemId;
            let label = this.state.wtDropdown.journalLabels;
            if (journal_item[0][option]) {
                if (option === 'journal_group_id') {
                    // Condition For Preventing journal_group id if I got the same id again means I need to unckeck id
                    if (journal_item[0][option].includes(value)) {
                        let index = journal_item[0][option].indexOf(value);
                        let lable_index = label.indexOf(name);
                        if (index > -1) {
                            journal_item[0][option].splice(index, 1);
                            label.splice(lable_index, 1);
                        }
                    } else {
                        journal_item[0][option][0] = value;
                        label = [name];
                    }
                } else if (journal_item[0][option].includes(value)) {
                    let index = journal_item[0][option].indexOf(value);
                    let lable_index = label.indexOf(name);
                    if (index > -1) {
                        journal_item[0][option].splice(index, 1);
                        label.splice(lable_index, 1);
                    }
                } else {
                    journal_item[0][option].push(value);
                    label.push(name);
                }
            }
            this.state.wtDropdown.journalLabels = label;
            this.state.wtDropdown.wtJouranlItemId = journal_item;
            this.state.wtDropdown.journalOption = option;
            this.state.wtDropdown.wtPartnerFilterOption = !this.state.wtDropdown.wtPartnerFilterOption;
        } else if (filter === 'Comparison') {
            this.state.wtDropdown.wtComparison = value;
            if (this.state.wtDropdown.wtComparison == 'previous_period') {
                this.state.wtDropdown.comparePeriod = $('input[name="periods_number"]').val();
            } else if (this.state.wtDropdown.wtComparison == 'same_last_year') {
                this.state.wtDropdown.comparePeriod = $('input[name="same_periods_number"]').val();
            } else if (this.state.wtDropdown.wtComparison == 'custom') {
                this.state.wtDropdown.comparisonFrom = $('input[name="custom_date_from"]').val();
                this.state.wtDropdown.comparisonTo = $('input[name="custom_date_to"]').val();
            }
            this.state.wtDropdown.wtPartnerFilterOption = !this.state.wtDropdown.wtPartnerFilterOption;
        } else if (filter === 'GroupBy') {
            if (value === 'Date' && option != this.state.wtDropdown.dateState) {
                this.state.wtDropdown.dateState = option;
                this.state.wtDropdown.groupDate = value;
            } else if (value === this.state.wtDropdown.groupState && this.state.wtDropdown.groupDate) {
                this.state.wtDropdown.groupState = '';
            } else if (option === this.state.wtDropdown.dateState) {
                this.state.wtDropdown.dateState = '';
                this.state.wtDropdown.groupDate = '';
                if(this.state.wtDropdown.groupState === ''){
                    this.state.wtDropdown.groupState ='employee_id';
                }
            }
            else {
                this.state.wtDropdown.groupState = value;
                sessionStorage.setItem('group_id',value);
            }
            this.state.wtDropdown.wtPartnerFilterOption = !this.state.wtDropdown.wtPartnerFilterOption;

        } else if (filter === 'GroupByRevenue') {
            if(value === 'Group_Date' && option != this.state.wtDropdown.dateState1){
                this.state.wtDropdown.dateState1 = option;
                this.state.wtDropdown.groupDate1 = value;
            }else if(value === this.state.wtDropdown.groupStateRevenue &&  this.state.wtDropdown.groupDate1){
                this.state.wtDropdown.groupStateRevenue = '';
            }else if(option === this.state.wtDropdown.dateState1){
                this.state.wtDropdown.dateState1 = '';
                this.state.wtDropdown.groupDate1 = ''; 
                if(this.state.wtDropdown.groupStateRevenue === ''){
                    this.state.wtDropdown.groupStateRevenue ='user_id';
                }
            }
            else{
                this.state.wtDropdown.groupStateRevenue = value;
            }
            this.state.wtDropdown.wtPartnerFilterOption = !this.state.wtDropdown.wtPartnerFilterOption;
        }
    }

    getDate() {
        this.state.today = moment().subtract(0, 'days').format('YYYY-MM-DD');
        this.state.current_date = moment().subtract(this.state.period, 'days').format('YYYY-MM-DD');
        this.state.prev_date = moment().subtract(this.state.period * 2, 'days').format('YYYY-MM-DD');
    }

}

on_wt_dashboard.template = "warlock_financial_dashboard_financial_dashboard.wt_dashboard";
on_wt_dashboard.components = { KpiCard, ChartRender, Chartfiter, DashBoardTable };

registry.category("actions").add("wt_dashboard", on_wt_dashboard);