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
from pathlib import Path
from typing import Optional, Dict, List, Iterable, Any, Iterator, Set

from tasks.db import Row, DB
from tasks.xml_reading import read_from_xmlstr


class TaskModel:

    def __init__(self, db: DB, keyword_extractor: KeywordExtractor):
        self._db = db
        self._tasks_revisions_table = self._db.table('tasks_revisions')
        self._keyword_extractor = keyword_extractor
        self._tasks: Dict[int, Task] = {}
        self._default_rev = TaskRevision.create_default(model=self)

    @property
    def tasks(self):
        return self._tasks.values()

    def read(self):
        self._db.open()
        self._tasks.clear()
        task_serial2revisions: Dict[int, List[TaskRevision]] = {}
        for row in self._tasks_revisions_table.select():
            task_rev = TaskRevision(model=self, **row)
            task_serial = task_rev.task_serial
            if task_serial not in task_serial2revisions:
                task_serial2revisions[task_serial] = [self._default_rev]
            task_serial2revisions[task_serial].append(task_rev)
        self._tasks = {serial: Task(serial, sorted(revs, key=lambda x: x.rev_no), self)
                       for serial, revs in task_serial2revisions.items()}

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

    def extract_keywords(self, text: str) -> List[str]:
        return self._keyword_extractor.get_keywords(text)


class Task:

    def __init__(self, serial: int, revisions: List[TaskRevision], model: TaskModel):
        assert len(revisions) > 0
        for i, rev in enumerate(revisions):
            assert rev.rev_no == i

        self._serial = serial
        self._revisions = revisions
        self._model = model

    @property
    def serial(self):
        return self._serial

    @property
    def last_revision(self):
        return self._revisions[-1]

    @property
    def revisions_list(self):
        return self._revisions

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
        self._part_keywords = set(word[:n] for word in self._keywords for n in range(2, len(word)))

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
