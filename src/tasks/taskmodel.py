# Copyright (C) 2013  Christian Czepluch
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
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Iterable, Any, Iterator, Set, Tuple

import yaml

from tasks.caching import TaskCache, TaskCacheManager, TaskCaches, TaskCacheData, TaskFilesState, RGB
from tasks.db import Row, DB
from tasks.xml_reading import read_from_xmlstr
from tasks.zipping import Unzipper, Zipper

TaskSerial = int


class TaskModel:

    def __init__(self, db: DB, tasks_root: Path, keyword_extractor: KeywordExtractor):
        self._db = db
        self._tasks_root = tasks_root
        self._tasks_revisions_table = self._db.table('tasks_revisions')
        self._keyword_extractor = keyword_extractor
        self._tasks: Dict[int, Task] = {}
        self._default_rev = TaskRevision.create_default(model=self)

    @property
    def tasks(self):
        return self._tasks.values()

    @property
    def tasks_root(self):
        return self._tasks_root

    def read(self) -> None:
        self._db.open()
        self._tasks.clear()
        task_revision_map = self._read_task_revisions()
        self._tasks = {serial: Task(serial, sorted(revs, key=lambda x: x.rev_no), self)
                       for serial, revs in task_revision_map.items()}
        self._read_task_caches()

    def _read_task_revisions(self) -> Dict[TaskSerial, List[TaskRevision]]:
        task_revision_map: Dict[int, List[TaskRevision]] = {}
        for row in self._tasks_revisions_table.select():
            task_rev = TaskRevision(model=self, **row)
            task_serial = task_rev.task_serial
            if task_serial not in task_revision_map:
                task_revision_map[task_serial] = [self._default_rev]
            task_revision_map[task_serial].append(task_rev)
        return task_revision_map

    def _read_task_caches(self) -> None:
        cache_mgr = TaskCacheManager(self._tasks_root)
        task_caches = cache_mgr.read_from_db(self._db)
        for cache in task_caches.map.values():
            task = self._tasks.get(cache.task_serial, None)
            if task is None:
                raise Exception('task_cache: task {task_cache.task_serial} not found')
            task.cache = TaskCacheData(files_state=cache.files_state,
                                       readme=cache.readme,
                                       file_names=cache.file_names)

    def create_new_task(self, task_serial: Optional[int] = None) -> Task:
        if task_serial is None:
            task_serial = self._get_next_task_id()
        return Task(task_serial, revisions=[self._default_rev], model=self)

    def _get_next_task_id(self) -> int:
        return max(self._tasks.keys()) + 1

    def add_task_revision(self, task_rev: TaskRevision) -> None:
        task_serial = task_rev.task_serial
        if task_serial not in self._tasks:
            self._tasks[task_serial] = self.create_new_task(task_serial)
        self._tasks[task_serial].add_revision(task_rev)

        self._write_task_revision(task_rev)

    def _write_task_revision(self, task_rev: TaskRevision) -> None:
        tasks_revisions_table = self._tasks_revisions_table
        task_rev_values = task_rev.get_values()
        row_values = {x.name: task_rev_values[x.name]
                      for x in tasks_revisions_table.attributes}
        new_row = Row(table=tasks_revisions_table, values=row_values)
        tasks_revisions_table.insert_row(new_row)
        self._db.commit()

    def get_sorted_categories(self) -> List[str]:
        cat_set = set(task.last_revision.category
                      for task in self._tasks.values()
                      if task.last_revision.category != '')
        return sorted(cat_set)

    def calc_keywords(self) -> List[str]:
        keywords = set()
        for task in self._tasks.values():
            keywords |= task.last_revision.keywords

        return sorted(keywords)

    # def search_tasks(self, with_keywords: Optional[List[str]] = None) -> List[Task]:
    #     if with_keywords is None:
    #         with_keywords = []
    #     result_tasks = []
    #     for id_ in sorted(self._tasks.keys()):
    #         task = self._tasks[id_]
    #         if len(with_keywords) == 0 or (set(with_keywords) & set(task.keywords)):
    #             result_tasks.append(task)
    #     return result_tasks

    def get_task(self, task_serial: int) -> Task:
        return self._tasks[task_serial]

    def extract_keywords(self, text: str) -> List[str]:
        return self._keyword_extractor.get_keywords(text)

    def update_cache(self, timestamp: datetime, task_cache_list: List[TaskCache]) -> None:
        for cache in task_cache_list:
            cache_task_key = cache.category, cache.date_str, cache.title
            if not cache.task_serial:
                # task = task_map.get(cache_task_key, None)
                # if task is None:
                #     task = self.create_new_task()
                #     new_task_rev = task.create_new_revision(**dlg_values)
                #     self.add_task_revision(new_task_rev)
                #     task_resource = ...
                #     task_resource.write_meta(task.serial)
                # else:
                #     cache.task_serial = task.serial
                raise Exception(cache_task_key)
            task = self._tasks.get(cache.task_serial, None)
            if task is None:
                raise Exception(cache.task_serial)  # todo: show error dialog

            task_key = self._get_task_key(task)
            if task_key != cache_task_key:
                raise Exception(cache.task_serial)  # todo: show error dialog

        cache_mgr = TaskCacheManager(self._tasks_root)
        task_caches = TaskCaches(
            update_datetime=timestamp,
            map={cache.task_serial: cache for cache in task_cache_list})
        cache_mgr.write_db(task_caches=task_caches, db=self._db)

        # update task.cache
        for task in self._tasks.values():
            task.cache = None
        for cache in task_caches.map.values():
            new_data = TaskCacheData(files_state=cache.files_state,
                                     readme=cache.readme,
                                     file_names=cache.file_names)
            self._tasks[cache.task_serial].cache = new_data

    @staticmethod
    def _get_task_key(task: Task) -> Tuple[str, str, str]:
        task_rev = task.last_revision
        return task_rev.category, task_rev.date, task_rev.title


class Task:

    def __init__(self, serial: int, revisions: List[TaskRevision], model: TaskModel):
        assert len(revisions) > 0
        for i, rev in enumerate(revisions):
            assert rev.rev_no == i

        self._serial = serial
        self._revisions = revisions
        self._model = model
        self.cache = None

    @property
    def serial(self):
        return self._serial

    @property
    def last_revision(self):
        return self._revisions[-1]

    @property
    def revisions_list(self):
        return self._revisions

    @property
    def files_state(self):
        return self.cache.files_state if self.cache else TaskFilesState.NO_FILES

    def get_revision(self, rev_no: int) -> TaskRevision:
        return self._revisions[rev_no]

    def is_empty(self) -> bool:
        n = len(self._revisions)
        return n == 0 or n == 1 and self._revisions[0].rev_no == 0

    def get_header(self) -> str:
        n = len(self._revisions)
        rev_1st = self._revisions[1] if n >= 2 else self._revisions[0]
        rev_last = self._revisions[-1]
        return f'{rev_1st.date}: {rev_last.title}'

    def get_rgb(self) -> RGB:
        if self.cache:
            return self.cache.files_state.rgb()

    def create_new_revision(self, title: str, body: str, category: str) -> TaskRevision:
        new_rev_no = len(self._revisions)
        return TaskRevision(
            task_serial=self._serial,
            rev_no=new_rev_no,
            date=datetime.today().strftime('%y%m%d'),
            category=category,
            title=title,
            body=body,
            group_serial=0,
            model=self._model
        )

    def add_revision(self, task_rev: TaskRevision) -> None:
        assert len(self._revisions) == task_rev.rev_no
        self._revisions.append(task_rev)

    def create_dir(self, tasks_root: Path) -> None:
        assert self.cache is None
        task_dpath = tasks_root / self.get_rel_path()
        assert not task_dpath.exists()
        task_dpath.mkdir()
        self._create_meta_file(task_dpath)
        self.cache = TaskCacheData(files_state=TaskFilesState.ACTIVE,
                                   readme='',
                                   file_names='')

    def _create_meta_file(self, task_dpath: Path) -> None:
        meta_fpath = task_dpath / '.meta'
        stream = meta_fpath.open('w')
        meta_data = {'task_serial': self.serial}
        yaml.safe_dump(meta_data, stream)

    def zip_dir(self, tasks_root: Path) -> None:
        assert self.cache is not None
        assert self.cache.files_state == TaskFilesState.ACTIVE
        task_dpath = tasks_root / self.get_rel_path()
        assert task_dpath.exists()
        zipper = Zipper(task_dpath)
        zipper.start()
        self.cache.files_state = TaskFilesState.PASSIVE
        shutil.rmtree(task_dpath)

    def unzip_file(self, tasks_root: Path) -> None:
        assert self.cache is not None
        assert self.cache.files_state == TaskFilesState.PASSIVE
        zip_fpath = tasks_root / (self.get_rel_path() + '.zip')
        assert zip_fpath.exists()
        unzipper = Unzipper(zip_fpath)
        unzipper.start()
        self.cache.files_state = TaskFilesState.ACTIVE
        zip_fpath.unlink()

    def get_path(self, tasks_root: Path, files_state: TaskFilesState) -> Path:
        task_rev = self.last_revision
        name = f'{task_rev.category}/{task_rev.date}-{task_rev.title}'
        if files_state == TaskFilesState.ACTIVE:
            return tasks_root / name
        elif files_state == TaskFilesState.PASSIVE:
            return tasks_root / (name + '.zip')

    def get_rel_path(self) -> str:
        task_rev = self.last_revision
        return f'{task_rev.category}/{task_rev.date}-{task_rev.title}'

    def does_meet_the_criteria(self, search_words: Iterable[str],
                               category: str, files_state: str) -> bool:
        task_rev = self.last_revision
        if task_rev.date == '200114':
            dummy = True

        if category and category != task_rev.category:
            return False
        if files_state:
            if self.files_state.name.lower() != files_state:
                return False
        return task_rev.contains_all_keyword(search_words)


class TaskRevision:

    @staticmethod
    def create_default(model) -> TaskRevision:
        return TaskRevision(
            task_serial=0,
            rev_no=0,
            date='',
            category='',
            title='',
            body='',
            group_serial=0,
            model=model)

    def __init__(self, task_serial: int, rev_no: int,
                 date: str, category: str, title: str, body: str, group_serial: int, model: TaskModel):

        self._task_serial = task_serial
        self._rev_no = rev_no
        self._date = date
        self._category = category
        self._title = title
        self._body = body
        self._page = read_from_xmlstr(body, contains_page_element=False)
        self._model = model
        self._group_serial = group_serial
        self._keywords: Set[str] = self._extract_keywords()
        self._part_keywords = set(word[:n] for word in self._keywords for n in range(2, len(word) + 1))

    def get_values(self):
        return {
            'task_serial': self._task_serial,
            'rev_no': self._rev_no,
            'date': self._date,
            'category': self._category,
            'title': self._title,
            'body': self._body,
            'group_serial': self._group_serial,
            'model': self._model,
        }

    @property
    def task_serial(self):
        return self._task_serial

    @property
    def task(self):
        return self._model.get_task(self._task_serial)

    @property
    def rev_no(self):
        return self._rev_no

    @property
    def date(self) -> str:
        normed_date = str(self._date)
        if len(normed_date) % 2 == 1:
            normed_date = '0' + normed_date
        return normed_date

    @property
    def title(self):
        return self._title

    @property
    def body(self):
        return self._body

    @property
    def page(self):
        return self._page

    @property
    def category(self):
        return self._category

    @property
    def keywords(self):
        return self._keywords

    def _extract_keywords(self) -> Set[str]:
        return set(self._iter_keywords())

    def _iter_keywords(self):
        yield from self._model.extract_keywords(self._title)
        for inline_elem in self._page.iter_inline_elements():
            if inline_elem.text:
                yield from self._model.extract_keywords(inline_elem.text)

    def contains_all_keyword(self, keywords: Iterable[str]) -> bool:
        return set(keywords) <= self._part_keywords

    def get_header(self) -> str:
        return self.task.get_header()

    def have_values_changed(self, new_values: Dict[str, Any]) -> bool:
        return self._title != new_values['title'] or \
               self._body != new_values['body'] or \
               self._category != new_values['category'] or \
               self._group_serial != new_values['group_serial']


class KeywordExtractor:
    rex = re.compile(r"[a-zA-Z0-9_äöüßÄÖÜ.]+[a-zA-Z0-9_äöüßÄÖÜ\-.]*[a-zA-Z0-9_äöüßÄÖÜ.]")

    def __init__(self, no_keywords_path: Path):
        lines = no_keywords_path.open(encoding='utf-8').readlines()
        self._no_keywords = set(line.strip() for line in lines)
        self._no_keywords.add('')

    def get_keywords(self, title: str) -> List[str]:
        keywords = self.rex.findall(title)
        return list(self._filter_keywords(keywords))

    def _filter_keywords(self, keywords: Iterable[str]) -> Iterator[str]:
        for keyword in keywords:
            kw = keyword.lower()
            while len(kw) > 0 and not self._is_alnum(kw[0]):
                kw = kw[1:]
            while len(kw) > 0 and not self._is_alnum(kw[-1]):
                kw = kw[:-1]
            if kw not in self._no_keywords:
                yield keyword.lower()

    @staticmethod
    def _is_alnum(ch):
        return ch.isalnum() or ch in ['ä', 'ö', 'ü', 'ß', 'Ä', 'Ö', 'Ü']
