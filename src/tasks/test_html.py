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
from tasks.page import Page, Header, Paragraph, List, ListItem, Table, Column, Row, Cell
from tasks.page import NormalText, BoldText, Link, Image
from tasks.page import HAlign, Width
from tasks.html_creator import write_htmlstr


class TestHtml(unittest.TestCase):

    def test_header(self):
        self._test_one_element(
            Header(level=1, inline_elements=[NormalText('aaa')]),
            '<h1>aaa</h1>'
        )

    def test_simple_paragraph(self):
        self._test_one_element(
            Paragraph([NormalText('aaa')]),
            '<p>aaa</p>'
        )

    def test_preformatted_paragraph(self):
        self._test_one_element(
            Paragraph([NormalText('  aaa\n  bbb')], preformatted=True),
            '<pre>  aaa\n  bbb</pre>'
        )

    def test_bold(self):
        self._test_one_element(
            Paragraph([NormalText('aaa'), BoldText('bbb'), NormalText('ccc')]),
            '<p>aaa<b>bbb</b>ccc</p>'
        )

    def test_list(self):
        self._test_one_element(
            List([ ListItem([ NormalText('aaa') ]) ]),
            '<ul><li>aaa</li></ul>'
        )

    def test_nested_list(self):
        self._test_one_element(
            List([
                ListItem([ NormalText('aaa') ],
                         sub_items=[ListItem([NormalText('bbb')])])
            ]),
            '<ul>'
              '<li>aaa'
                '<ul>'
                  '<li>bbb</li>'
                '</ul>'
              '</li>'
            '</ul>'
        )

    def test_list_with_arrow(self):
        self._test_one_element(
            List([ ListItem([NormalText('aaa')]),
                   ListItem([NormalText('bbb')], symbol='=>')]),
            '<ul><li>aaa</li><li>=&gt; bbb</li></ul>'
        )

    def test_preformatted_list(self):
        self._test_one_element(
            List([ ListItem( [NormalText('  aaa\n  bbb')], preformatted=True) ]),
            '<ul><li><pre>  aaa</pre><pre>  bbb</pre></li></ul>'
        )

    def test_table(self):
        self._test_one_element(
            Table(columns=[ Column(halign=HAlign.left,  text='A'),
                            Column(halign=HAlign.right, text='B') ],
                  rows=[ Row([ Cell([NormalText('aaa')]),
                               Cell([NormalText('bbb')]) ]) ]),
            '<table>'
              '<thead>'
                '<th align="left">A</th>' '<th align="right">B</th>'
              '</thead>'
              '<tbody>'
                '<tr>' + '<td>aaa</td>' '<td>bbb</td>' '</tr>'
              '</tbody>'
            '</table>'
        )

    def _test_one_element(self, page_elem1, html_elem_str1: str):
        page1 = Page([page_elem1])
        html_str1 = '<html>' + html_elem_str1 + '</html>'

        html_str2 = write_htmlstr(page1)
        self.assertEqual(html_str2, html_str1)
