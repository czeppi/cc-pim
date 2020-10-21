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
from re import Match
from typing import Iterator, Optional, List as TList

from tasks.page import HAlign, BlockElement, InlineElement
from tasks.page import NormalText, BoldText
from tasks.page import Page, Header, Paragraph, List, ListItem, Table, Column, Row, Cell


def read_markup(markup_str: str) -> Page:
    parser = _MarkupParser(markup_str)
    page = parser.parse()
    return page


class _MarkupParser:

    def __init__(self, markup_text: str):
        self._markup_text = markup_text
        self._list_items_always_preformatted = False  # True

    def parse(self) -> Page:
        block_elements = list(self._iter_block_elements())
        return Page(block_elements)

    def _iter_block_elements(self) -> Iterator[BlockElement]:
        self._line_iter = _LineIterator(self._markup_text)
        while not self._line_iter.stopped:
            for create_func in [self._create_header, self._create_list, self._create_table, self._create_paragraph]:
                new_block_element = create_func()
                if new_block_element is not None:
                    yield new_block_element
                    while not self._line_iter.stopped and self._line_iter.cur_line.is_empty:
                        self._line_iter.get_next_line()
                    break
            else:
                raise MarkupParseError(self._line_iter.cur_line, 'invalid line')

    def _create_header(self) -> Optional[BlockElement]:
        cur_line = self._line_iter.cur_line
        if cur_line is None:
            return None
        header_line = cur_line.create_header_line()
        if header_line is None:
            return None

        self._line_iter.get_next_line()
        self._skip_empty_line()

        inline_parser = InlineParser(header_line.text)
        inline_elements = inline_parser.parse()
        return Header(header_line.level, inline_elements)

    def _create_paragraph(self) -> Optional[Paragraph]:
        cur_line = self._line_iter.cur_line
        if cur_line is None or cur_line.is_empty:
            return None

        lines = []
        while cur_line is not None and not cur_line.is_empty:
            lines.append(cur_line.text)
            cur_line = self._line_iter.get_next_line()
        self._skip_empty_line()

        preformatted = self._are_lines_preformatted(lines)
        para_text = '\n'.join(lines)
        inline_parser = InlineParser(para_text)
        inline_elements = inline_parser.parse()
        return Paragraph(inline_elements, preformatted=preformatted)

    def _skip_empty_line(self) -> None:
        cur_line = self._line_iter.cur_line
        if cur_line is not None and not cur_line.is_empty:
            raise MarkupParseError(cur_line, 'line is not empty')
        self._line_iter.get_next_line()

    @staticmethod
    def _are_lines_preformatted(lines: List[str]) -> bool:
        return any(len(line) > 0 and (line[0] == ' ' or line[-1] == ' ') for line in lines)

    def _create_list(self) -> Optional[List]:
        list_items = list(self._iter_list_items_recursive())
        if len(list_items) > 0:
            self._skip_empty_line()
            return List(list_items)

    def _iter_list_items_recursive(self) -> Iterator[ListItem]:
        prev_list_item = None
        first_indent_width = None

        while True:
            cur_line = self._line_iter.cur_line
            if cur_line is None:
                break

            cur_list_line = cur_line.create_list_line()
            if cur_list_line is None:
                break

            cur_indent_width = cur_list_line.indent_len

            if prev_list_item is None:
                prev_list_item = self._create_list_item(cur_list_line)
                first_indent_width = cur_indent_width
            elif cur_indent_width == first_indent_width:
                yield prev_list_item
                prev_list_item = self._create_list_item(cur_list_line)
            elif cur_indent_width > first_indent_width:
                sub_items = list(self._iter_list_items_recursive())
                prev_list_item.sub_items = sub_items
            else:
                break

        if prev_list_item is not None:
            yield prev_list_item

    def _create_list_item(self, list_line0: _ListLine) -> ListItem:
        lines = list(self._iter_list_item_lines(list_line0))
        preformatted = self._are_lines_preformatted(lines)
        if self._list_items_always_preformatted:
            preformatted = True
        text = '\n'.join(lines)
        inline_parser = InlineParser(text)
        inline_elements = inline_parser.parse()
        return ListItem(inline_elements=inline_elements, symbol=list_line0.symbol, preformatted=preformatted)

    def _iter_list_item_lines(self, list_line0):
        yield list_line0.text

        text_indent_len = list_line0.indent_len + len(list_line0.symbol) + len(' ')
        while True:
            line_k = self._line_iter.get_next_line()
            if line_k is None or line_k.is_empty:  # end of line or new block?
                break
            list_line_k = line_k.create_list_line()
            if list_line_k:  # new list item?
                break
            if line_k.indent_len < text_indent_len:
                raise Exception(line_k, 'wrong indent')
            yield line_k.text[text_indent_len:]

    def _create_table(self) -> Optional[Table]:
        columns = None
        rows = []
        for k, table_line in enumerate(self._iter_table_lines()):
            if k == 0:
                columns = list(self._iter_columns(table_line))
            else:
                row = self._create_row(table_line)
                rows.append(row)

        if columns is not None:
            self._skip_empty_line()
            return Table(columns=columns, rows=rows)

    def _iter_table_lines(self) -> Iterator[_TableLine]:
        while not self._line_iter.stopped:
            cur_line = self._line_iter.cur_line
            if cur_line is None:
                break
            table_line = cur_line.create_table_line()
            if table_line is None:
                break
            yield table_line
            self._line_iter.get_next_line()

    def _iter_columns(self, table_line: _TableLine) -> Iterator[Column]:
        for col_str in table_line.cell_strings:
            halign = self._calc_halign(col_str)
            yield Column(halign, col_str.strip())

    @staticmethod
    def _calc_halign(cell_str: str) -> HAlign:
        default_halign = HAlign.LEFT
        if cell_str == '':
            return default_halign

        if cell_str[0] != ' ' and cell_str[-1] == ' ':
            return HAlign.LEFT
        elif cell_str[0] == ' ' and cell_str[-1] != ' ':
            return HAlign.RIGHT
        elif cell_str[0] == ' ' and cell_str[-1] == ' ':
            return HAlign.CENTRE

        return default_halign

    def _create_row(self, table_line: _TableLine) -> Row:
        cells = list(self._iter_cells(table_line))
        return Row(cells)

    def _iter_cells(self, table_line: _TableLine) -> Iterator[Cell]:
        for cell_str in table_line.cell_strings:
            yield self._create_cell(cell_str)

    @staticmethod
    def _create_cell(cell_str: str) -> Cell:
        inline_parser = InlineParser(cell_str)
        inline_elements = inline_parser.parse()
        return Cell(inline_elements)


class _LineIterator:
    
    def __init__(self, text: str):
        self._raw_lines = text.split('\n')
        self._num_lines = len(self._raw_lines)
        self._k = 0
        self._cur_line = None
        if self._num_lines > 0:
            self._cur_line = _Line(self._k, self._raw_lines[self._k])
        
    @property
    def cur_line(self) -> Optional[_Line]:
        return self._cur_line
        
    @property
    def stopped(self) -> bool:
        return self._k >= self._num_lines
        
    def get_next_line(self) -> Optional[_Line]:
        if self._k + 1 < self._num_lines:
            self._k += 1
            self._cur_line = _Line(self._k, self._raw_lines[self._k])
            return self._cur_line
        else:
            self._k = self._num_lines
            self._cur_line = None
            
            
class _Line:

    _strip_left_rex = re.compile(r"(?P<leading_spaces> *)(?P<tail>.*)")
    _header_rex = re.compile(r"(?P<leading_hashes>#+) (?P<text>.*)")
    _list_rex = re.compile(r"(?P<leading_spaces> *)(?P<symbol>-|\+|=>|\?|[0-9]+\.(\)?)|[a-z]\.(\)?)) (?P<text>.*)")
    _table_rex = re.compile(r"|(.*)")
    _bold_rex = re.compile(r"\*(?P<bold>\w[^*]*\w)\*")
    _link_rex = re.compile(r"\[(.*)(\|.*)]")
    _image_rex = re.compile(r"")
    
    def __init__(self, row: int, text: str):
        self._row = row
        self._text = text
        m = self._strip_left_rex.match(text)
        assert m is not None
        self._indent_len = len(m.group('leading_spaces'))
        self._left_stripped = m.group('tail')

    def __str__(self):
        return f'{self._row}: {self._text}'

    def __repr__(self):
        return str(self)
        
    @property
    def row(self) -> int:
        return self._row

    @property
    def text(self) -> str:
        return self._text

    @property
    def indent_len(self) -> int:
        return self._indent_len
    
    @property
    def left_stripped(self) -> str:
        return self._left_stripped

    @property
    def is_empty(self) -> bool:
        return self._left_stripped == ''
        
    def create_header_line(self) -> Optional[_HeaderLine]:
        header_match = self._header_rex.match(self._text)
        if header_match is not None:
            level = len(header_match.group('leading_hashes'))
            text = header_match.group('text')
            return _HeaderLine(level, text)

    def create_paragraph_line(self) -> _ParagraphLine:
        return _ParagraphLine(self._text)

    def create_list_line(self) -> Optional[_ListLine]:
        list_match = self._list_rex.match(self._left_stripped)
        if list_match is not None:
            list_symbol = list_match.group('symbol')
            text = list_match.group('text')
            return _ListLine(self._indent_len, list_symbol, text)
            
    def create_table_line(self) -> Optional[_TableLine]:
        items = self._text.split('|')
        if len(items) > 1:
            if items[0] != '':
                raise MarkupParseError(self, 'wrong table line')

            if items[-1] == '':
                return _TableLine(items[1:-1])
            else:  # incomplete last item!
                return _TableLine(items[1:])

        
class _HeaderLine:

    def __init__(self, level: int, text: str):
        self.level = level
        self.text = text


class _ParagraphLine:

    def __init__(self, text: str):
        self.text = text


class _ListLine:

    def __init__(self, indent_len: int, symbol: str, text: str):
        self.indent_len = indent_len
        self.symbol = symbol  # '-' or '=>'
        self.text = text
    
       
class _TableLine:

    def __init__(self, cell_strings: TList[str]):
        self.cell_strings = cell_strings


class InlineParser:

    rex = re.compile(r'(?P<bold>\*(?P<bold_core>\w[^*]*\w)\*)')

    def __init__(self, text: str):
        self._text = text
        self._inline_elements = []
        self._prev_end = 0
        self._cur_xml_child = None

    def parse(self) -> TList[InlineElement]:
        self._prev_end = 0
        self._cur_xml_child = None
        for match in self.rex.finditer(self._text):
            self._process_gap(match)
            any(func(match)
                for func in [self._process_bold, self._process_link, self._process_image])
        gap_text = self._text[self._prev_end:]
        self._process_gap_text(gap_text)
        return self._inline_elements

    def _process_gap(self, match: Match) -> None:
        match_begin, match_end = match.span()
        gap_text = self._text[self._prev_end:match_begin]
        self._process_gap_text(gap_text)
        self._prev_end = match_end

    def _process_gap_text(self, gap_text: str) -> None:
        normal_text = NormalText(gap_text)
        self._inline_elements.append(normal_text)

    def _process_bold(self, match: Match) -> bool:
        bold = match.group('bold')
        if bold is None:
            return False

        bold_text = BoldText(match.group('bold_core'))
        self._inline_elements.append(bold_text)
        return True

    @staticmethod
    def _process_link(match: Match) -> bool:
        bold = match.group('link')
        if bold is None:
            return False

        return False  # todo....

    @staticmethod
    def _process_image(match: Match) -> bool:
        bold = match.group('image')
        if bold is None:
            return False

        return False  # todo....


class MarkupParseError(Exception):

    def __init__(self, line_info: _Line, err_txt: str):
        self.row = line_info.row
        self.line = line_info.text
        self.err_txt = err_txt
        
    def __str__(self):
        return f'{self.row}: {self.line} - {self.err_txt}'
