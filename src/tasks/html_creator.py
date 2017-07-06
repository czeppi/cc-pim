# Copyright (C) 2017  Christian Czepluch
#
# This file is part of CC-PIM.
#
# CC-PIM is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# CC-PIM is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with CC-PIM.  If not, see <http://www.gnu.org/licenses/>.

import xml.etree.ElementTree as ET
from tasks.page import Page, Header, Paragraph, List, ListItem, Table, Column, Row, Cell
from tasks.page import NormalText, BoldText, Link, Image
from tasks.page import HAlign, Width


def write_htmlstr(page: Page) -> str:
    html_root = _HtmlCreator(page).create()
    return ET.tostring(html_root, encoding='unicode')


class _HtmlCreator:

    def __init__(self, page: Page):
        self._page = page

    def create(self) -> ET.Element:
        html_page = ET.fromstring('<p></p>')
        for block_element in self._page.block_elements:
            self._add_html_block_element(html_page, block_element)
        return html_page

    def _add_html_block_element(self, html_page, block_element):
        if isinstance(block_element, Header):
            self._add_html_header(html_page, block_element)
        elif isinstance(block_element, Paragraph):
            self._add_html_paragraph(html_page, block_element)
        elif isinstance(block_element, List):
            self._add_html_list(html_page, block_element)
        elif isinstance(block_element, Table):
            self._add_html_table(html_page, block_element)

    def _add_html_header(self, html_parent, header):
        html_header = ET.SubElement(html_parent, f'h{header.level}')
        self._add_html_inline_elements(html_header, header.inline_elements)

    def _add_html_paragraph(self, html_parent, paragraph):
        html_para = ET.SubElement(html_parent, 'p')
        self._add_html_inline_elements(html_para, paragraph.inline_elements)

    def _add_html_list(self, html_parent, list_):
        html_list = ET.SubElement(html_parent, 'ul')
        for list_item in list_.items:
            self._add_html_listitem(html_list, list_item)

    def _add_html_listitem(self, html_parent, list_item):
        html_list_item = ET.SubElement(html_parent, 'li')

        inline_elements = list_item.inline_elements
        if list_item.symbol == '=>':
            if len(inline_elements) > 0 and isinstance(inline_elements[0], NormalText):
                inline_elements[0] = NormalText('=> ' + inline_elements[0].text)
            else:
                inline_elements = [NormalText('=> ')] + inline_elements
        self._add_html_inline_elements(html_list_item, inline_elements)
        for sub_item in list_item.sub_items:
            html_list = ET.SubElement(html_list_item, 'ul')
            self._add_html_listitem(html_list, sub_item)

    def _add_html_table(self, html_parent, table):
        html_table = ET.SubElement(html_parent, 'table')
        html_thead = ET.SubElement(html_table, 'thead')
        html_tbody = ET.SubElement(html_table, 'tbody')
        for col in table.columns:
            self._add_html_th(html_thead, col)
        for row in table.rows:
            self._add_html_tr(html_tbody, row)

    def _add_html_th(self, html_parent, column):
        html_th = ET.SubElement(html_parent, 'th', align=str(column.halign.name))
        html_th.text = column.text

    def _add_html_tr(self, html_parent, row):
        html_tr = ET.SubElement(html_parent, 'tr')
        for cell in row.cells:
            self._add_html_td(html_tr, cell)

    def _add_html_td(self, html_tr, cell):
        html_td = ET.SubElement(html_tr, 'td')
        self._add_html_inline_elements(html_td, cell.inline_elements)

    def _add_html_inline_elements(self, html_block_element, inline_elements):
        html_block_element.text = ''
        if len(inline_elements) == 0:
            return

        start_index = 0
        inline_element0 = inline_elements[0]
        if isinstance(inline_element0, NormalText):
            html_block_element.text = inline_element0.text
            start_index = 1

        k = start_index
        while k < len(inline_elements):
            inline_element = inline_elements[k]
            html_inline_element = self._add_html_inline_element(html_block_element, inline_element)
            if k + 1 < len(inline_elements):
                next_inline_element = inline_elements[k+1]
                if isinstance(next_inline_element, NormalText):
                    html_inline_element.tail = next_inline_element.text
                    k += 1
            k += 1

    def _add_html_inline_element(self, html_block_element, inline_element):
        if isinstance(inline_element, BoldText):
            return self._add_html_bold(html_block_element, inline_element)

    def _add_html_bold(self, html_parent, bold_text):
        html_bold = ET.SubElement(html_parent, 'b')
        html_bold.text = bold_text.text
        return html_bold







