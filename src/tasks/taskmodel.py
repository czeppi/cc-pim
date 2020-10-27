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
from datetime import datetime
from functools import total_ordering
from typing import Optional, Dict, List, Iterable, Any, Iterator

from tasks.db import Row, DB
from tasks.xml_reader import read_from_xmlstr


class TaskModel:

    def __init__(self, db: DB, keyword_extractor: KeywordExtractor, overrides: Dict[str, str]):
        self._db = db
        self._tasks_revisions_table = self._db.table('tasks_revisions')
        self._keyword_extractor = keyword_extractor
        self._overrides = overrides
        self._tasks: Dict[int, Task] = {}
        self._tasks_revisions: Dict[int, TaskRevision] = {}

    @property
    def tasks(self):
        return self._tasks.values()

    def read(self):
        self._db.open()
        self._tasks.clear()
        self._tasks_revisions.clear()
        default_rev = TaskRevision.create_default(model=self)
        self._tasks_revisions[0] = default_rev
        task_serial2revisions: Dict[int, List[TaskRevision]] = {}
        for row in self._tasks_revisions_table.select():
            task_rev = TaskRevision(model=self, **row)
            self._tasks_revisions[task_rev.id] = task_rev
            task_serial = task_rev.task_serial
            if task_serial not in task_serial2revisions:
                task_serial2revisions[task_serial] = [default_rev]
            task_serial2revisions[task_serial].append(task_rev)
        self._tasks = {serial: Task(serial, revs, self) for serial, revs in task_serial2revisions.items()}

    def create_new_task(self, task_serial: Optional[int] = None) -> Task:
        if task_serial is None:
            task_serial = self._get_next_task_id()
        default_rev = self._tasks_revisions[0]
        return Task(task_serial, revisions=[default_rev], model=self)

    def _get_next_task_id(self) -> int:
        return max(self._tasks.keys()) + 1

    def add_task_revision(self, task_rev: TaskRevision) -> None:
        if task_rev.id == 0:
            raise Exception()

        task_serial = task_rev.task_serial
        if task_serial == '':
            raise Exception(str(task_rev.id))

        if task_serial not in self._tasks:
            self._tasks[task_serial] = self.create_new_task(task_serial)
        self._tasks[task_serial].add_revision(task_rev)
        self._tasks_revisions[task_rev.id] = task_rev

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
            keywords |= set(task.last_revision.keywords)
        return sorted(keywords)

    def search_tasks(self, with_keywords: Optional[List[str]] = None) -> List[Task]:
        if with_keywords is None:
            with_keywords = []
        result_tasks = []
        for id_ in sorted(self._tasks.keys()):
            task = self._tasks[id_]
            if len(with_keywords) == 0 or (set(with_keywords) & set(task.keywords)):
                result_tasks.append(task)
        return result_tasks

    def get_task(self, task_serial: int) -> Task:
        return self._tasks[task_serial]

    def get_task_revision(self, task_rev_id: int) -> TaskRevision:
        return self._tasks_revisions[task_rev_id]

    def get_next_task_revision_id(self) -> int:
        max_id = max(self._tasks_revisions.keys())
        return max_id + 1

    def extract_keywords(self, text: str) -> List[str]:
        return self._keyword_extractor.get_keywords(text)


@total_ordering
class TaskID:  # todo: use it

    def __init__(self, serial: int):
        self._serial = serial

    def __str__(self):
        return f'{self._serial:05}'

    def __eq__(self, other):
        return self._serial == other.serial

    def __lt__(self, other):
        return self._serial < other.serial

    @property
    def serial(self):
        return self._serial


class Task:

    def __init__(self, serial: int, revisions: List[TaskRevision], model: TaskModel):
        self._serial = serial
        self._revisions = {x.id: x for x in revisions}
        self._model = model
        self._first_revision = self._get_first_revision()
        self._last_revision = self._get_last_revision()

    def _get_first_revision(self) -> TaskRevision:
        first_revisions = set(x for x in self._revisions.values() if x.prev_id == 0)
        if len(first_revisions) != 1:
            raise Exception(self._serial)
        return first_revisions.pop()

    def _get_last_revision(self) -> TaskRevision:
        all_rev_ids = set(self._revisions.keys())
        referenced_rev_ids = set(x.prev_id for x in self._revisions.values())
        last_rev_id_list = list(all_rev_ids - referenced_rev_ids)
        if len(last_rev_id_list) != 1:
            raise Exception(f'{self._serial}, {all_rev_ids} - {referenced_rev_ids} => {last_rev_id_list}')
        last_rev_id = last_rev_id_list[0]
        return self._revisions[last_rev_id]

    @property
    def id(self):
        return self._serial

    @property
    def first_revision(self):
        return self._first_revision

    @property
    def last_revision(self):
        return self._last_revision

    @property
    def revisions_list(self):
        return self._revisions.values()

    def is_empty(self) -> bool:
        rev_ids = self._revisions.keys()
        return rev_ids == [] or rev_ids == [0]

    def get_header(self) -> str:
        return f'{self._first_revision.date}: {self._last_revision.title}'

    def create_new_revision(self, title: str, body: str, category: str) -> TaskRevision:
        return TaskRevision(
            id=self._model.get_next_task_revision_id(),
            prev_id=self._last_revision.id,
            task_serial=self._serial,
            date=datetime.today().strftime('%y%m%d'),
            category=category,
            title=title,
            body=body,
            model=self._model
        )

    def add_revision(self, task_rev: TaskRevision) -> None:
        self._revisions[task_rev.id] = task_rev
        self._last_revision = task_rev


class TaskRevision:

    @staticmethod
    def create_default(model) -> TaskRevision:
        return TaskRevision(
            id=0,
            prev_id=None,
            task_serial=0,
            date='',
            category='',
            title='',
            body='',
            model=model)

    def __init__(self, id: int, prev_id: Optional[int], task_serial: int,
                 date: str, category: str, title: str, body: str, model: TaskModel):
        self._id = id
        self._prev_id = prev_id
        self._task_serial = task_serial
        self._date = date
        self._category = category
        self._title = title
        self._body = body
        self._page = read_from_xmlstr(body, contains_page_element=False)
        self._model = model

    def get_values(self):
        return {
            'id': self._id,
            'prev_id': self._prev_id,
            'task_serial': self._task_serial,
            'date': self._date,
            'category': self._category,
            'title': self._title,
            'body': self._body,
            'model': self._model,
        }

    @property
    def id(self):
        return self._id

    @property
    def prev_id(self):
        return self._prev_id

    @property
    def prev(self):
        return self._model.get_task_revision(self._prev_id)

    @property
    def task_serial(self):
        return self._task_serial

    @property
    def task(self):
        return self._model.get_task(self._task_serial)

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
        title_keywords = set(self._model.extract_keywords(self._title))
        body_keywords = set(self._model.extract_keywords(self._body))
        return sorted(title_keywords | body_keywords)

    def contains_all_keyword(self, keywords: Iterable[str]) -> bool:
        return set(keywords) <= set(self.keywords)

    def get_header(self) -> str:
        # return '{}: {}'.format(self._date, self._title)
        # return '{}-{}: {}'.format(self._task_id[:6], self._task_id[6:].upper(), self._title)
        return self.task.get_header()

    def have_values_changed(self, new_values: Dict[str, Any]) -> bool:
        return self._title != new_values['title'] or \
               self._body != new_values['body'] or \
               self._category != new_values['category']


class KeywordExtractor:
    rex = re.compile(r"[a-zA-Z0-9_äöüßÄÖÜ.]+[a-zA-Z0-9_äöüßÄÖÜ\-.]*[a-zA-Z0-9_äöüßÄÖÜ.]")

    def __init__(self, no_keywords_pathname: str):
        lines = open(no_keywords_pathname, encoding='utf-8').readlines()
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
