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
# Programm erhalten haben. Wenn nicht, siehe <http://www.gnu.org/licenses/>.

import xml.etree.ElementTree as ET
from tasks.page import Page, Header, Paragraph, List, ListItem, Table, Column, Row, Cell
from tasks.page import NormalText, BoldText, Link, Image
from tasks.page import HAlign, Width


def read_from_xmlstr(xml_str: str) -> str:
    xml_root = ET.fromstring(xml_str)
    return _XmlReader(xml_root).read()


def read_from_xmlroot(xml_root: ET.Element) -> str:
    return _XmlReader(xml_root).read()


class _XmlReader:

    def __init__(self, xml_root: ET.Element):
        self._xml_root = xml_root

    def read(self):
        return self._create_page(self._xml_root)

    def _create_page(self, xml_root):
        block_elements = list(self._create_block_element(xml_elem) for xml_elem in xml_root)
        return Page(block_elements)

    def _create_block_element(self, xml_element):
        tag = xml_element.tag
        if tag == 'header':
            return self._create_header(xml_element)
        elif tag == 'paragraph':
            return self._create_paragraph(xml_element)
        elif tag == 'list':
            return self._create_list(xml_element)
        elif tag == 'table':
            return self._create_table(xml_element)

    def _create_header(self, xml_header):
        level = int(xml_header.get('level'))
        inline_elements = list(self._iter_inline_elements(xml_header))
        return Header(level=level, inline_elements=inline_elements)

    def _create_paragraph(self, xml_para):
        inline_elements = list(self._iter_inline_elements(xml_para))
        return Paragraph(inline_elements)

    def _create_list(self, xml_list):
        items = list(self._iter_list_items(xml_list))
        return List(items)

    def _iter_list_items(self, xml_list_or_item):
        for xml_item in xml_list_or_item:
            inline_elements = list(self._iter_inline_elements(xml_item))
            sub_items = list(self._iter_list_items(xml_item))
            yield ListItem(inline_elements=inline_elements, sub_items=sub_items)

    def _create_table(self, xml_table):
        columns = list(self._iter_columns(xml_table))
        rows = list(self._iter_rows(xml_table))
        return Table(columns=columns, rows=rows)

    def _iter_columns(self, xml_table):
        for xml_col in filter(lambda x: x.tag == 'column', xml_table):
            halign = HAlign[xml_col.get('halign')]
            yield Column(halign=halign, text=xml_col.text)

    def _iter_rows(self, xml_table):
        for xml_row in filter(lambda x: x.tag == 'row', xml_table):
            cells = list(self._iter_cells(xml_row))
            yield Row(cells)

    def _iter_cells(self, xml_row):
        for xml_cell in xml_row:
            inline_elements = list(self._iter_inline_elements(xml_cell))
            yield Cell(inline_elements=inline_elements)

    def _iter_inline_elements(self, xml_element):
        if xml_element.text:
            yield NormalText(xml_element.text)
        for xml_child in xml_element:
            yield self._create_inline_element(xml_child)
            if xml_child.tail:
                yield NormalText(xml_child.tail)

    def _create_inline_element(self, xml_elem):
        tag = xml_elem.tag
        if tag == 'bold':
            return self._create_bold_text(xml_elem)
        elif tag == 'link':
            return self._create_link(xml_elem)
        elif tag == 'image':
            return self._create_image(xml_elem)

    def _create_bold_text(self, xml_bold):
        return BoldText(xml_bold.text)

    def _create_link(self, xml_link):
        path = xml_link.get('path')
        return Link(url=path, text=xml_link.text)

    def _create_image(self, xml_image):
        path = xml_image.get('path')
        width_str = xml_image.get('width')
        if width_str[-1] == '%':
            width = Width(int(width_str[:-1]), relativ=True)
        else:
            width = Width(int(width_str), relative=False)
        return Image(path=path, width=width)
