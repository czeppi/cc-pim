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
from typing import Iterator, Iterable

from tasks.page import HAlign
from tasks.page import NormalText, BoldText, Link, Image
from tasks.page import Page, Header, Paragraph, List, ListItem, Table, Row, Cell, BlockElement, InlineElement


def write_markup(page: Page) -> str:
    return _MarkupCreator(page).create()


class _MarkupCreator:
    def __init__(self, page: Page):
        self._page = page

    def create(self) -> str:
        lines = list(self._iter_page_lines(self._page))
        while len(lines) > 0 and lines[-1] == '':
            del lines[-1]
        lines.append('')
        return '\n'.join(lines)

    def _iter_page_lines(self, page: Page) -> Iterator[str]:
        for block_elem in page.block_elements:
            yield from self._iter_block_element_lines(block_elem)
            yield ''

    def _iter_block_element_lines(self, block_element: BlockElement) -> Iterator[str]:
        if isinstance(block_element, Header):
            yield from self._iter_header_lines(block_element)
        elif isinstance(block_element, Paragraph):
            yield from self._iter_paragraph_lines(block_element)
        elif isinstance(block_element, List):
            yield from self._iter_list_lines(block_element)
        elif isinstance(block_element, Table):
            yield from self._iter_table_lines(block_element)

    def _iter_header_lines(self, header: Header) -> Iterator[str]:
        header_text = self._create_inline_elements_str(header.inline_elements)
        assert '\n' not in header_text
        yield header.level * '#' + ' ' + header_text

    def _iter_paragraph_lines(self, paragraph: Paragraph) -> Iterator[str]:
        para_text = self._create_inline_elements_str(paragraph.inline_elements)
        for para_line in para_text.split('\n'):
            yield para_line  # .strip()

    def _iter_list_lines(self, list_: List) -> Iterator[str]:
        for item in list_.items:
            yield from self._iter_list_item_lines(item, indent_len=0)

    def _iter_list_item_lines(self, list_item: ListItem, indent_len: int) -> Iterator[str]:
        item_text = self._create_inline_elements_str(list_item.inline_elements)
        symbol = list_item.symbol
        symbol_ws = ' ' * len(symbol)
        for k, item_line in enumerate(item_text.split('\n')):
            yield indent_len * ' ' + (symbol if k == 0 else symbol_ws) + ' ' + item_line
            for sub_item in list_item.sub_items:
                yield from self._iter_list_item_lines(sub_item, indent_len + len(symbol) + 1)

    def _iter_table_lines(self, table: Table) -> Iterator[str]:
        yield '|' + '|'.join(self._create_col_str(col) for col in table.columns) + '|'
        for row in table.rows:
            yield self._create_row_line(row)

    @staticmethod
    def _create_col_str(col):
        if col.halign == HAlign.left:
            return col.text + ' '
        elif col.halign == HAlign.right:
            return ' ' + col.text
        elif col.halign == HAlign.center:
            return ' ' + col.text + ' '

    def _create_row_line(self, row: Row) -> str:
        return '|' + '|'.join(self._create_cell_str(cell) for cell in row.cells) + '|'

    def _create_cell_str(self, cell: Cell) -> str:
        cell_text = self._create_inline_elements_str(cell.inline_elements)
        assert '\n' not in cell_text
        return cell_text

    def _create_inline_elements_str(self, inline_elements: Iterable[InlineElement]) -> str:
        text_parts = list(self._create_inline_element_str(x) for x in inline_elements)
        return ''.join(text_parts)

    def _create_inline_element_str(self, inline_elem: InlineElement) -> str:
        if isinstance(inline_elem, NormalText):
            return self._create_normal_text_str(inline_elem)
        if isinstance(inline_elem, BoldText):
            return self._create_bold_str(inline_elem)
        elif isinstance(inline_elem, Link):
            return self._create_link_str(inline_elem)
        elif isinstance(inline_elem, Image):
            return self._create_image_str(inline_elem)
        else:
            raise Exception(str(inline_elem))

    @staticmethod
    def _create_normal_text_str(normal_text: NormalText) -> str:
        return normal_text.text

    @staticmethod
    def _create_bold_str(bold: BoldText) -> str:
        return '*' + bold.text + '*'

    @staticmethod
    def _create_link_str(link: Link) -> str:
        return f'[link: url={link.url}, text={link.text}]'

    @staticmethod
    def _create_image_str(image: Image) -> str:
        return f'[image: url={image.path}, width={image.width}]'
