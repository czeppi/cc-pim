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
        self._test1(
            Header(level=1, inline_elements=[NormalText('title')]),
            '# title\n')

    def test_one_line_paragraph(self):
        self._test1(
            Paragraph([ NormalText('aaa') ]),
            'aaa\n')

    def test_two_lines_paragraph(self):
        self._test1(
            Paragraph([ NormalText('aaa\nbbb') ]),
            'aaa\n'
            'bbb\n')

    def test_two_paragraphs(self):
        self._test_n(
            [
                Paragraph([ NormalText('aaa') ]),
                Paragraph([ NormalText('bbb') ]),
            ],
            'aaa\n'
            '\n'
            'bbb\n')

    def test_preformatted_paragraph(self):
        self._test1(
            Paragraph([ NormalText('  aaa') ], preformatted=True),
            '  aaa\n')

    # def test_paragraph_with_indented_line(self):
    #     self._test(
    #         Paragraph([ NormalText('aaa\n bbb') ]),
    #         'aaa\n'
    #         ' bbb\n')

    def test_list_with_one_item(self):
        self._test1(
            List([ ListItem(inline_elements=[NormalText('aaa')]) ]),
            '- aaa\n')

    def test_list_with_two_items(self):
        self._test1(
            List([
                ListItem(inline_elements=[NormalText('aaa')]),
                ListItem(inline_elements=[NormalText('bbb')]),
            ]),
            '- aaa\n'
            '- bbb\n')

    def test_sublist(self):
        self._test1(
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
        self._test1(
            List([
                ListItem(inline_elements=[NormalText('aaa\nbbb')])
            ]),
            '- aaa\n'
            '  bbb\n')

    def test_list_with_indented_line(self):
        self._test1(
            List([
                ListItem(inline_elements=[NormalText('aaa\n bbb')])
            ]),
            '- aaa\n'
            '   bbb\n')

    def test_list_with_preformatted_lines(self):
        self._test1(
            List([
                ListItem(inline_elements=[NormalText('  aaa\n  bbb')], preformatted=True)
            ]),
            '-   aaa\n'
            '    bbb\n')

    def test_list_with_preformatted_lines2(self):
        self._test1(
            List([
                ListItem(inline_elements=[NormalText('aaa')], preformatted=False),
                ListItem(inline_elements=[NormalText('bbb\nccc\nddd')], preformatted=True)
            ]),
            '- aaa\n'
            '- bbb\n'
            '  ccc\n'
            '  ddd\n')

    def test_list_with_arrow(self):
        self._test1(
            List([
                ListItem(inline_elements=[NormalText('aaa')]),
                ListItem(inline_elements=[NormalText('bbb')], symbol='=>'),
            ]),
            '- aaa\n'
            '=> bbb\n')

    def test_list_with_arrow2(self):
        self._test1(
            List([
                ListItem(inline_elements=[NormalText('aaa\nbbb')], symbol='=>'),
            ]),
            '=> aaa\n'
            '   bbb\n')

    def test_list_with_question_mark(self):
        self._test1(
            List([
                ListItem(inline_elements=[NormalText('aaa')]),
                ListItem(inline_elements=[NormalText('bbb')], symbol='?'),
            ]),
            '- aaa\n'
            '? bbb\n')

    def test_list_with_plus(self):
        self._test1(
            List([
                ListItem(inline_elements=[NormalText('aaa')]),
                ListItem(inline_elements=[NormalText('bbb')], symbol='+'),
            ]),
            '- aaa\n'
            '+ bbb\n')

    def test_list_with_numbers1(self):
        self._test1(
            List([
                ListItem(inline_elements=[NormalText('aaa')], symbol='1.'),
                ListItem(inline_elements=[NormalText('bbb')], symbol='2.'),
            ]),
            '1. aaa\n'
            '2. bbb\n')

    def test_list_with_numbers2(self):
        self._test1(
            List([
                ListItem(inline_elements=[NormalText('aaa')], symbol='1.)'),
                ListItem(inline_elements=[NormalText('bbb')], symbol='2.)'),
            ]),
            '1.) aaa\n'
            '2.) bbb\n')

    def test_list_with_letters1(self):
        self._test1(
            List([
                ListItem(inline_elements=[NormalText('aaa')], symbol='a.'),
                ListItem(inline_elements=[NormalText('bbb')], symbol='b.'),
            ]),
            'a. aaa\n'
            'b. bbb\n')

    def test_list_with_letters2(self):
        self._test1(
            List([
                ListItem(inline_elements=[NormalText('aaa')], symbol='a.)'),
                ListItem(inline_elements=[NormalText('bbb')], symbol='b.)'),
            ]),
            'a.) aaa\n'
            'b.) bbb\n')

    def test_two_lists(self):
        self._test_n(
            [
                List([
                    ListItem(inline_elements=[NormalText('aaa')]),
                ]),
                List([
                    ListItem(inline_elements=[NormalText('bbb')]),
                ]),
            ],
            '- aaa\n'
            '\n'
            '- bbb\n')

    def test_list_and_paragraph(self):
        self._test_n(
            [
                Paragraph([NormalText('aaa\nbbb')]),
                List([
                    ListItem(inline_elements=[NormalText('ccc')]),
                    ListItem(inline_elements=[NormalText('ddd')]),
                ]),
                Paragraph([NormalText('eee\nfff')]),
            ],
            'aaa\n'
            'bbb\n'
            '\n'
            '- ccc\n'
            '- ddd\n'
            '\n'
            'eee\n'
            'fff\n')

    def test_table(self):
        self._test1(
            Table(
                columns=[
                    Column(halign=HAlign.left, text='aaa') ],
                rows=[
                    Row([ Cell( [NormalText('bbb')] ) ])
                ]
            ),
           '|aaa |\n'
           '|bbb|\n')

    def test_bold(self):
       self._test1(
           Paragraph([ NormalText('aaa '), BoldText('bbb'), NormalText(' ccc') ]),
           'aaa *bbb* ccc\n')
                   
    def _test1(self, block_element, markup_str1):
        self._test_n([block_element], markup_str1)

    def _test_n(self, block_elements, markup_str1):
        page1 = Page(block_elements=block_elements)
        markup_str1_normed = markup_str1 #+ '\n'

        markup_str2 = write_markup(page1)
        self.assertEqual(markup_str2, markup_str1_normed)

        page2 = read_markup(markup_str1)
        self.assertEqual(page2, page1)
