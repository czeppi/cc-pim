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
from dataclasses import dataclass

from PySide2.QtGui import QIcon
from PySide2.QtWidgets import QMainWindow

from pysidegui.globalitemid import GlobalItemID
from typing import Optional, Iterator, Iterable, Dict

from tasks.caching import RGB


class ModelGui:

    def new_item(self, frame: QMainWindow, data_icons: Dict[str, QIcon],
                 css_buf: Optional[str]) -> Optional[GlobalItemID]:
        raise NotImplemented()

    def edit_item(self, glob_item_id: GlobalItemID, frame: QMainWindow, data_icons: Dict[str, QIcon],
                  css_buf: Optional[str]) -> bool:
        raise NotImplemented()

    def save_all(self) -> None:
        raise NotImplemented()

    def revert_change(self) -> None:
        raise NotImplemented()

    def get_html_text(self, glob_item_id: GlobalItemID,
                      search_rex: Optional[re.Pattern] = None) -> str:
        raise NotImplemented()

    def exists_uncommitted_changes(self) -> bool:
        raise NotImplemented()

    def get_id_from_href(self, href_str: str) -> Optional[GlobalItemID]:
        raise NotImplemented()

    def iter_sorted_filtered_items(self, search_words: Iterable[str],
                                   filter_category: str,
                                   filter_files_state: str) -> Iterator[ResultItemData]:
        raise NotImplemented()

    @staticmethod
    def iter_categories() -> Iterator[str]:
        raise NotImplemented()

    @staticmethod
    def iter_context_menu_items(glob_item_id: GlobalItemID) -> Iterator[str]:
        yield from []  # default: no context menu

    def exec_context_menu_action(self, glob_item_id: GlobalItemID,
                                 action_name: str, file_commander_cmd: str) -> None:
        pass


@dataclass
class ResultItemData:
    glob_id: GlobalItemID
    category: str
    title: str
    rgb: Optional[RGB] = None
