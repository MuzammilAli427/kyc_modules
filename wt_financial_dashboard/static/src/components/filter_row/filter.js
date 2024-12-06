/** @odoo-module */

import {Component, useState, onWillStart} from  "@odoo/owl";

export class Chartfiter extends Component {
	setup() {
		this.state = useState({
			partner_ids: [],
			partner_tag_ids: [],
			journal_datas:[],
			toggle:'',
			toggle1:'',
			toggle2:'',
			tempDateGroup:'',
			tempDateGroup1:'',
			toggle3:'',
		});
		// this.orm = useService("orm");
		onWillStart(async () => {
			await this.getPartner();
			await this.getPartnerTag();
			await this.getAccountJournalData();
		})

	}
	wtToggleMenu(state,value){
		if(state.toggle == value){
			state.toggle = ''
		}else{
			state.toggle = value;
		}
	}
	wtToggleMenu1(state,value){
		if(state.toggle1 == value){
			state.toggle1 = ''
		}else{
			state.toggle1 = value;
		}
	}
	wtToggleMenu2(state,value){
		if(state.toggle2 == value){
			state.toggle2 = ''
		}else{
			state.toggle2 = value;
		}
	}
	wtToggleMenu3(state,value){
		if(state.toggle3 == value){
			state.toggle3 = ''
		}else{
			state.toggle3 = value;
		}
	}
	wtDateTick(state,value){
		if(value === state.tempDateGroup){
			state.tempDateGroup = false;
		}else{
			state.tempDateGroup = value;
		}
	}
	wtDateTick1(state,value){
		if(value === state.tempDateGroup1){
			state.tempDateGroup1 = false;
		}else{
			state.tempDateGroup1 = value;
		}
	}
	async getPartner() {
		let data = await this.env.services.orm.call('res.partner', 'search_read', [], { 
			fields: ["id", "name", "display_name"],
            domain: [], 
        });
        this.state.partner_ids = data
	}
	async getPartnerTag() {
		let data = await this.env.services.orm.call('res.partner.category', 'search_read', [], { 
			fields: ["id", "name", "display_name"],
            domain: [], 
        });
		this.state.partner_tag_ids = data
	}

	async getAccountJournalData(){
		let data = await this.env.services.orm.call('account.journal','search_read',[],{
			fields:["id","name"],
			domain:[]
		})
		let journal_groupdata = await this.env.services.orm.call('account.journal.group','search_read',[],{
			fields:["id","name"],
			domain:[],
		})
		if(journal_groupdata){
			this.state.journal_datas.push({
				label:"Journal Groups",
				data:journal_groupdata,
				option:'journal_group_id'
			});
		}
		this.state.journal_datas.push({
			label:"Your Company",
			data:data,
			option:'journals'
		});
	}
}

Chartfiter.template = 'wt_filter_component'