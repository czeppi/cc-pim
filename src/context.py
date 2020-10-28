# Copyright (C) 2014  Christian Czepluch
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
from dataclasses import dataclass
from pathlib import Path
from typing import Tuple


class Context:

    def __init__(self, root_dir, config: Config):
        self._root_dir = root_dir
        self._etc_dir = root_dir / 'etc'
        self._config = config

    @property
    def config(self):
        return self._config

    @property
    def app_icon_dir(self):
        return self._etc_dir / 'icons'

    @property
    def data_icon_dir(self):
        return self.data_dir / 'icons'

    @property
    def data_dir(self):
        return Path('g:/app-data/cc-pim')

    @property
    def contacts_db_path(self):
        return self.data_dir / 'contacts.sqlite'

    @property
    def tasks_db_path(self):
        return self.data_dir / 'tasks.sqlite3'

    @property
    def tasks_metamodel_path(self):
        return self._etc_dir / 'tasks.ini'

    @property
    def no_keywords_path(self):
        return self._etc_dir / 'no-keywords.txt'


@dataclass
class Config:
    app_title: str = 'CC-PIM'
    frame_pos: Tuple[int, int] = 0, 0
    frame_size: Tuple[int, int] = 1200, 800
    search_width: int = 400
    margin: int = 5
    logging_enabled: bool = False
