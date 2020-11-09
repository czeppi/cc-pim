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
import yaml

from contacts.contactmodel import ContactModel
from contacts.repository import Repository
from tasks.db import DB
from tasks.metamodel import MetaModel
from tasks.taskmodel import TaskModel, WordExtractor

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
        config_fpath = self._user_dpath / 'config.yaml'
        stream = config_fpath.open('r')
        yaml_data = yaml.safe_load(stream)
        config_data = {}
        if 'tasks_root' in yaml_data:
            root_dpath = Path(yaml_data['tasks_root'])
            if not root_dpath.is_absolute():
                root_dpath = (self._user_dpath / root_dpath).resolve()
            config_data['tasks_root'] = root_dpath
        if 'file_commander_cmd' in yaml_data:
            config_data['file_commander_cmd'] = yaml_data['file_commander_cmd']
        return Config(**config_data)

    def read_state(self) -> UserState:
        state_fpath = self._user_dpath / 'state.yaml'
        if state_fpath.exists():
            stream = state_fpath.open('r')
            yaml_data = yaml.safe_load(stream)
            state_data = {
                'frame_pos': (int(yaml_data['frame_x']), int(yaml_data['frame_y'])),
                'frame_size': (int(yaml_data['frame_width']), int(yaml_data['frame_height'])),
                'search_width': int(yaml_data['search_width']),
            }
            return UserState(**state_data)
        else:
            return UserState()

    def write_state(self, state: UserState) -> None:
        state_fpath = self._user_dpath / 'state.yaml'
        stream = state_fpath.open('w')
        frame_x, frame_y = state.frame_pos
        frame_width, frame_height = state.frame_size
        yaml_data = {
            'frame_x': frame_x,
            'frame_y': frame_y,
            'frame_width': frame_width,
            'frame_height': frame_height,
            'search_width': state.search_width,
        }
        yaml.safe_dump(yaml_data, stream)

    def read_icons(self) -> Dict[str, Icon]:
        icon_dpath = self._user_dpath / 'icons'
        return {icon_fpath.stem.lower(): _read_icon(icon_fpath)
                for icon_fpath in icon_dpath.iterdir()}

    def get_contact_repo(self) -> Repository:
        return Repository(self._user_dpath / 'contacts.sqlite')

    def read_task_model(self, tasks_metamodel: MetaModel, tasks_root: Path) -> TaskModel:
        sqlite3_path = self._user_dpath / 'tasks.sqlite'
        db = DB(sqlite3_path, tasks_metamodel, logging_enabled=LOGGING_ENABLED)
        keyword_extractor = WordExtractor(self._user_dpath / 'no-keywords.txt')
        task_model = TaskModel(db, tasks_root=tasks_root, keyword_extractor=keyword_extractor)
        task_model.read()
        return task_model


@dataclass
class UserState:
    frame_pos: Tuple[int, int] = 0, 0
    frame_size: Tuple[int, int] = 1200, 800
    search_width: int = 400


@dataclass
class Config:
    tasks_root: Path
    file_commander_cmd: str
    margin: int = 5


def _read_icon(icon_fpath: Path) -> Icon:
    if GUI == 'pyside2':
        return Icon(str(icon_fpath))
    elif GUI == 'wx':
        return Icon(str(icon_fpath), wx.BITMAP_TYPE_ICO)
