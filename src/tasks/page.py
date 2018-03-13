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

from enum import Enum
from pathlib import Path
from typing import List as TList


"""
example:


Page([
    Header(level=1, inline_elements=[NormalText('Ein Titel')]),
    Paragraph([NormalText('Dies ist '), BoldElement('ein'), NormalText(' Absatz.')],
    List([
        ListItem(inline_elements=[NormalText('a')],
                 sub_items = [
                    ListItem(inline_elements=[NormalText('a1')]),
                    ListItem(inline_elements=[NormalText('a2')]),
                 ]),
        ListItem(inline_elements=[NormalText('b')],
                 sub_items = [
                    ListItem(inline_elements=[NormalText('b1')]),
                 ]),
    ]),
    Table(columns=[Column(halign=HAlign.left), Column(halign=HAlign.right)],
          rows=[
            Row([Cell(NormalText('A1')), Cell(NormalText('B1'))]),
            Row([Cell(NormalText('A2')), Cell(NormalText('B2'))]),
    ])
])

"""


class ReadOnlyList:

    def __init__(self, items):
        self._items = items

    def __eq__(self, other):
        return self._items == other._items

    def __ne__(self, other):
        return not self.__eq__(other)

    def __iter__(self):
        yield from self._items

    def __len__(self):
        return len(self._items)


class HAlign(Enum):
    
    left = 1
    right = 2
    centre = 3
    
    
class Width:

    def __init__(self, value, relative=True):
        self.value = value
        self.is_relative = relative
        
    def __eq__(self, other):
        return isinstance(other, Width) and self.value == other.value and self.is_relative == other.is_relevant


class ElementBase:

    def __eq__(self, other):
        raise Exception('not implemented')

    def __ne__(self, other):
        return not self.__eq__(other)


class InlineElement(ElementBase):
    pass

    
class NormalText(InlineElement):

    def __init__(self, text: str):
        assert isinstance(text, str)
        self.text = text

    def __eq__(self, other):
        return isinstance(other, NormalText) and self.text == other.text

        
class BoldText(InlineElement):

    def __init__(self, text: str):
        assert isinstance(text, str)
        self.text = text

    def __eq__(self, other):
        return isinstance(other, BoldText) and self.text == other.text


class Link(InlineElement):

    def __init__(self, url: str, text: str = None):
        assert isinstance(url, str) and isinstance(text, str)
        self.url = url
        self.text = text
    
    def __eq__(self, other):
        return isinstance(other, Link) and self.url == other.url and self.text == other.text


class Image(InlineElement):

    def __init__(self, path: Path, width: Width):
        assert isinstance(path, Path) and isinstance(width, Width)
        self.path = path
        self.width = width
            
    def __eq__(self, other):
        return isinstance(other, Image) and self.path == other.path and self.width == other.width


class BlockElement(ElementBase):
    pass

        
class Header(BlockElement):

    def __init__(self, level: int, inline_elements: TList[InlineElement] = []):
        assert isinstance(level, int) and all(isinstance(x, InlineElement) for x in inline_elements)
        self.level = level
        self.inline_elements = inline_elements
        
    def __eq__(self, other):
        return isinstance(other, Header) \
               and self.level == other.level \
               and self.inline_elements == other.inline_elements


class Paragraph(BlockElement):

    def __init__(self, inline_elements: TList[InlineElement] = [], preformatted: bool = False):
        assert all(isinstance(x, InlineElement) for x in inline_elements)
        self.inline_elements = inline_elements
        self.preformatted = preformatted

    def __eq__(self, other):
        return isinstance(other, Paragraph) \
               and self.inline_elements == other.inline_elements \
               and self.preformatted == other.preformatted


class ListItem(ElementBase):

    def __init__(self, inline_elements: TList[InlineElement] = [],
                       sub_items: TList['ListItem'] = [],
                       symbol: str = '-',
                       preformatted: bool = False):
        assert  all(isinstance(x, InlineElement) for x in inline_elements) \
            and all(isinstance(x, ListItem) for x in sub_items)
        self.symbol = symbol
        self.inline_elements = inline_elements
        self.sub_items = sub_items
        self.preformatted = preformatted

    def __eq__(self, other):
        return isinstance(other, ListItem) \
               and self.inline_elements == other.inline_elements \
               and self.sub_items == other.sub_items \
               and self.preformatted == other.preformatted


class List(BlockElement):

    def __init__(self, items: TList[ListItem] = []):
        assert all(isinstance(x, ListItem) for x in items)
        self.items = items
        
    def __eq__(self, other):
        return isinstance(other, List) and self.items == other.items


class Column(ElementBase):

    def __init__(self, halign: HAlign, text: str):
        assert isinstance(halign, HAlign) and isinstance(text, str)
        self.halign = halign
        self.text = text

    def __eq__(self, other):
        return isinstance(other, Column) and self.halign == other.halign and self.text == other.text


class Cell(ElementBase):

    def __init__(self, inline_elements: TList[InlineElement] = []):
        assert all(isinstance(x, InlineElement) for x in inline_elements)
        self.inline_elements = inline_elements

    def __eq__(self, other):
        return isinstance(other, Cell) and self.inline_elements == other.inline_elements


class Row(ElementBase):

    def __init__(self, cells: TList[Cell] = []):
        assert all(isinstance(x, Cell) for x in cells)
        self.cells = cells

    def __eq__(self, other):
        return isinstance(other, Row) and self.cells == other.cells


class Table(BlockElement):

    def __init__(self, columns: TList[Column], rows: TList[Row]):
        assert  all(isinstance(x, Column) for x in columns) \
            and all(isinstance(x, Row) for x in rows)
        self.columns = columns
        self.rows = rows

    def __eq__(self, other):
        return isinstance(other, Table) and self.columns == other.columns and self.rows == other.rows


class Page(ElementBase):

    def __init__(self, block_elements: TList[BlockElement] = []):
        assert all(isinstance(x, BlockElement) for x in block_elements)
        self.block_elements = block_elements

    def __eq__(self, other):
        return isinstance(other, Page) and self.block_elements == other.block_elements

