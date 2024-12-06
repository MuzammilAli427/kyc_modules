/** @odoo-module */

import { useService } from '@web/core/utils/hooks';
import { Component, useState,onMounted} from "@odoo/owl";

export class DashBoardTable extends Component {
    setup(){

        this.state = useState({
            row_id:'',
            table_config:[],
            temp_id:'',
        })

        this.actionService = useService('action');
        this.orm = useService('orm');
    };
    
   async viewChildData(id,props,state){
    let domain = [];
    let table_data=[];
    state.temp_id = id;
    props.childState = true;
    if(this.props.getDate === 'Date' || this.props.revenueDate ==='Group_Date'){
    domain.push(['date',id[0][1],id[0][2]],['date',id[1][1],id[1][2]]);
    }else{
        if(this.props.WtmenuItem === 'item7'){
            domain.push([this.props.groupState,'=',id]);
        }else if(this.props.WtmenuItem === 'item8'){
            domain.push([this.props.revenueState,'=',id])
        }
        if(props.dateDomain[0][2] === props.dateDomain[1][2]){
            // We Pass Empty Because That means User Doesn'r Select any Filter.
        }else{
            domain.push(['date','>',props.dateDomain[0][2]],['date','<',props.dateDomain[1][2]])
        }
    }
    let list_ids = await this.env.services.orm.search(props.wtModel, domain);
    let results = await this.env.services.orm.read(props.wtModel,list_ids, props.fields);
    for(let i=0; i < results.length; i++){
        if(this.props.WtmenuItem === 'item7'){
            table_data.push(
                {
                'id':results[i]['id'],
                'name':results[i][props.fields[0]],
                'date':results[i][props.fields[1]],
                'employee_name':results[i][props.fields[2]][1],
                'total':results[i][props.fields[3]]
            })
        }else if(this.props.WtmenuItem === 'item8'){
            table_data.push(
                {
                'id':results[i]['id'],
                'name':results[i][props.fields[0]][1],
                'date':results[i][props.fields[1]],
                'employee_name':results[i][props.fields[2]][1],
                'total':results[i][props.fields[3]],
                'taxed':results[i][props.fields[4]]
            })
        }
    }

    state.table_config = table_data;
   }
};

DashBoardTable.template = 'wtdahsboadTable';