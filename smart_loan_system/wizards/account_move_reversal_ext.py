from odoo import api, fields, models, _


class MoveReversalExt(models.TransientModel):
    _inherit = 'account.move.reversal'

    def reverse_moves(self):
        res = super(MoveReversalExt, self).reverse_moves()
        parent_move = self.move_ids[0].reversed_entry_id
        move = self.move_ids[0]
        move_line = move.invoice_line_ids.filtered(lambda l: l.debit)
        parent_line = parent_move.invoice_line_ids.filtered(lambda l: l.name == move_line.name)
        if parent_line:
            parent_line.write({'unpaid_amount': parent_line.unpaid_amount + move_line.amount_currency,
                               'paid_amount': parent_line.paid_amount - move_line.amount_currency})
        parent_move.write({'writeoff_reverse_entry_id' : self.new_move_ids[0].id})
        return res
