# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2011 Enapps LTD (<http://www.enapps.co.uk>).
#    All Rights Reserved
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import time
from openerp.report import report_sxw
from openerp import pooler
from account.report.common_report_header import common_report_header
from sm_kit import groupe_digits


class account_fstr_report(report_sxw.rml_parse, common_report_header):

    _name = 'account_fstr.category.report'

    date_end = None
    root_node_obj = None

    def __init__(self, cr, uid, name, context):
        super(account_fstr_report, self).__init__(cr, uid, name, context)
        self.root_node_obj = pooler.get_pool(cr.dbname).get('account_fstr.category').browse(cr, uid, context.get('account_fstr_root_node', context['active_id']), context=context)
        self.category_pool = pooler.get_pool(cr.dbname).get('account_fstr.category')
        ids = context['active_ids']
        self.localcontext.update({
            'time': time,
            'template_data':  self._get_template_data(cr, uid, ids, [], self.root_node_obj.id, context=context),
            'date_end': '',
        })

    def _get_root_id(self):
        if self.root_node_obj:
            return self.root_node_obj
        else:
            return None

    def _get_template_data(self, cr, uid, ids, statements, category_id, context={}):
        category_obj = self.category_pool.browse(cr, uid, category_id, context=context)
        name = category_obj.name
        result = [self._get_statement(cr, uid, ids, [], self._get_root_id(), -1, context=context), self._get_root_id().balance]
        return {
            'name': name,
            'statements': result,
            'lang': context['lang'],
        }


    def _get_statement(self, cr, uid, ids, statements_list, category_obj, parent_indent, context={}):
        indent = category_obj.indent_title + parent_indent
        font_name_title = 'Helvetica'
        font_name_end = 'Helvetica'
        decoratation_underline_title = 'none'
        decoratation_underline_end = 'none'
        decoration_bold_end = 'none'
        decoration_bold_title = 'none'

        # Category Name - italic
        if category_obj.italic_title:
            font_name_title = 'italic'

        # Category text_decoration -underline
        if category_obj.underline_title:
            decoratation_underline_title = 'underline'

        # Category text-bold -bold
        if category_obj.bold_title:
            decoration_bold_title = 'bold'

        # Category End Name -italic
        if category_obj.italic_end:
            font_name_end = 'italic'

        # Category end text-decoration -underline
        if category_obj.underline_end:
            decoratation_underline_end = 'underline'

        # Category end text-bold -bold
        if category_obj.bold_title:
            decoration_bold_end = 'bold'

        total_amount = 0
        internal_statements = []

        if category_obj.state == 'normal':
            for account_statement_obj in category_obj.account_ids:
                account_total_amount = account_statement_obj.balance

                # skip iterations where amount = 0 and hide_zero box ticked
                if 'hide_zero' in context:
                    hide_zero = int(context['hide_zero'])
                    if hide_zero == 1 and account_total_amount == 0.0:
                        continue

                if category_obj.inversed_sign:
                    account_total_amount = -account_total_amount

                internal_statements.append({
                    'name': "%s\t%s" % (account_statement_obj.code, account_statement_obj.name,),
                    'indent': indent + 10,
                    'top_spacing': None,
                    'bottom_spacing': None,
                    'font_name': 'Helvetica',
                    'underline': False,
                    'total_amount': account_total_amount,
                    'decoration': 'none',
                    'decoration_bold': 'none',
                    'padding': 2,
                    'category_title': 'true',
                    'background': '#FFFFFF',
                })
                total_amount += account_total_amount
            internal_statements = sorted(internal_statements, key=lambda statement: statement['name'])

        elif category_obj.state != 'normal':
            for child_category in sorted(category_obj.child_id, key=lambda child_obj: child_obj.sequence):
                internal_statements = self._get_statement(cr, uid, ids, internal_statements, child_category, indent, context=context)
            total_amount = category_obj.balance
            if category_obj.inversed_sign:
                total_amount = -total_amount
        # Category Title
        if category_obj.display_heading:
            statements_list.append({
                'name': category_obj.name,
                'indent': category_obj.indent_title + category_obj.top_spacing_title,
                'top_spacing': category_obj.top_spacing_title,
                'bottom_spacing': category_obj.bottom_spacing_title,
                'font_name': font_name_title,
                'underline': category_obj.underline_title,
                'total_amount': total_amount if category_obj.consolidate_total else 0,
                'decoration': decoratation_underline_title,
                'decoration_bold': decoration_bold_title,
                'padding': 2,
                'category_title': 'false',
                'background': '#F0F0F0',
            })
        if not category_obj.consolidate_total:
            statements_list.extend(internal_statements)
        # Category End Name
        if category_obj.display_total:
            statements_list.append({
                'name': category_obj.name_end,
                'indent': category_obj.indent_end,
                'top_spacing': category_obj.top_spacing_end,
                'bottom_spacing': category_obj.bottom_spacing_end,
                'font_name': font_name_end,
                'underline': category_obj.underline_end,
                'total_amount': total_amount,
                'decoration': decoratation_underline_end,
                'decoration_bold': decoration_bold_end,
                'padding': 10,
                'category_title': 'true',
                'background': '#FFFFFF',
            })
        return statements_list

report_sxw.report_sxw(
    'report.account_financial_report.report',
    'account_fstr.category',
    'account_financial_report_engine/reports/account_financial_report_engine.mako',
    parser=account_fstr_report
)
