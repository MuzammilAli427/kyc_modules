# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import content_disposition, request
from odoo.tools import html_escape
import json


class XLSXReportController(http.Controller):
    @http.route("/print_excel", type="http", auth="user", methods=["POST"], csrf=False)
    def get_report_xlsx(self, model, options, output_format, report_name, **kw):
        options = json.loads(options)
        report_obj = request.env[model].sudo().browse(options.get("self_id"))
        token = "sample-token"
        try:
            if output_format == "xlsx":
                response = request.make_response(
                    None,
                    headers=[
                        ("Content-Type", "application/vnd.ms-excel"),
                        (
                            "Content-Disposition",
                            content_disposition(report_name + ".xlsx"),
                        ),
                    ],
                )
                report_obj.formulate_excel_report(response)
            response.set_cookie("fileToken", token)
            return response
        except Exception as e:
            se = http.serialize_exception(e)
            error = {"code": 200, "message": "Odoo Server Error", "data": se}
            return request.make_response(html_escape(json.dumps(error)))
