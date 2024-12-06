# -*- coding: utf-8 -*-

import time
from odoo import api, models, _
from odoo.exceptions import UserError
from datetime import datetime
import json

class ReportPaymentAmountOverview(models.AbstractModel):
    _name = 'report.bit_financial_chart.report_payment_amount'
    _description = 'Report Payment Amount'


    def chart_img(self, date_from, date_to):                                                                            
        # partner = data['form'].get('partner_id', False)
        orders_this_year = self.env['account.payment'].read_group(                                  
            ['&', '&',                                                                         
             ('payment_type','=','inbound'),                                                     
             ('date', '>=', date_from),                      
             ('date', '<=', date_to)],                   
            ['amount'],                                                                
            ['date:month']                                                               
        )                                                                                      
        # import pdb;pdb.set_trace();                                                           
        months = [order['date:month'] for order in orders_this_year]                     
        amount_values = [order['amount'] for order in orders_this_year]                   
        quantity_values = [order['date_count'] for order in orders_this_year]                   
        print (months)                                                                                    
        print (amount_values)                                                                                    
        print (quantity_values)                                                                                    
        data = {                                                                               
            'type': 'bar',                                                                     
            'data': {                                                                          
                'labels': months,                                                              
                'datasets': [                                                                  
                    {   
                        'label': 'Quantity',            
                        "borderColor": "rgb(255, 99, 132)",
                        "backgroundColor": "rgb(255, 99, 132)",
                        "fill": False,                                      
                        'data': quantity_values,
                        "yAxisID": "y"                                       
                    },
                    {    
                        'label': 'Amount',                                        
                        "borderColor": "rgb(54, 162, 235)",
                        "backgroundColor": "rgb(54, 162, 235)",
                         "fill": False,                                                                   
                        'data': amount_values,
                         "yAxisID": "y1"
                                                                       
                    },                                                                         
                ]                                                                              
            },
            "options": {
            "title": {
      "display": True,
      "text": "Payment Amount"
    },
    "scales": {
      "yAxes": [
      {
        "id": "y",
        "type": "linear",
        "display": True,
        "position": "left"
      }, 
      {
        "id": "y1",
        "type": "linear",
        "display": True,
        "position": "right",
        "gridLines": {
          "drawOnChartArea": False
        }
      }
      ]
      }
      }


        }                                                                                      
        return f"https://quickchart.io/chart?c={json.dumps(data)}"


    @api.model
    def _get_report_values(self, docids, data=None):
        if not data.get('form') or not self.env.context.get('active_model'):
            raise UserError(_("Form content is missing, this report cannot be generated."))
        model = self.env.context.get('active_model')
        docs = self.env[model].browse(self.env.context.get('active_ids', []))
        date_from = data['form'].get('date_from', False)
        date_to = data['form'].get('date_to', False)

        # cr = self._cr
        # cr.execute(f"""
        #                 SELECT
        #                     TO_CHAR(date_trunc('month', date), 'YYYY-MM') AS month,
        #                     COUNT(id) AS invoice_quantity,
        #                     SUM(amount) AS total_amount,
        #                     SUM(CASE WHEN state = 'posted' THEN amount ELSE 0 END) AS paid_amount
        #                 FROM
        #                     account_move
        #                 WHERE
        #                     EXTRACT(YEAR FROM date) = EXTRACT(YEAR FROM NOW())
        #                     {"AND date >= '" + str(date_from) + "'" if date_from else ""}
        #                     {"AND date <= '" + str(date_to) + "'" if date_to else ""}
        #                 GROUP BY
        #                     TO_CHAR(date_trunc('month', date), 'YYYY-MM')
        #                 ORDER BY
        #                     TO_CHAR(date_trunc('month', date), 'YYYY-MM') DESC;
        #                 """)
        # records = cr.fetchall()
        # chart_data = {                                                                               
        #     'type': 'bar',                                                                     
        #     'data': {                                                                          
        #         'labels': [months[0] for months in records],                                                              
        #         'datasets': [                                                                  
        #             {                                                                          
        #                 'label': 'Payment',                                        
        #                 'data': [months[1] for months in records]                                                     
        #             },
        #             {                                                                          
        #                 'label': 'Amount',                                        
        #                 'data': [months[2] for months in records]                                                     
        #             },                                                                         
        #         ]                                                                              
        #     },                                                                                 
        # }
        chart_img = self.chart_img(date_from, date_to)
        # chart_img = f"https://quickchart.io/chart?c={json.dumps(chart_data)}"

        
        return {
            'doc_ids': docids,
            'doc_model': model,
            'data': data['form'],
            'docs': docs,
            'time': time,
            # 'records': records,  # complete records
            # (Used to bring current user who is making printing this report)
            'user_id': self.env['res.users'].browse(self._uid).name,
            'date_from': date_from,
            'date_to': date_to,
            'chart_img': chart_img,
        }

