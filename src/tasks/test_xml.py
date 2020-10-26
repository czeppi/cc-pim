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

import unittest

from tasks.page import HAlign, BlockElement
from tasks.page import NormalText, BoldText
from tasks.page import Page, Header, Paragraph, List, ListItem, Table, Column, Row, Cell
from tasks.xml_reader import read_from_xmlstr
from tasks.xml_write import write_xmlstr


class TestXml(unittest.TestCase):

    def test_header(self):
        self._test_one_element(
            Header(level=1, inline_elements=[NormalText('aaa')]),
            '<header level="1">aaa</header>'
        )

    def test_paragraph(self):
        self._test_one_element(
            Paragraph([NormalText('aaa')]),
            '<paragraph>aaa</paragraph>'
        )

    def test_preformatted_paragraph(self):
        self._test_one_element(
            Paragraph([NormalText('aaa')], preformatted=True),
            '<paragraph preformatted="true">aaa</paragraph>'
        )

    def test_bold(self):
        self._test_one_element(
            Paragraph([NormalText('aaa'), BoldText('bbb'), NormalText('ccc')]),
            '<paragraph>aaa<bold>bbb</bold>ccc</paragraph>'
        )

    def test_simple_list(self):
        self._test_one_element(
            List([ListItem([NormalText('aaa')])]),
            '<list><item>aaa</item></list>'
        )

    def test_preformatted_list_item(self):
        self._test_one_element(
            List([ListItem([NormalText('aaa')], preformatted=True)]),
            '<list><item preformatted="true">aaa</item></list>'
        )

    def test_list_with_non_default_symbol(self):
        self._test_one_element(
            List([ListItem([NormalText('aaa')], symbol='a.')]),
            '<list><item symbol="a.">aaa</item></list>'
        )

    def test_list_with_sublist(self):
        self._test_one_element(
            List([
                ListItem(
                    inline_elements=[NormalText('aaa'), BoldText('bbb'), NormalText('ccc')],
                    sub_items=[
                        ListItem([NormalText('ddd')])
                    ]
                )
            ]),
            '<list>'
            '<item>aaa<bold>bbb</bold>ccc'
            '<item>ddd</item>'
            '</item>'
            '</list>'
        )
    def test_table(self):
        self._test_one_element(
            Table(columns=[Column(halign=HAlign.LEFT, text='A'),
                           Column(halign=HAlign.RIGHT, text='B')],
                  rows=[Row([Cell([NormalText('aaa')]),
                             Cell([NormalText('bbb')])])]),
            '<table>'
            '<column halign="left">A</column>' 
            '<column halign="right">B</column>'
            '<row><cell>aaa</cell><cell>bbb</cell></row>'
            '</table>'
        )

    def _test_one_element(self, page_elem1: BlockElement, xml_elem_str1: str):
        page1 = Page([page_elem1])
        xml_str1 = '<page>' + xml_elem_str1 + '</page>'

        page2 = read_from_xmlstr(xml_str1)
        self.assertEqual(page2, page1)

        xml_str2 = write_xmlstr(page1)
        # self.assertEqual(xml_str2, xml_str1)  # too difficult, to get exact the same string

        page3 = read_from_xmlstr(xml_str2)
        self.assertEqual(page3, page1)
