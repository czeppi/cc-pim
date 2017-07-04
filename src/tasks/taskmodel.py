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
# Programm erhalten haben. Wenn nicht, siehe <http://www.gnu.org/licenses/>.

import re
from collections import defaultdict
from datetime import datetime
from docutils.core import publish_string

from tasks.metamodel import MetaModel
from tasks.db import DB
from tasks.db import Row


class TaskModel:

    def __init__(self, context):
        self._context = context
        path = context.sqlite3_pathname
        self._meta_model = MetaModel(context.logging_enabled)
        self._meta_model.read(context.metamodel_pathname)
        self._db = DB(context.sqlite3_pathname, self._meta_model, 
            logging_enabled=context.logging_enabled)
        self._tasks_revisions_table = self._db.table('tasks_revisions')
        self._keyword_extractor = KeywordExtractor(context.no_keywords_pathname)
        
    @property
    def tasks(self):
        return self._tasks.values()
        
    @property
    def context(self):
        return self._context
        
    def read(self):
        self._db.open()
        tasks_revisions_table = self._tasks_revisions_table
        self._tasks = {}  # id -> Task
        self._tasks_revisions = {}  # id -> TaskRevision
        default_rev = TaskRevision.create_default(model=self)
        self._tasks_revisions[0] = default_rev
        task_id2revisions = {}  # task_id -> list(TaskRevision)  # defaultdict(list)
        for row in self._tasks_revisions_table.select():
            task_rev = TaskRevision(model=self, **row)
            self._tasks_revisions[task_rev.id] = task_rev
            task_id = task_rev.task_id
            if task_id not in task_id2revisions:
                task_id2revisions[task_id] = [default_rev]
            task_id2revisions[task_id].append(task_rev)
        self._tasks = { id: Task(id, revs, self) for id, revs in task_id2revisions.items() }

    def create_new_task(self, task_id=None):
        if task_id is None:
            date_str = datetime.today().strftime('%y%m%d')
            task_id = self._get_next_task_id(date_str)
        default_rev = self._tasks_revisions[0]
        return Task(task_id, revisions=[default_rev], model=self)

    def _get_next_task_id(self, date_str):
        for i in range(1, 100):
            task_id = '{}-{:02}'.format(date_str, i)
            if task_id not in self._tasks:
                return task_id
        raise Exception()
        
    def add_task_revision(self, task_rev):
        if task_rev.id == 0:
            raise Exception()
            
        task_id = task_rev.task_id
        if task_id == '':
            raise Exception(str(task_rev.id))
            
        if task_id not in self._tasks:
            self._tasks[task_id] = self.create_new_task(task_id)
        self._tasks[task_id].add_revision(task_rev)
        self._tasks_revisions[task_rev.id] = task_rev
        
        self._write_task_revision(task_rev)
        
    def _write_task_revision(self, task_rev):
        tasks_revisions_table = self._tasks_revisions_table
        task_rev_values = task_rev.get_values()
        row_values = { x.name: task_rev_values[x.name] 
            for x in tasks_revisions_table.attributes }
        new_row = Row(table=tasks_revisions_table, values=row_values)
        tasks_revisions_table.insert_row(new_row)
        self._db.commit()
        
    def get_sorted_categories(self):
        cat_set = set(task.last_revision.category 
            for task in self._tasks.values() 
            if task.last_revision.category != '')
        return sorted(cat_set)
            
    def calc_keywords(self):
        keywords = set()
        for task in self._tasks.values():
            keywords |= set(task.last_revision.keywords)
        return sorted(keywords)
        
    def search_tasks(self, with_keywords=[]):
        result_tasks = []
        for id in sorted(self._tasks.keys()):
            task = self._tasks[id]
            if len(with_keywords) == 0 or (set(with_keywords) & set(task.keywords)):
                result_tasks.append(task)
        return result_tasks
        
    def get_task(self, task_id):
        return self._tasks[task_id]
        
    def get_task_revision(self, task_rev_id):
        return self._tasks_revisions[task_rev_id]
        
    def get_next_task_revision_id(self):
        max_id = max(self._tasks_revisions.keys())
        return max_id + 1
        
    def extract_keywords(self, text):
        return self._keyword_extractor.get_keywords(text)
        

class Task:

    def __init__(self, id, revisions, model):
        self._id = id
        self._revisions = { x.id: x for x in revisions }
        self._model = model
        self._init_first_revision()
        self._init_last_revision()
        
    def _init_first_revision(self):
        """ suche erste nicht-default-Revision
        """
        first_revisions = set(x for x in self._revisions.values() if x.prev_id == 0)
        if len(first_revisions) != 1:
            raise Exception(self._id)
        self._first_revision = first_revisions.pop()
        
    def _init_last_revision(self):
        all_rev_ids = set(self._revisions.keys())
        referenced_rev_ids = set(x.prev_id for x in self._revisions.values())
        last_rev_id_list = list(all_rev_ids - referenced_rev_ids)
        if len(last_rev_id_list) != 1:
            raise Exception('{}, {} - {} => {}'.format(self._id, all_rev_ids, referenced_rev_ids,last_rev_id_list))
        last_rev_id = last_rev_id_list[0]
        self._last_revision = self._revisions[last_rev_id]
    
    @property
    def id(self):
        return self._id
        
    @property
    def first_revision(self):
        return self._first_revision
        
    @property
    def last_revision(self):
        return self._last_revision
        
    @property
    def revisions_list(self):
        return self._revisions.values()
        
    def is_empty(self):
        rev_ids = self._revisions.keys()
        return rev_ids == [] or rev_ids == [0]
        
    def get_header(self):
        return '{}: {}'.format(self._first_revision.date, self._last_revision.title)
        
    def create_new_revision(self, title, body, category):
        return TaskRevision(
            id=self._model.get_next_task_revision_id(),
            prev_id=self._last_revision.id,
            task_id=self._id,
            date=datetime.today().strftime('%y%m%d'),
            category=category,
            title=title,
            body=body,
            model=self._model
        )
        
    def add_revision(self, task_rev):
        self._last_revision = task_rev
        

class TaskRevision:

    @staticmethod
    def create_default(model):
        return TaskRevision(
            id=0,
            prev_id=None,
            task_id='',
            date='',
            category='',
            title='',
            body='',
            model=model)
    
    def __init__(self, id, prev_id, task_id, date, category, title, body, model):
        self._id = id
        self._prev_id = prev_id
        self._task_id = task_id
        self._date = date
        self._category = category
        self._title = title
        self._body = body
        self._model = model
        
    def get_values(self):
        return {
            'id': self._id,
            'prev_id': self._prev_id,
            'task_id': self._task_id,
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
    def task_id(self):
        return self._task_id
        
    @property
    def task(self):
        return self._model.get_task(self._task_id)
        
    @property
    def date(self):
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
    def category(self):
        return self._category

    @property
    def keywords(self):
        title_keywords = set(self._model.extract_keywords(self._title))
        body_keywords  = set(self._model.extract_keywords(self._body))
        return sorted(title_keywords | body_keywords)
        
    def contains_all_keyword(self, keywords):
        return set(keywords) <= set(self.keywords)
        
    def get_header(self):
        #return '{}: {}'.format(self._date, self._title)
        #return '{}-{}: {}'.format(self._task_id[:6], self._task_id[6:].upper(), self._title)
        return self.task.get_header()
        
    def get_rst_text(self):
        header = self.get_header()
        rst_text = '{}\n{}\n\n{}'.format(header, len(header) * '=', self._body)
        return rst_text
        
    def get_html_text(self):
        rst_text = self.get_rst_text()
        html_text = self.rst2html(rst_text)
        return html_text
        
    def rst2html(self, rst_text):
        context = self._model.context
        overrides = {
            'template':        context.template_pathname,
            'stylesheet_path': context.user_css_pathname,
        }
        html_bytes = publish_string(rst_text, writer_name='html', 
            settings_overrides=overrides)
        html_text = str(html_bytes, encoding='utf-8')
        return html_text
       
    def have_values_changed(self, new_values):
        return self._title != new_values['title'] or \
            self._body != new_values['body'] or \
            self._category != new_values['category']
           

class KeywordExtractor:

    rex = re.compile(r"[a-zA-Z0-9_äöüßÄÖÜ\.]+[a-zA-Z0-9_äöüßÄÖÜ\-\.]*[a-zA-Z0-9_äöüßÄÖÜ\.]")
    
    def __init__(self, no_keywords_pathname):
        lines = open(no_keywords_pathname, encoding='utf-8').readlines()
        self._no_keywords = set(line.strip() for line in lines)
        self._no_keywords.add('')
    
    def get_keywords(self, title):
        keywords = self.rex.findall(title)
        return list(self._filter_keywords(keywords))
        
    def _filter_keywords(self, keywords):
        for keyword in keywords:
            kw = keyword.lower()
            while len(kw) > 0 and not self._is_alnum(kw[0]):
                kw = kw[1:]
            while len(kw) > 0 and not self._is_alnum(kw[-1]):
                kw = kw[:-1]
            if kw not in self._no_keywords:
                yield keyword.lower()
                
    def _is_alnum(self, ch):
        return ch.isalnum() or ch in ['ä', 'ö', 'ü', 'ß', 'Ä', 'Ö', 'Ü']
        