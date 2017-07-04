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
import xml.etree.ElementTree as ET
from tasks.markup_reader import read_markup
from tasks.markup_writer import write_markup
from tasks.page import Page, Header, Paragraph, List, ListItem, Table, Column, Row, Cell
from tasks.page import NormalText, BoldText, Link, Image
from tasks.page import HAlign, Width


class TestMarkup(unittest.TestCase):

    def test_header(self):
        self._test(
            Header(level=1, inline_elements=[NormalText('title')]),
            '# title\n')


    def test_list(self):
        self._test(
            List([ ListItem(inline_elements=[NormalText('aaa')]) ]),
            '- aaa\n')

    def test_sublist(self):
        self._test(
            List([
               ListItem(
                   inline_elements=[NormalText('aaa')],
                   sub_items=[
                       ListItem([NormalText('bbb')])
                   ])
            ]),
            '- aaa\n'
            '  - bbb\n')

    def test_list_with_2lines_item(self):
        self._test(
            List([
                ListItem(inline_elements=[NormalText('aaa\nbbb')])
            ]),
            '- aaa\n'
            '  bbb\n')

    def test_table(self):
        self._test(
            Table(
                columns=[
                    Column(halign=HAlign.left, text='aaa') ],
                rows=[
                    Row([ Cell( [NormalText('bbb')] ) ])
                ]
            ),
           '|aaa |\n'
           '|bbb|\n')

    def test_paragraph(self):
        self._test(
            Paragraph([ NormalText('aaa') ]),
            'aaa\n')

    def test_two_lines_paragraph(self):
        self._test(
            Paragraph([ NormalText('aaa\nbbb') ]),
            'aaa\n'
            'bbb\n')

    def test_bold(self):
       self._test(
           Paragraph([ NormalText('aaa '), BoldText('bbb'), NormalText(' ccc') ]),
           'aaa *bbb* ccc\n')
                   
    def _test(self, block_element, markup_str1):
        page1 = Page(block_elements=[block_element])
        markup_str1_normed = markup_str1 #+ '\n'

        markup_str2 = write_markup(page1)
        self.assertEqual(markup_str2, markup_str1_normed)

        page2 = read_markup(markup_str1)
        self.assertEqual(page2, page1)

