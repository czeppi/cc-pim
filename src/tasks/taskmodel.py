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
from typing import Optional, Dict, List, Iterable, Any, Iterator, Set
import yaml

from tasks.caching import TaskCache, TaskCacheManager, TaskCaches, TaskCacheData, TaskFilesState, RGB, TaskDir
from tasks.db import Row, DB
from tasks.xml_reading import read_from_xmlstr
from tasks.zipping import Unzipper, Zipper

TaskSerial = int


class TaskModel:

    def __init__(self, db: DB, tasks_root: Path, word_extractor: WordExtractor):
        self._db = db
        self._tasks_root = tasks_root
        self._tasks_revisions_table = self._db.table('tasks_revisions')
        self._word_extractor = word_extractor
        self._tasks: Dict[int, Task] = {}
        self._default_rev = TaskRevision.create_default()

    @property
    def db(self):
        return self._db

    @property
    def tasks(self):
        return self._tasks.values()

    @property
    def tasks_root(self):
        return self._tasks_root

    @property
    def word_extractor(self):
        return self._word_extractor

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
            task_rev = TaskRevision(word_extractor=self._word_extractor, **row)
            task_serial = task_rev.task_serial
            if task_serial not in task_revision_map:
                task_revision_map[task_serial] = [self._default_rev]
            task_revision_map[task_serial].append(task_rev)
        return task_revision_map

    def _read_task_caches(self) -> None:
        cache_mgr = TaskCacheManager(self._tasks_root)
        task_caches = cache_mgr.read_from_db(self._db)
        for cache in task_caches.map.values():
            if cache.task_serial not in self._tasks:
                raise Exception(f'task_cache: task {cache.task_serial} not found')

        for task in self._tasks.values():
            cache = task_caches.map.get(task.serial, None)
            cache_data = cache.get_data() if cache is not None else None
            task.set_cache(cache_data, self._word_extractor)

    def update_cache_of_active_tasks(self) -> None:
        print('update caches of active tasks...')
        for task in self._tasks.values():
            if task.cache and task.cache.files_state == TaskFilesState.ACTIVE:
                task_dir = TaskDir(task.get_path(self._tasks_root))
                cache = task_dir.read()
                cache_data = cache.get_data()
                if cache_data != task.cache:
                    task.set_cache(cache_data, self._word_extractor)
                    cache_mgr = TaskCacheManager(self._tasks_root)
                    cache_mgr.write_one_cache_to_db(task_cache=cache, db=self._db)
        self._db.commit()
        print('ready (caches updated)')

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

    def calc_words(self) -> Set[str]:
        words = set()
        for task in self._tasks.values():
            words |= task.last_revision.words

        return words

    def get_task(self, task_serial: int) -> Task:
        return self._tasks[task_serial]

    def extract_words(self, text: str) -> Set[str]:
        return self._word_extractor.get_words(text)

    def update_cache(self, timestamp: datetime, task_cache_list: List[TaskCache]) -> None:
        for cache in task_cache_list:
            cache_rel_path = cache.get_rel_path()
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
                raise Exception(cache_rel_path)

            task = self._tasks.get(cache.task_serial, None)
            if task is None:
                raise Exception(cache.task_serial)  # todo: show error dialog

            task_rel_path = task.get_rel_path()
            if task_rel_path != cache_rel_path:
                raise Exception(cache.task_serial, task_rel_path, cache_rel_path)  # todo: show error dialog

        cache_mgr = TaskCacheManager(self._tasks_root)
        task_caches = TaskCaches(
            update_datetime=timestamp,
            map={cache.task_serial: cache for cache in task_cache_list})
        cache_mgr.write_caches_to_db(task_caches=task_caches, db=self._db)

        # update task.cache
        for task in self._tasks.values():
            task.set_cache(None, self._word_extractor)
        for cache in task_caches.map.values():
            new_data = TaskCacheData(files_state=cache.files_state,
                                     readme=cache.readme,
                                     file_names=cache.file_names)
            self._tasks[cache.task_serial].set_cache(new_data, self._word_extractor)


class Task:

    def __init__(self, serial: int, revisions: List[TaskRevision], model: TaskModel):
        assert len(revisions) > 0
        for i, rev in enumerate(revisions):
            assert rev.rev_no == i

        self._serial = serial
        self._revisions = revisions

        self._model = model
        self._cache = None
        self._cache_words = set()
        self._word_parts = set()

    @property
    def serial(self):
        return self._serial

    @property
    def last_revision(self):
        return self._revisions[-1]

    @property
    def revisions(self):
        return self._revisions

    @property
    def cache(self):
        return self._cache

    @property
    def files_state(self):
        return self._cache.files_state if self._cache else TaskFilesState.NO_FILES

    def get_revision(self, rev_no: int) -> TaskRevision:
        return self._revisions[rev_no]

    def is_empty(self) -> bool:
        n = len(self._revisions)
        return n == 0 or n == 1 and self._revisions[0].rev_no == 0

    def get_header(self) -> str:
        n = len(self._revisions)
        rev_1st = self._revisions[1] if n >= 2 else self._revisions[0]
        rev_last = self._revisions[-1]
        return f'{rev_1st.date_str}: {rev_last.title}'

    def get_rgb(self) -> RGB:
        if self._cache:
            return self._cache.files_state.rgb()

    def create_new_revision(self, date: str, title: str, body: str, category: str) -> TaskRevision:
        new_rev_no = len(self._revisions)
        return TaskRevision(
            task_serial=self._serial,
            rev_no=new_rev_no,
            date=date,  # datetime.today().strftime('%y%m%d'),
            category=category,
            title=title,
            body=body,
            group_serial=0,
            word_extractor=self._model.word_extractor
        )

    def add_revision(self, task_rev: TaskRevision) -> None:
        assert len(self._revisions) == task_rev.rev_no
        self._revisions.append(task_rev)

    def create_dir(self, tasks_root: Path) -> None:
        assert self._cache is None
        task_dpath = tasks_root / self.get_rel_path()
        assert not task_dpath.exists()
        task_dpath.mkdir()
        self._create_meta_file(task_dpath)
        self._cache = TaskCacheData(files_state=TaskFilesState.ACTIVE,
                                    readme='',
                                    file_names='')

    def _create_meta_file(self, task_dpath: Path) -> None:
        meta_fpath = task_dpath / '.meta'
        stream = meta_fpath.open('w')
        meta_data = {'task_serial': self.serial}
        yaml.safe_dump(meta_data, stream)

    def zip_dir(self, tasks_root: Path) -> None:
        assert self._cache is not None
        assert self._cache.files_state == TaskFilesState.ACTIVE
        task_dpath = tasks_root / self.get_rel_path()
        assert task_dpath.exists()
        zipper = Zipper(task_dpath)
        zipper.start()
        self._cache.files_state = TaskFilesState.PASSIVE
        shutil.rmtree(task_dpath)

    def unzip_file(self, tasks_root: Path) -> None:
        assert self._cache is not None
        assert self._cache.files_state == TaskFilesState.PASSIVE
        zip_fpath = tasks_root / (self.get_rel_path() + '.zip')
        assert zip_fpath.exists()
        unzipper = Unzipper(zip_fpath)
        unzipper.start()
        self._cache.files_state = TaskFilesState.ACTIVE
        zip_fpath.unlink()

    def get_path(self, tasks_root: Path) -> Optional[Path]:
        if self._cache:
            files_state = self._cache.files_state
            rel_path = self.get_rel_path()
            if files_state == TaskFilesState.ACTIVE:
                return tasks_root / rel_path
            elif files_state == TaskFilesState.PASSIVE:
                return tasks_root / (rel_path + '.zip')

    def get_date_str(self) -> str:
        return self._revisions[1].date_str

    def get_rel_path(self) -> str:
        assert not self._revisions[0].date_str
        task_last_rev = self.last_revision
        title_fname = self._get_title_fname(task_last_rev.title)
        return f'{task_last_rev.category}/{self.get_date_str()}-{title_fname}'

    def get_title_fname(self) -> str:
        return self._get_title_fname(self.last_revision.title)

    @staticmethod
    def _get_title_fname(title: str) -> str:
        assert ':' not in title
        title_fname = title.replace(', ', '-').replace(' ', '-')
        assert ',' not in title_fname
        assert ' ' not in title_fname
        assert '--' not in title_fname
        return title_fname

    def set_cache(self, cache_data: Optional[TaskCacheData], word_extractor: WordExtractor):
        self._cache = cache_data
        self._cache_words.clear()
        if cache_data is not None:
            if cache_data.readme:
                self._cache_words |= word_extractor.get_words(cache_data.readme)
            if cache_data.file_names:
                self._cache_words |= word_extractor.get_words(cache_data.file_names)
        self._update_word_parts()

    def _update_word_parts(self) -> None:
        words = self._cache_words | self.last_revision.words
        self._word_parts = set(word[:n] for word in words for n in range(2, len(word) + 1))

    def does_meet_the_criteria(self, search_words: Iterable[str],
                               category: str, files_state: str) -> bool:
        task_rev = self.last_revision

        if category and category != task_rev.category:
            return False
        if files_state:
            if self.files_state.name.lower() != files_state:
                return False
        return self._contains_all_words(search_words)

    def _contains_all_words(self, words: Iterable[str]) -> bool:
        return set(words) <= self._word_parts


class TaskRevision:

    @staticmethod
    def create_default() -> TaskRevision:
        return TaskRevision(
            task_serial=0,
            rev_no=0,
            date='',
            category='',
            title='',
            body='',
            group_serial=0)

    def __init__(self, task_serial: int, rev_no: int,
                 date: str, category: str, title: str, body: str, group_serial: int,
                 word_extractor: Optional[WordExtractor] = None):
        self._task_serial = task_serial
        self._rev_no = rev_no
        self._date_str = self._norm_date_str(date)
        self._category = category
        self._title = title
        self._body = body
        self._group_serial = group_serial

        self._page = read_from_xmlstr(body, contains_page_element=False)
        self._words: Set[str] = set(self._iter_words(word_extractor)) if word_extractor else set()

    @staticmethod
    def _norm_date_str(date_str) -> str:
        normed_date = date_str
        if len(normed_date) % 2 == 1:
            normed_date = '0' + normed_date
        return normed_date

    def _iter_words(self, word_extractor: WordExtractor) -> Iterator[str]:
        yield from word_extractor.get_words(self._title)
        for inline_elem in self._page.iter_inline_elements():
            if inline_elem.text:
                yield from word_extractor.get_words(inline_elem.text)

    @property
    def task_serial(self):
        return self._task_serial

    @property
    def rev_no(self):
        return self._rev_no

    @property
    def date_str(self) -> str:
        return self._date_str

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
    def words(self):
        return self._words

    def get_values(self):
        return {
            'task_serial': self._task_serial,
            'rev_no': self._rev_no,
            'date': self._date_str,
            'category': self._category,
            'title': self._title,
            'body': self._body,
            'group_serial': self._group_serial,
        }

    def have_values_changed(self, new_values: Dict[str, Any]) -> bool:
        return self._title != new_values['title'] or \
               self._body != new_values['body'] or \
               self._category != new_values['category'] or \
               self._group_serial != new_values['group_serial']


class WordExtractor:
    _REX = re.compile(r"[a-zA-Z0-9äöüßÄÖÜ]+[a-zA-Z0-9äöüßÄÖÜ_\-]*[a-zA-Z0-9äöüßÄÖÜ]")

    def __init__(self, no_keywords_path: Path):
        lines = no_keywords_path.open(encoding='utf-8').readlines()
        self._no_keywords = set(line.strip() for line in lines)
        self._no_keywords.add('')

    def get_words(self, text: str) -> Set[str]:
        unfiltered_words = set(self._iter_words(text))
        return set(word for word in unfiltered_words if self._is_word_valid(word))

    def _iter_words(self, text: str) -> Iterator[str]:
        words = set(word.lower() for word in self._REX.findall(text))
        yield from words

        for word in words:
            word_parts = word.split('-')
            if len(word_parts) >= 2:
                yield from word_parts

    def _is_word_valid(self, word: str) -> bool:
        return len(word) >= 2 and word not in self._no_keywords
