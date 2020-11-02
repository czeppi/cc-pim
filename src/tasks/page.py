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

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import List as TList, Optional, Iterator

"""
example:


Page([
    Header(level=1, inline_elements=[NormalText('A Title')]),
    Paragraph([NormalText('Dies ist '), BoldElement('ein'), NormalText(' paragraph.')],
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


class HAlign(Enum):
    LEFT = 1
    RIGHT = 2
    CENTRE = 3


@dataclass
class Width:
    value: int
    is_relative: bool = True


@dataclass
class ElementBase:

    def copy(self) -> InlineElement:
        raise NotImplemented()


@dataclass
class InlineElement(ElementBase):
    text: Optional[str]


@dataclass
class NormalText(InlineElement):

    def copy(self) -> NormalText:
        return NormalText(self.text)


@dataclass
class BoldText(InlineElement):

    def copy(self) -> BoldText:
        return BoldText(self.text)


@dataclass
class Link(InlineElement):
    uri: str

    def copy(self):
        return Link(text=self.text, uri=self.uri)


@dataclass
class Image(InlineElement):
    path: Path
    width: Width

    def copy(self):
        return Image(path=self.path, width=self.width, text=self.text)


@dataclass
class BlockElement(ElementBase):
    pass

    def iter_inline_elements(self) -> Iterator[InlineElement]:
        raise NotImplemented


@dataclass
class Header(BlockElement):
    level: int
    inline_elements: TList[InlineElement] = field(default_factory=list)

    def iter_inline_elements(self) -> Iterator[InlineElement]:
        yield from self.inline_elements


@dataclass
class Paragraph(BlockElement):
    inline_elements: TList[InlineElement] = field(default_factory=list)
    preformatted: bool = False

    def iter_inline_elements(self) -> Iterator[InlineElement]:
        yield from self.inline_elements


@dataclass
class ListItem(ElementBase):
    inline_elements: TList[InlineElement] = field(default_factory=list)
    sub_items: TList[ListItem] = field(default_factory=list)
    symbol: str = '-'
    preformatted: bool = False

    def iter_inline_elements(self) -> Iterator[InlineElement]:
        yield from self.inline_elements
        for sub_item in self.sub_items:
            yield from sub_item.iter_inline_elements()


@dataclass
class List(BlockElement):
    items: TList[ListItem] = field(default_factory=list)

    def iter_inline_elements(self) -> Iterator[InlineElement]:
        for item in self.items:
            yield from item.iter_inline_elements()


@dataclass
class Column(ElementBase):
    halign: HAlign
    text: str


@dataclass
class Cell(ElementBase):
    inline_elements: TList[InlineElement] = field(default_factory=list)

    def iter_inline_elements(self) -> Iterator[InlineElement]:
        yield from self.inline_elements


@dataclass
class Row(ElementBase):
    cells: TList[Cell] = field(default_factory=list)

    def iter_inline_elements(self) -> Iterator[InlineElement]:
        for cell in self.cells:
            yield from cell.iter_inline_elements()


@dataclass
class Table(BlockElement):
    columns: TList[Column]
    rows: TList[Row]

    def iter_inline_elements(self) -> Iterator[InlineElement]:
        for row in self.rows:
            yield from row.iter_inline_elements()


@dataclass
class Page(ElementBase):
    block_elements: TList[BlockElement] = field(default_factory=list)

    def iter_inline_elements(self) -> Iterator[InlineElement]:
        for block_element in self.block_elements:
            yield from block_element.iter_inline_elements()
