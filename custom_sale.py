# -*- coding: utf-8 -*-
##############################################################################
#
#    This module uses OpenERP, Open Source Management Solution Framework.
#    Copyright (C) 2015-Today BrowseInfo (<http://www.browseinfo.in>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>
#
##############################################################################

from datetime import datetime, timedelta
import time
from openerp.osv import fields, osv


class sale_order(osv.osv):
    _inherit = "sale.order"
    
    def action_wait(self, cr, uid, ids, context=None):
        context = context or {}
        Invoice_pool = self.pool.get('account.invoice')
        Inv_line_pool = self.pool.get('account.invoice.line')
        Journal_pool = self.pool.get('account.journal')
        account_pool = self.pool.get('account.account')
        for o in self.browse(cr, uid, ids):
            if o.warehouse_id.partner_id.company_id.id != o.warehouse_id.company_id.id:
#                if o.warehouse_id.partner_id and o.warehouse_id.partner_id.is_company == True:
#                    account_id = o.warehouse_id.partner_id.property_account_payable.id
                    
#                    payment_term = o.warehouse_id.partner_id.property_supplier_payment_term.id
#                elif o.warehouse_id.partner_id and o.warehouse_id.partner_id.is_company == False:
#                    account_id = o.warehouse_id.partner_id.parent_id.property_account_payable.id
                    
 #                   payment_term = o.warehouse_id.partner_id.parent_id.property_supplier_payment_term.id
                
                account_id = account_pool.search(cr, uid, [('company_id', '=', o.warehouse_id.company_id.id), ('type', '=', 'payable')])
                
                journal_id = Journal_pool.search(cr, uid, [('type', '=', 'purchase'), ('company_id', '=', o.warehouse_id.company_id.id)])
                print '\n acc and journal',account_id,journal_id
                sup_inv_vals = {
                    'partner_id': o.warehouse_id.partner_id.id,
                    'currency_id': o.pricelist_id.currency_id.id,
                    'company_id': o.warehouse_id.company_id.id,
                    'account_id': account_id and account_id[0] or False,
                    'journal_id': journal_id and journal_id[0] or False,
                    'user_id': o.user_id.id,
                    'origin': o.name,
                    'type': 'in_invoice',
#                    'payment_term': payment_term,
                }
                sup_inv_id = Invoice_pool.create(cr, uid, sup_inv_vals)
                print '\n supplier inv',sup_inv_id,sup_inv_vals,journal_id
                for sale_line in o.order_line:
                    tax_list = []
                    for tax in sale_line.product_id.supplier_taxes_id:
                        tax_list.append(tax.id)
                    inv_line_vals = {
                        'product_id': sale_line.product_id.id,
                        'name': sale_line.name,
                        'quantity': sale_line.product_uom_qty,
                        'uos_id': sale_line.product_uom.id,
                        'account_id': account_id and account_id[0] or False,
                        'price_unit': sale_line.product_id.standard_price,
                        'invoice_id': sup_inv_id,
#                        'discount': sale_line.discount,
                        'invoice_line_tax_id': [(6, 0, tax_list)],
                    }
                    print '\n supplier inv line',inv_line_vals
                    Inv_line_pool.create(cr, uid, inv_line_vals)
                
            if not o.order_line:
                raise osv.except_osv(_('Error!'),_('You cannot confirm a sales order which has no line.'))
            noprod = self.test_no_product(cr, uid, o, context)
            if (o.order_policy == 'manual') or noprod:
                self.write(cr, uid, [o.id], {'state': 'manual', 'date_confirm': fields.date.context_today(self, cr, uid, context=context)})
            else:
                self.write(cr, uid, [o.id], {'state': 'progress', 'date_confirm': fields.date.context_today(self, cr, uid, context=context)})
            self.pool.get('sale.order.line').button_confirm(cr, uid, [x.id for x in o.order_line])
        return True    
    
