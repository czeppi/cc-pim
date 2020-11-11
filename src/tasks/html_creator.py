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

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from typing import Optional, List as TList, Iterator, Iterable, Tuple

from tasks.page import NormalText, BoldText, Link
from tasks.page import Page, Header, Paragraph, List, ListItem, Table, Column, Row, Cell, BlockElement, InlineElement
from tasks.taskmodel import TaskModel


def write_htmlstr(title: str, page: Page,
                  link_solver: Optional[LinkSolver] = None,
                  search_rex: Optional[re.Pattern] = None) -> str:
    html_root = _HtmlCreator(title, page, link_solver, search_rex).create()
    return ET.tostring(html_root, encoding='unicode')


class _HtmlCreator:

    def __init__(self, title: str, page: Page,
                 link_solver: Optional[LinkSolver], search_rex: Optional[re.Pattern]):
        self._title = title
        self._page = page
        self._link_solver = link_solver
        self._search_rex = search_rex

    def create(self) -> ET.XML:
        html_page: ET.XML = ET.fromstring('<html></html>')

        if self._title:
            self._add_html_header(html_page, Header(level=0, inline_elements=[NormalText(self._title)]))

        for block_element in self._page.block_elements:
            self._add_html_block_element(html_page, block_element)
        return html_page

    def _add_html_block_element(self, html_page: ET.XML, block_element: BlockElement) -> None:
        if isinstance(block_element, Header):
            self._add_html_header(html_page, block_element)
        elif isinstance(block_element, Paragraph):
            self._add_html_paragraph(html_page, block_element)
        elif isinstance(block_element, List):
            self._add_html_list(html_page, block_element)
        elif isinstance(block_element, Table):
            self._add_html_table(html_page, block_element)

    def _add_html_header(self, html_parent, header: Header) -> None:
        html_header = ET.SubElement(html_parent, f'h{header.level + 1}')
        self._add_html_inline_elements(html_header, header.inline_elements)

    def _add_html_paragraph(self, html_parent, paragraph: Paragraph) -> None:
        if paragraph.preformatted:
            html_pre = ET.SubElement(html_parent, 'pre')
            self._add_html_inline_elements(html_pre, paragraph.inline_elements)
        else:
            html_para = ET.SubElement(html_parent, 'p')
            self._add_html_inline_elements(html_para, paragraph.inline_elements)

    def _add_html_list(self, html_parent, list_: List) -> None:
        html_list = ET.SubElement(html_parent, 'ul')
        for list_item in list_.items:
            self._add_html_listitem(html_list, list_item)

    def _add_html_listitem(self, html_parent, list_item: ListItem) -> None:
        html_list_item = ET.SubElement(html_parent, 'li')

        inline_elements: TList[InlineElement] = list_item.inline_elements
        if list_item.symbol != '-':
            if len(inline_elements) > 0 and isinstance(inline_elements[0], NormalText):
                inline_elements[0] = NormalText(list_item.symbol + ' ' + inline_elements[0].text)
            else:
                inline_elements = [NormalText(list_item.symbol + ' ')] + inline_elements

        # if list_item.preformatted:
        #     html_cur_item = ET.SubElement(html_list_item, 'pre')
        # else:
        #     html_cur_item = html_list_item
        # self._add_html_inline_elements(html_cur_item, inline_elements)
        if list_item.preformatted:
            self._add_preformatted_html_inline_elements(html_list_item, inline_elements)
        else:
            self._add_html_inline_elements(html_list_item, inline_elements)

        for sub_item in list_item.sub_items:
            # html_list = ET.SubElement(html_cur_item, 'ul')
            html_list = ET.SubElement(html_list_item, 'ul')
            self._add_html_listitem(html_list, sub_item)

    def _add_html_table(self, html_parent, table: Table) -> None:
        html_table = ET.SubElement(html_parent, 'table')

        html_thead = ET.SubElement(html_table, 'thead')
        html_thead_tr = ET.SubElement(html_thead, 'tr')
        for col in table.columns:
            self._add_html_th(html_thead_tr, col)

        html_tbody = ET.SubElement(html_table, 'tbody')
        for row in table.rows:
            self._add_html_tr(html_tbody, row)

    @staticmethod
    def _add_html_th(html_parent, column: Column) -> None:
        html_th = ET.SubElement(html_parent, 'th', align=column.halign.name.lower())
        html_th.text = column.text

    def _add_html_tr(self, html_parent, row: Row) -> None:
        html_tr = ET.SubElement(html_parent, 'tr')
        for cell in row.cells:
            self._add_html_td(html_tr, cell)

    def _add_html_td(self, html_tr, cell: Cell) -> None:
        html_td = ET.SubElement(html_tr, 'td')
        self._add_html_inline_elements(html_td, cell.inline_elements)

    def _add_html_inline_elements(self, html_parent_element, inline_elements: TList[InlineElement]) -> None:
        if self._search_rex:
            transformer = InlineElementTransformer(self._search_rex)
            inline_elements = transformer.transform(inline_elements)

        html_parent_element.text = ''
        if len(inline_elements) == 0:
            return

        start_index = 0
        inline_element0 = inline_elements[0]
        if isinstance(inline_element0, NormalText) and not inline_element0.class_attr:
            html_parent_element.text = inline_element0.text
            start_index = 1

        k = start_index
        while k < len(inline_elements):
            inline_element = inline_elements[k]
            html_inline_element = self._add_html_inline_element(html_parent_element, inline_element)
            if k + 1 < len(inline_elements):
                next_inline_element = inline_elements[k + 1]
                if isinstance(next_inline_element, NormalText):
                    html_inline_element.tail = next_inline_element.text
                    k += 1
            k += 1

    def _add_preformatted_html_inline_elements(self, html_block_element, inline_elements: TList[InlineElement]) -> None:
        html_block_element.text = ''

        for elements_in_line in self._iter_inline_elements_per_line(inline_elements):
            html_pre = ET.SubElement(html_block_element, 'pre')
            self._add_html_inline_elements(html_pre, elements_in_line)

    @staticmethod
    def _iter_inline_elements_per_line(inline_elements: TList[InlineElement]) -> Iterator[TList[InlineElement]]:
        elements_in_line = []
        for inline_element in inline_elements:
            text = getattr(inline_element, 'text', None)
            if text is None:
                elements_in_line.append(inline_element)
            else:
                lines = text.split('\n')
                n = len(lines)
                if n == 1:
                    elements_in_line.append(inline_element)
                elif n > 1:
                    for line in lines[:-1]:
                        new_element = inline_element.copy()
                        new_element.text = line
                        elements_in_line.append(new_element)
                        yield elements_in_line
                        elements_in_line = []
                    new_element = inline_element.copy()
                    new_element.text = lines[-1]
                    elements_in_line.append(new_element)
        if len(elements_in_line) > 0:
            yield elements_in_line

    def _add_html_inline_element(self, html_block_element, inline_element: InlineElement) -> ET.SubElement:
        if isinstance(inline_element, BoldText):
            return self._add_html_bold(html_block_element, inline_element)
        elif isinstance(inline_element, Link):
            return self._add_html_link(html_block_element, inline_element)
        elif isinstance(inline_element, NormalText):
            return self._add_html_div(html_block_element, inline_element)
        else:
            raise Exception(type(inline_element))

    @staticmethod
    def _add_html_div(html_parent, normal_text: NormalText) -> ET.SubElement:
        attrib = {}
        if normal_text.class_attr:
            attrib['class'] = normal_text.class_attr
        html_div = ET.SubElement(html_parent, 'div', attrib=attrib)
        html_div.text = normal_text.text
        return html_div

    @staticmethod
    def _add_html_bold(html_parent, bold_text: BoldText) -> ET.SubElement:
        html_bold = ET.SubElement(html_parent, 'b')
        html_bold.text = bold_text.text
        if bold_text.class_attr:
            html_bold.attrib['class'] = bold_text.class_attr
        return html_bold

    def _add_html_link(self, html_parent, link: Link) -> ET.SubElement:
        html_link = ET.SubElement(html_parent, 'a', href=link.uri)
        if link.text:
            html_link.text = link.text
        elif self._link_solver is not None:
            html_link.text = self._link_solver.get_link_text(link.uri)
        else:
            html_link.text = link.uri

        if link.class_attr:
            html_link.attrib['class'] = link.class_attr
        return html_link


class LinkSolver:
    _TASK_REX = re.compile(r"task(?P<serial>[0-9]+)")

    def __init__(self, task_model: TaskModel):
        self._task_model = task_model

    def get_link_text(self, uri: str) -> str:
        match = self._TASK_REX.match(uri)
        if match:
            task_serial = int(match.group('serial'))
            task = self._task_model.get_task(task_serial)
            return task.get_header()
        return uri


class InlineElementTransformer:

    def __init__(self, search_rex: re.Pattern):
        self._search_rex = search_rex

    def transform(self, inline_elements: Iterable[InlineElement]
                  ) -> TList[InlineElement]:
        return list(self._iter_transformed(inline_elements))

    def _iter_transformed(self, inline_elements: Iterable[InlineElement]
                          ) -> Iterator[InlineElement]:
        for elem in inline_elements:
            if elem.text:
                for text_part, marked in self._iter_text_parts(elem.text):
                    new_elem = elem.copy()
                    new_elem.text = text_part
                    new_elem.class_attr = 'search_text' if marked else None
                    yield new_elem
            else:
                yield elem.copy()

    def _iter_text_parts(self, text: str) -> Iterator[Tuple[str, bool]]:
        i = 0
        for match in self._search_rex.finditer(text):
            a, b = match.span()
            if a > i:
                yield text[i:a], False
            yield text[a: b], True
            i = b
        if i < len(text):
            yield text[i:], False
