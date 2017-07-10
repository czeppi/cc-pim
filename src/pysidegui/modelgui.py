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

from pysidegui.globalitemid import GlobalItemID
from typing import Optional, Iterator


class ModelGui:

    def new_item(self, frame) -> Optional[GlobalItemID]:
        raise Exception('net yet implemented.')

    def edit_item(self, glob_item_id: GlobalItemID, frame) -> bool:
        raise Exception('net yet implemented.')

    def save_all(self):
        raise Exception('net yet implemented.')

    def revert_change(self):
        raise Exception('net yet implemented.')

    def get_html_text(self, glob_item_id: GlobalItemID) -> str:
        raise Exception('net yet implemented.')

    def exists_uncommited_changes(self) -> bool:
        raise Exception('net yet implemented.')

    def get_id_from_href(self, href_str: str) -> GlobalItemID:
        raise Exception('net yet implemented.')

    def iter_sorted_ids_from_keywords(self, keywords) -> Iterator[GlobalItemID]:
        raise Exception('net yet implemented.')

    def get_object_title(self, glob_item_id: GlobalItemID) -> str:
        raise Exception('net yet implemented.')
