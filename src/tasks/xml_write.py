import xml.etree.ElementTree as ET
from tasks.page import Page, Header, Paragraph, List, ListItem, Table, Column, Row, Cell
from tasks.page import NormalText, BoldText, Link, Image
from tasks.page import HAlign, Width


def write_xmlstr(page: Page) -> str:
    xml_root = _XmlCreator(page).create()
    return ET.tostring(xml_root, encoding='unicode')


def create_xmlroot(page: Page) -> ET.Element:
    return _XmlCreator(page).create()


class _XmlCreator:

    def __init__(self, page: Page):
        self._page = page

    def create(self) -> ET.Element:
        xml_page = ET.fromstring('<page></page>')
        for block_element in self._page.block_elements:
            self._add_xml_block_element(xml_page, block_element)
        return xml_page

    def _add_xml_block_element(self, xml_page, block_element):
        if isinstance(block_element, Header):
            self._add_xml_header(xml_page, block_element)
        elif isinstance(block_element, Paragraph):
            self._add_xml_paragraph(xml_page, block_element)
        elif isinstance(block_element, List):
            self._add_xml_list(xml_page, block_element)
        elif isinstance(block_element, Table):
            self._add_xml_table(xml_page, block_element)

    def _add_xml_header(self, xml_parent, header):
        xml_header = ET.SubElement(xml_parent, 'header', level=str(header.level))
        self._add_xml_inline_elements(xml_header, header.inline_elements)

    def _add_xml_paragraph(self, xml_parent, paragraph):
        xml_para = ET.SubElement(xml_parent, 'paragraph')
        self._add_xml_inline_elements(xml_para, paragraph.inline_elements)

    def _add_xml_list(self, xml_parent, list_):
        xml_list = ET.SubElement(xml_parent, 'list')
        for list_item in list_.items:
            self._add_xml_listitem(xml_list, list_item)

    def _add_xml_listitem(self, xml_parent, list_item):
        xml_list_item = ET.SubElement(xml_parent, 'item')
        self._add_xml_inline_elements(xml_list_item, list_item.inline_elements)
        for sub_item in list_item.sub_items:
            self._add_xml_listitem(xml_list_item, sub_item)

    def _add_xml_table(self, xml_parent, table):
        xml_table = ET.SubElement(xml_parent, 'table')
        for col in table.columns:
            self._add_xml_column(xml_table, col)
        for row in table.rows:
            self._add_xml_row(xml_table, row)

    def _add_xml_column(self, xml_parent, column):
        xml_col = ET.SubElement(xml_parent, 'column', halign=str(column.halign.name))
        xml_col.text = column.text

    def _add_xml_row(self, xml_parent, row):
        xml_row = ET.SubElement(xml_parent, 'row')
        for cell in row.cells:
            self._add_xml_cell(xml_row, cell)

    def _add_xml_cell(self, xml_parent, cell):
        xml_cell = ET.SubElement(xml_parent, 'cell')
        self._add_xml_inline_elements(xml_cell, cell.inline_elements)

    def _add_xml_inline_elements(self, xml_block_element, inline_elements):
        xml_block_element.text = ''
        if len(inline_elements) == 0:
            return

        start_index = 0
        inline_element0 = inline_elements[0]
        if isinstance(inline_element0, NormalText):
            xml_block_element.text = inline_element0.text
            start_index = 1

        k = start_index
        while k < len(inline_elements):
            inline_element = inline_elements[k]
            xml_inline_element = self._add_xml_inline_element(xml_block_element, inline_element)
            if k + 1 < len(inline_elements):
                next_inline_element = inline_elements[k+1]
                if isinstance(next_inline_element, NormalText):
                    xml_inline_element.tail = next_inline_element.text
                    k += 1
            k += 1

    def _add_xml_inline_element(self, xml_block_element, inline_element):
        if isinstance(inline_element, BoldText):
            return self._add_xml_bold(xml_block_element, inline_element)

    def _add_xml_bold(self, xml_parent, bold_text):
        xml_bold = ET.SubElement(xml_parent, 'bold')
        xml_bold.text = bold_text.text
        return xml_bold






