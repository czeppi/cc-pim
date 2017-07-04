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

    def test_paragraph(self):
        self._test_one_element(
            Paragraph([NormalText('aaa')]),
            '<p>aaa</p>'
        )

    def test_bold(self):
        self._test_one_element(
            Paragraph([NormalText('aaa'), BoldText('bbb'), NormalText('ccc')]),
            '<p>aaa<b>bbb</b>ccc</p>'
        )

    def test_list(self):        self._test_one_element(
            List([ ListItem([ NormalText('aaa') ]) ]),
            '<ul><li>aaa</li></ul>'
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
        html_str1 = '<p>' + html_elem_str1 + '</p>'

        html_str2 = write_htmlstr(page1)
        self.assertEqual(html_str2, html_str1)
