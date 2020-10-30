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
from typing import Tuple, Dict

from contacts.contactmodel import ContactModel
from contacts.repository import Repository
from tasks.db import DB
from tasks.metamodel import MetaModel
from tasks.taskmodel import TaskModel, KeywordExtractor

GUI = 'pyside2'
LOGGING_ENABLED = False

if GUI == 'pyside2':
    from PySide2.QtGui import QIcon as Icon
elif GUI == 'wx':
    import wx
    from wx import Icon


@dataclass
class Context:
    system: SystemResourceMgr
    user: UserResourceMgr


class SystemResourceMgr:

    def __init__(self, etc_dpath: Path):
        self._etc_dpath = etc_dpath

    @property
    def icon_dir(self) -> Path:
        return self._etc_dpath / 'icons'

    def read_icon(self, icon_name: str) -> Icon:
        icon_fpath = self._etc_dpath / 'icons' / (icon_name + '.ico')
        return _read_icon(icon_fpath)

    def read_task_metamodel(self) -> MetaModel:
        metamodel_path = self._etc_dpath / 'tasks.ini'
        meta_model = MetaModel(LOGGING_ENABLED)
        meta_model.read(metamodel_path)
        return meta_model


class UserResourceMgr:

    def __init__(self, user_dpath: Path):
        self._user_dpath = user_dpath

    def read_config(self) -> Config:
        return Config()  # todo: read it from file

    def read_state(self) -> UserState:
        return UserState()  # todo: read it from file

    def read_icons(self) -> Dict[str, Icon]:
        icon_dpath = self._user_dpath / 'icons'
        return {icon_fpath.stem.lower(): _read_icon(icon_fpath)
                for icon_fpath in icon_dpath.iterdir()}

    def read_contact_model(self) -> ContactModel:
        contact_repo = Repository(self._user_dpath / 'contacts.sqlite')
        contact_repo.reload()
        date_changes, fact_changes = contact_repo.aggregate_revisions()
        return ContactModel(date_changes, fact_changes)

    def read_task_model(self, tasks_metamodel: MetaModel) -> TaskModel:
        sqlite3_path = self._user_dpath / 'tasks.sqlite'
        db = DB(sqlite3_path, tasks_metamodel, logging_enabled=LOGGING_ENABLED)
        keyword_extractor = KeywordExtractor(self._user_dpath / 'no-keywords.txt')
        task_model = TaskModel(db, keyword_extractor=keyword_extractor)
        task_model.read()
        return task_model


@dataclass
class UserState:
    frame_pos: Tuple[int, int] = 0, 0
    frame_size: Tuple[int, int] = 1200, 800
    search_width: int = 400


@dataclass
class Config:
    margin: int = 5
    logging_enabled: bool = False


def _read_icon(icon_fpath: Path) -> Icon:
    if GUI == 'pyside2':
        return Icon(str(icon_fpath))
    elif GUI == 'wx':
        return Icon(str(icon_fpath), wx.BITMAP_TYPE_ICO)
