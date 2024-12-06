from odoo import fields, models, _
from odoo.exceptions import ValidationError
from datetime import datetime
import json
import io
from odoo.tools import date_utils

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter


class GSHWizard(models.TransientModel):
    _name = "gsh.wizard"

    start_date = fields.Date(string="From")
    end_date = fields.Date(string="To")
    currency_id = fields.Many2one("res.currency", string="Currency")
    report = fields.Selection(
        [("balance", "Balance Report"), ("income", "Income Report")], string="Report"
    )

    def get_pdf(self):
        self.check_date()
        return self.env.ref("gsh_reporting.action_report_gsh").report_action(self.id)

    def get_xlsx(self):
        datas = {"self_id": self.id}
        return {
            "type": "ir.actions.report",
            "report_type": "xlsx",
            "data": {
                "model": "gsh.wizard",
                "output_format": "xlsx",
                "options": json.dumps(datas, default=date_utils.json_default),
                "report_name": "GSH Report",
            },
        }

    def check_date(self):
        self.ensure_one()
        if self.start_date > self.end_date:
            raise ValidationError(_("Please select appropriate dates"))

        # return self._get_printable_values()

    def _get_printable_values(self):
        """This method retrieves values suitable for printing or display."""

        # Extract month and year from start_date
        start_month = self.start_date.month
        start_year = self.start_date.year

        # Extract month and year from end_date
        end_month = self.end_date.month
        end_year = self.end_date.year

        bank_statement_domain = [
            ("date", ">=", f"{start_year}-{start_month:02d}-01"),
            ("date", "<=", f"{end_year}-{end_month:02d}-31"),
            ("company_id", "=", self.env.company.id),
        ]

        if self.currency_id:
            bank_statement_domain.append(("currency_id", "=", self.currency_id.id))

        bank_statements = self.env["account.bank.statement"].search(
            bank_statement_domain, order="date asc"
        )

        monthly_balance = {}
        months = []
        monthly_balance_dict = {}
        for statement in bank_statements:
            journal_name = statement.journal_id
            stmt_month = statement.date.strftime("%B")
            stmt_year = statement.date.year
            month_str = str(stmt_month) + "-" + str(stmt_year)
            if month_str not in months:
                months.append(month_str)
            # monthly_balance.update({month_str: statement.balance_end_real})

            if journal_name not in monthly_balance_dict:
                monthly_balance_dict[journal_name] = {}

            # Update the monthly_balance_dict for the current journal
            if self.report == "balance":
                monthly_balance_dict[journal_name].update(
                    {month_str: statement.balance_end_real}
                )
            elif self.report == "income":
                total_incoming_amount = 0
                for line in statement.line_ids:
                    if line.move_id._get_reconciled_invoices():
                        total_incoming_amount += line.amount

                monthly_balance_dict[journal_name].update(
                    {month_str: total_incoming_amount}
                )
        return {"months": months, "monthly_balance": monthly_balance_dict}

    def formulate_excel_report(self, response):
        """This method involves the process of structuring, organizing,
        and composing data and information in a manner suitable
        for presentation in an Excel spreadsheet."""

        printable_values = self._get_printable_values()
        if self.report == "balance":
            HEADING = "Balance Report"
        elif self.report == "income":
            HEADING = "Incoming Report"

        # Workbook Operations
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {"in_memory": True})
        sheet = workbook.add_worksheet()
        head = workbook.add_format(
            {"align": "center", "bold": True, "font_size": "20px"}
        )
        thead = workbook.add_format(
            {"align": "center", "bold": True, "font_size": "10px"}
        )
        cell_format = workbook.add_format(
            {
                "font_size": "12px",
            }
        )
        txt = workbook.add_format({"font_size": "10px", "align": "center"})
        sheet.merge_range("G2:L3", HEADING, head)
        sheet.write("G6", "From:", cell_format)
        sheet.merge_range(
            "H6:I6",
            self.start_date.strftime("%B") + "-" + str(self.start_date.year),
            txt,
        )
        sheet.write("K6", "To:", cell_format)
        sheet.merge_range(
            "L6:N6",
            self.end_date.strftime("%B") + "-" + str(self.end_date.year),
            txt,
        )

        sheet.write("C8", "Bank", thead)
        sheet.write("D8", "Currency", thead)
        header_column = 4
        header_row = 7
        for header in printable_values.get("months"):
            sheet.write(header_row, header_column, header, thead)
            header_column = header_column + 1
        data_row = 8
        data_column = 2

        for journal in printable_values.get("monthly_balance"):
            sheet.write(data_row, data_column, journal.name, txt)
            sheet.write(
                data_row,
                data_column + 1,
                journal.currency_id.name or self.env.company.currency_id.name,
                txt,
            )
            balance_column = 4
            for month in printable_values.get("months"):
                value = printable_values.get("monthly_balance").get(journal).get(month)
                sheet.write(data_row, balance_column, value, txt)
                balance_column = balance_column + 1
            data_row = data_row + 1
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
