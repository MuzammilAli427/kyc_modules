odoo.define('payment_by_invoice_lines_omax.custom_payment', function (require) {
"use strict";
    var ShowPaymentLineWidget = require('account.payment');
    var core = require('web.core');
    var field_registry = require('web.field_registry');
    var field_utils = require('web.field_utils');
    var AbstractField = require('web.AbstractField');

    var QWeb = core.qweb;
    var _t = core._t;
    ShowPaymentLineWidget.ShowPaymentLineWidget.include({
        events: _.extend({
            'click .outstanding_credit_assign': '_onOutstandingCreditAssign',
        }, AbstractField.prototype.events),
        _onRemoveMoveReconcile: function (event) {
            //make payment_id to get value by static/src/xml file 
            var payment_id = parseInt($(event.currentTarget).attr('account-payment-id'))//cust
            var self = this;
            var moveId = parseInt($(event.target).attr('move-id'));
            var partialId = parseInt($(event.target).attr('partial-id'));
            if (partialId !== undefined && !isNaN(partialId)){
                this._rpc({
                    model: 'account.move',
                    method: 'js_remove_outstanding_partial',
                    args: [moveId, partialId],// payment_id
                    context:{payment_main_id : payment_id}//pass val in context 
                }).then(function () {
                    self.trigger_up('reload');
                });
            }
        },
    });
});
