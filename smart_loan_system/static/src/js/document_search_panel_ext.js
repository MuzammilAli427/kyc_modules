/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { DocumentsSearchPanel } from "@documents/views/search/documents_search_panel";

debugger
patch(DocumentsSearchPanel.prototype, "smart_loan_system", {
    /**
     * @override
     */
    setup() {
        debugger
        this.res_model = this.env.model.rootParams.context.active_model
        this._super(...arguments);
    },

    DisableFolders(display_name) {
      let retail_fold = ['ID', 'Driving License', 'Passport', 'Others']
      let corporate_fold = ['KvK', 'Articles of incorporation', 'Shareholder register', 'Company Documentations']
      if (this.res_model == 'kyc.retail'){
        if (display_name === 'ID' || display_name === 'Driving License' || display_name === 'Passport' || display_name === 'Others') {
            return true;
          } else {
            return false;
          }
        }
      if (this.res_model == 'kyc.corporate'){
            if (display_name === 'KvK' || display_name === 'Articles of incorporation' || display_name === 'Shareholder register' || display_name === 'Company Documentations') {
                return true;
            } else {
                return false;
            }
        }
      if (this.res_model == 'loan.collateral'){
            const allowedDisplayNames = [
                'Collaterals',
                'Mortgage',
                'Mortgage Deed',
                'Appraisal Report',
                'Kadaster Registration',
                'Power of attorney',
                'Other',
                'Vehicle',
                'FOT',
                'Inspection certificate of car',
                'Other',
                'Insurance',
                'Car',
                'Life',
                'Fire',
                'Personal Accident',
                'Inventory / Fixed Assets',
                'Liability',
                'CAR (construction all risk)',
                'Other',
                'Guarantee',
                'Corporate Guarantee',
                'Personal Guarantee',
                'Cross Corporate Guarantee',
                'Net Worth Statement',
                'Other',
                'Cash',
                'Pledge Agreement TD',
                'Pledge Agreement Savings',
                'Other',
                'Receivables',
                'Assignment Receivables Deed',
                'Account Receivables Listing By Aging Report',
                'Other',
                'General',
                'Income Assignment',
                'Specific General Assignment',
                'General Assignment',
                'Salary Assignment',
                'Lease Income Assignment',
                'Inventory/Fixed Assets',
                'FEO Inventory Assignment Deed',
                'Inventory Listing',
                'Salary Statement',
                'Pension Statement',
                'Pension Withholding Letter',
                'Salary Withholding Letter',
                'Insurance Payment Receipt',
                'Other',
                'Loan Subordination',
                'Loan Subordination Deed',
                'Other',
                'Pledge of Shares',
                'Pledge of Shares Deeds',
                'Shareholder Register',
                'Excerpt of Curacao Chamber',
                'Other',

            ];

            if (allowedDisplayNames.includes(display_name)) {
                debugger;
                return true;
            } else {
                return false;
            }
        }
        if (this.res_model == 'account.loan') {
            const allowedDisplayNames = [
                'Loan Documents',
                'Salary Statement',
                'Pension Statement',
                'Pension Withholding Letter',
                'Salary Withholding Letter',
                'Insurance Payment receipt',
                'Business Proposal',
                'Balance Sheet',
                'Income Statement',
                'Cash Flow Statement',
                'Recent Audited Financials',
                'Corporate Tax Returns',
                'Bank Statements',
                'Debt Schedule',
                'Appraisal Reports',
                'Mortgage Deeds',
                'Inventory Lists',
                'Articles of Association/Bylaws',
                'Operating Agreements',
                'Shareholder Agreements',
                'Business Licenses',
                'Interim Financial Statements',
                'Personal Financial Statements',
                'Business Credit Report',
                'Personal Credit Report',
                'KYC Documents',
                'Proof of Address',
                'Leases and Contracts',
                'Recent Asset Valuations',
                'Insurance Policies',
                'Restructuring Agreement',
                'Environmental Reports',
                'Industry Licenses/Permits',
                'Memo',
                'Executive Summary'
            ];

            if (allowedDisplayNames.includes(display_name)) {
                debugger;
                return true;
            } else {
                return false;
            }
        }

      if (this.res_model == 'kyc.groups'){
            if (display_name === 'KvK' || display_name === 'Articles of incorporation' || display_name === 'Shareholder register' || display_name === 'Company Documentations') {
                return true;
            } else {
                return false;
            }
        } else {
            return true;
        }
    },
    });