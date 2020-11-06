# Copyright (C) 2020  Christian Czepluch
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

import os
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Iterator, Optional, Any
from datetime import datetime
from zipfile import ZipFile

import yaml

from tasks.db import DB, Row

TaskSerial = int

_TASK_DPATH_REX = re.compile(r"[0-9x]{4,6}-.*")
_TASK_ZIPFILE_REX = re.compile(r"[0-9x]{4,6}-.*\.zip")
_TASK_FSTEM_REX = re.compile(r"(?P<date_str>[0-9x]{4,6})-(?P<title>.*)")


@dataclass
class TaskCaches:
    update_datetime: datetime
    map: Dict[TaskSerial, TaskCache] = field(default_factory=dict)


@dataclass
class TaskCache:
    task_serial: TaskSerial
    files_state: TaskFilesState
    category: str
    date_str: str
    title: str
    readme: str
    file_names: str


@dataclass
class TaskCacheData:
    files_state: TaskFilesState
    readme: str
    file_names: str


class TaskFilesState(Enum):
    UNKNOWN = 0
    NO_FILES = 1
    ACTIVE = 2   # unzipped
    PASSIVE = 3   # zipped
    ARCHIVED = 4  # on extra hard disc

    def rgb(self):
        return {
            self.ACTIVE.value: [0, 160, 0],
            self.PASSIVE.value: [0, 0, 255],
            self.ARCHIVED.value: [128, 128, 128],
        }.get(self.value, None)


@dataclass
class TaskMetaFileData:
    task_serial: int


class TaskCacheManager:

    def __init__(self, root: Path):
        self._root = root

    def read_resources(self) -> List[TaskResource]:
        return list(self._read_recursive(self._root))

    def _read_recursive(self, dpath: Path) -> Iterator[TaskResource]:
        for item in dpath.iterdir():
            if item.is_dir():
                if _TASK_DPATH_REX.match(item.name):
                    yield TaskDir(item)
                else:
                    yield from self._read_recursive(item)
            elif _TASK_ZIPFILE_REX.match(item.name):
                yield TaskZipFile(item)

    @staticmethod
    def read_from_db(db: DB) -> TaskCaches:
        misc_table = db.table('misc')
        misc_rows = misc_table.select(where_str='key = "task_caches_timestamp"')
        assert len(misc_rows) == 1
        misc_row = misc_rows[0]
        update_timestamp = int(misc_row['value'])
        update_datetime = datetime.fromtimestamp(update_timestamp)
        task_caches = TaskCaches(update_datetime=update_datetime)

        task_caches_table = db.table('task_caches')
        for row in task_caches_table.select():
            task_serial = int(row['task_serial'])
            task_caches.map[task_serial] = TaskCache(
                task_serial=task_serial,
                files_state=TaskFilesState[row['files_state'].upper()],
                category=row['category'],
                date_str=row['date'],
                title=row['title'],
                readme=row['readme'],
                file_names=row['file_names'],
            )
        return task_caches

    @staticmethod
    def write_db(db: DB, task_caches: TaskCaches) -> None:
        task_caches_table = db.table('task_caches')
        task_caches_table.clear()
        for cache in task_caches.map.values():
            row_values = {
                'task_serial': cache.task_serial,
                'files_state': cache.files_state.name.lower(),
                'category': cache.category,
                'date': cache.date_str,
                'title': cache.title,
                'readme': '' if cache.readme is None else cache.readme,
                'file_names': cache.file_names,
            }
            new_row = Row(table=task_caches_table, values=row_values)
            task_caches_table.insert_row(new_row)

        print('write_db: ready with caches')
        print(f'update_time: {task_caches.update_datetime}, = {int(task_caches.update_datetime.timestamp())}')

        misc_table = db.table('misc')

        where_str = 'key = "task_caches_timestamp"'
        value = str(int(task_caches.update_datetime.timestamp()))
        rows = misc_table.select(where_str=where_str)
        if len(rows) == 0:
            row = Row({'key': 'task_caches_timestamp', 'value': value}, misc_table)
            misc_table.insert_row(row)
        else:
            misc_table.update_row(values={'value': value}, where_str=where_str)
        db.commit()

    def update_state_files_in_db(self, task_serial: TaskSerial,
                                 new_files_state: TaskFilesState, db: DB) -> None:
        task_caches_table = db.table('task_caches')
        where_str = f'task_serial = {task_serial}'
        values = {'files_state': new_files_state.name.lower()}
        task_caches_table.update_row(values=values, where_str=where_str)
        db.commit()


class TaskResource:
    files_state = TaskFilesState.UNKNOWN

    def __init__(self, path: Path):
        self._path = path

    @property
    def path(self):
        return self._path

    def read(self) -> TaskCache:
        match = _TASK_FSTEM_REX.match(self._path.stem)
        return TaskCache(
            task_serial=self._read_metafile().task_serial,
            files_state=self.files_state,
            category=self._path.parent.name,
            date_str=match.group('date_str'),
            title=match.group('title'),
            readme=self._read_readme(),
            file_names=self._read_filenames(),
        )

    def _read_filenames(self):
        raise NotImplemented()

    def _read_readme(self) -> Optional[str]:
        raise NotImplemented()

    def _read_metafile(self) -> Optional[TaskMetaFileData]:
        raise NotImplemented()

    def write_metafile(self, meta_data: TaskMetaFileData) -> None:
        raise NotImplemented()


class TaskZipFile(TaskResource):
    files_state = TaskFilesState.PASSIVE

    def _read_filenames(self) -> str:
        lines = []
        with ZipFile(self._path, 'r') as zip_file:
            for zip_info in zip_file.infolist():
                lines.append(zip_info.filename)
        tree = self._create_file_tree(lines)
        return '\n'.join(list(self._iter_file_tree_items(tree, indent='')))

    def _iter_file_tree_items(self, tree: Dict[str, Any], indent: str) -> Iterator[str]:
        for name in sorted(tree.keys()):
            yield indent + name
            yield from self._iter_file_tree_items(tree[name], indent + '  ')

    def _create_file_tree(self, lines: List[str]) -> Dict[str, Any]:
        tree = {}
        for line in lines:
            line2 = line[:-1] if line[-1] == '/' else line
            parts = line2.split('/')
            self._add_parts_to_tree(parts, tree)
        return tree

    @staticmethod
    def _add_parts_to_tree(parts: List[str], tree: Dict[str, Any]) -> None:
        data = tree
        for part in parts:
            if part not in data:
                data[part] = {}
            data = data[part]

    def _read_readme(self) -> Optional[str]:
        with ZipFile(self._path, 'r') as zip_file:
            try:
                data = zip_file.read('readme.txt')
                try:
                    buf = data.decode('utf-8')
                    return buf
                except UnicodeDecodeError:
                    buf = data.decode('latin1')
                    return buf
            except KeyError:
                return

    def _read_metafile(self) -> Optional[TaskMetaFileData]:
        with ZipFile(self._path, 'r') as zip_file:
            try:
                data = zip_file.read('.meta')
                buf = data.decode('utf-8')
                yaml_data = yaml.safe_load(buf)
                return TaskMetaFileData(
                    task_serial=int(yaml_data['task_serial']))
            except KeyError:
                return

    def write_metafile(self, meta_data: TaskMetaFileData) -> None:
        zip_stat = self._path.stat()
        zip_mtime = zip_stat.st_mtime
        zip_atime = zip_mtime
        yaml_data = {'task_serial': meta_data.task_serial}
        yaml_str = yaml.safe_dump(yaml_data)
        with ZipFile(self._path, 'a') as zip_file:
            zip_file.writestr('.meta', yaml_str)
        os.utime(self._path, times=(zip_atime, zip_mtime))


class TaskDir(TaskResource):
    files_state = TaskFilesState.ACTIVE

    def _read_filenames(self) -> str:
        return '\n'.join(list(self._read_filenames_recursive(self._path, 0)))

    def _read_filenames_recursive(self, dpath: Path, level: int) -> Iterator[str]:
        indent = ' ' * level
        for item in dpath.iterdir():
            yield indent + item.name
            if item.is_dir():
                yield from self._read_filenames_recursive(item, level + 1)

    def _read_readme(self) -> Optional[str]:
        readme_fpath = self._path / 'readme.txt'
        if readme_fpath.exists():
            data = readme_fpath.open('rb').read()
            try:
                buf = data.decode('utf-8')
                return buf
            except UnicodeDecodeError:
                buf = data.decode('latin1')
                return buf

    def _read_metafile(self) -> Optional[TaskMetaFileData]:
        meta_fpath = self._path / '.meta'
        if meta_fpath.exists():
            stream = meta_fpath.open('r', encoding='utf-8')
            yaml_data = yaml.safe_load(stream)
            try:
                return TaskMetaFileData(
                    task_serial=int(yaml_data['task_serial']))
            except TypeError:
                dummy = True

    def write_metafile(self, meta_data: TaskMetaFileData) -> None:
        yaml_data = {'task_serial': meta_data.task_serial}
        meta_fpath = self._path / '.meta'
        stream = meta_fpath.open('w', encoding='utf-8')
        yaml.safe_dump(yaml_data, stream)
