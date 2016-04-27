#! /usr/bin/env python3

# Copyright (C) 2015  Christian Czepluch
#
# This file is part of CC-PIM.
#
# CC-Notes is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# CC-Notes is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with CC-Notes.  If not, see <http://www.gnu.org/licenses/>.
# Programm erhalten haben. Wenn nicht, siehe <http://www.gnu.org/licenses/>.

"""
    data_dir = config.get_data_dir()
    repo_path = data_dir / 'contact.db'
    
    repo = Repo(repo_path)
    contacts = repo.update(revision_number=None)
    
    
    use cases
    =========
    
    find person
    -----------
    - input: search_text etc.
    - output: list of persons
    - code:
        persons = contacts.find_persons(search_text)
    
    show person
    -----------
    - show details of a special person
    - code:
        for attr in person.iter_attributes():
           name  = attr.name    
           value = attr.value
    
    edit person
    -----------
    - update:
        #person.update()
        contacts.update()
        person = contacts.get_person(person_id)
    - change attribute-values
        new_values = person_dialog.get_values()
    - commit changes
        contacts.commit(person, new_values)
        => evtl. merge_dialog bei Konflikten

"""

import sqlite3
import time
from pathlib import Path
from modeling.basetypes import VagueDate


class Repository:

    def __init__(self, db_source=':memory:'):
        self._db_source = db_source
        self._revisions = {}
        self._logging_enabled = False
        self._create_conn()
        self._commited_date_serial_set = set()
        self._commited_fact_serial_set = set()
        self._uncommited_date_serial_set = set()
        self._uncommited_fact_serial_set = set()

    def _create_conn(self):
        exists_db = self._exists_db()
        self._conn = sqlite3.connect(str(self._db_source))
        self._conn.row_factory = sqlite3.Row
        if not exists_db:
            self._create_db()

    def _exists_db(self):
        if self._db_source == ':memory:':
            return False
        else:
            return self._get_db_path().exists()

    def _get_db_path(self):
        if isinstance(self._db_source, Path):
            return self._db_source
        else:
            return Path(self._db_source)

    def _create_db(self):
        self._execute_sql("create table revisions (serial integer primary key, timestamp int, comment text)")
        self._execute_sql("create table dates (serial integer, revision int, date text)")
        self._execute_sql("create table facts (serial integer, revision int, predicate int, subject int, value text, note text, date_begin int, date_end int)")
        self._conn.commit()

    def count_revisions(self):
        return len(self._revisions)

    def get_new_date_serial(self):
        dates = self._commited_date_serial_set | self._uncommited_date_serial_set
        new_serial = 1 if len(dates) == 0 else max(dates) + 1
        self._uncommited_date_serial_set.add(new_serial)
        return new_serial

    def get_new_fact_serial(self):
        facts = self._commited_fact_serial_set | self._uncommited_fact_serial_set
        new_serial = 1 if len(facts) == 0 else max(facts) + 1
        self._uncommited_fact_serial_set.add(new_serial)
        return new_serial

    def reload(self):
        self._revisions.clear()
        self._load_revisions()
        self._load_dates()
        self._load_facts()

    def _load_revisions(self):
        for rev_no, timestamp, comment in self._execute_sql("select serial, timestamp, comment from revisions"):
            new_rev = Revision(rev_no, timestamp, comment)
            self._revisions[rev_no] = new_rev

    def _load_dates(self):
        for serial, rev_no, date_str in self._execute_sql("select serial, revision, date from dates"):
            self._revisions[rev_no].dates[serial] = VagueDate(date_str)

    def _load_facts(self):
        for serial, rev_no, predicate_serial, subject_serial, value, note, date_begin_serial, date_end_serial \
        in self._execute_sql("select serial, revision, predicate, subject, value, note, date_begin, date_end from facts"):
            self._revisions[rev_no].fact_changes[serial] = Fact(serial, predicate_serial, subject_serial, value, note, date_begin_serial, date_end_serial)

    def update(self):
        pass
        
    def commit(self, comment, date_changes, fact_changes):
        rev_no = len(self._revisions) + 1
        now = time.time()
        new_rev = Revision(rev_no, now, comment, date_changes, fact_changes)
        self._execute_sql("insert into revisions (serial, timestamp, comment) values (?, ?, ?)", (rev_no, now, comment))
        for date_serial, date in new_rev.date_changes.items():
            self._execute_sql("insert into dates (serial, revision, date) values (?, ?, ?)", (date_serial, rev_no, str(date)))
            if date_serial in self._uncommited_date_serial_set:
                self._uncommited_date_serial_set.remove(date_serial)
                self._commited_date_serial_set.add(date_serial)
        for fact_serial, fact in new_rev.fact_changes.items():
            self._execute_sql("insert into facts (serial, revision, predicate, subject, value, note, date_begin, date_end) values (?, ?, ?, ?, ?, ?, ?, ?)",
                              (fact_serial, rev_no, fact.predicate_serial, fact.subject_serial, fact.value, fact.note, fact.date_begin_serial, fact.date_end_serial))
            if fact_serial in self._uncommited_fact_serial_set:
                self._uncommited_fact_serial_set.remove(fact_serial)
                self._commited_fact_serial_set.add(fact_serial)
        self._conn.commit()
        return new_rev


    # def get_contacts(self, revision_number=None):
    #     revisions = self._revisions if (revision_number is None) else self._revisions[:revision_number+1]
    #     contacts = Contacts()
    #     for revision in revisions:
    #         for attr_change in revision.changes:
    #             self._update_contacts(contacts, attr_change)
    #     return contacts
            
    #def _update_contacts(self, contacts, attr_change):

    def _select_one(self, col_names, table_name, where=None):
        cursor = self._select(col_names, table_name, where)
        return cursor.fetchone()
    
    def _select_all(self, col_names, table_name, where=None):
        cursor = self._select(col_names, table_name, where)
        return cursor.fetchall()
        
    def _select(self, col_names, table_name, where=None):
        columns_str = ', '.join(col_names)
        sql_cmd = "select {} from {}".format(columns_str, table_name)
        if where:
            sql_cmd += " where " + where
        cursor = self._sql_execute(sql_cmd)
        return cursor

    def _execute_sql(self, sql_cmd, values=None):
        cursor = self._conn.cursor()
        if values is None:
            if self._logging_enabled:
                print(sql_cmd)
            cursor.execute(sql_cmd)
        else:
            if self._logging_enabled:
                print(sql_cmd, values)
            cursor.execute(sql_cmd, values)
        return cursor

    def get_revision(self, rev_no):
        return self._revisions[rev_no]

    def aggregate_revisions(self, rev_begin=None, rev_end=None):
        date_changes = {}
        fact_changes = {}
        for rev_no in sorted(self._revisions.keys()):
            if  (rev_begin is None or rev_no >= rev_begin) \
            and (rev_end   is None or rev_no < rev_end):
                rev = self._revisions[rev_no]
                date_changes.update(rev.date_changes)
                fact_changes.update(rev.fact_changes)
        return date_changes, fact_changes

    
class Revision: # alias Commit

    def __init__(self, serial, timestamp=None, comment="", date_changes={}, fact_changes={}):
        self._serial = serial
        if timestamp is None:
            timestamp = time.time()
        self._timestamp = timestamp
        self._comment = comment
        self._date_changes = date_changes  # serial -> VagueDate
        self._fact_changes = fact_changes  # serial -> Fact
        
    @property
    def serial(self):
        return self._serial

    @property
    def timestamp(self):
        return self._timestamp

    @property
    def comment(self):
        return self._comment

    @property
    def date_changes(self):
        return self._date_changes
        
    @property
    def fact_changes(self):
        return self._fact_changes

        
class Fact:

    def __init__(self, serial, predicate_serial, subject_serial, value, note=None, date_begin_serial=None, date_end_serial=None):
        self.serial = serial
        self.predicate_serial = predicate_serial
        self.subject_serial = subject_serial
        self.value = value
        self.date_begin_serial = date_begin_serial
        self.date_end_serial = date_end_serial
        self.note = note

    def copy(self):
        return Fact(
            serial=self.serial,
            predicate_serial=self.predicate_serial,
            subject_serial=self.subject_serial,
            value=self.value,
            note=self.note,
            date_begin_serial=self.date_begin_serial,
            date_end_serial=self.date_end_serial
        )


# class FactData:
#
#     def __init__(self, predicate_serial, object_serial, value, note=None, date_begin=None, date_end=None):
#         self.predicate_serial = predicate_serial
#         self.object_serial = object_serial
#         self.value = value
#         self.date_begin = date_begin
#         self.date_end = date_end
#         self.note = note


# class FactChange:
#
#     def __init__(self, serial, fact, revision_serial):
#         self.serial = serial
#         self.fact = fact
#         self.revision_serial = revision_serial
    
    
    
    
    
    
    
    
    
#------------------------------------------------------------------------------

# class Relation:

    # def __init__(self, serial, subject, predicate, object):
        # self._serial = serial
        # self._subject = subject
        # self._predicate = predicate
        # self._object = object

#------------------------------------------------------------------------------

# class Database:

    # def __init__(self, path):
        # self._path = path
        # self._conn = ...
        # self._commits = []
        # self._logging_enabled = False
        
    # def update(self, model):
        # local_serial  = model.commit_serial
        # remote_serial = self.read_last_commit_serial()
    
        # for serial in range(local_serial + 1, remote_serial + 1):
            # for relation in ....:
                # self._select('... in relation where commit="serial")
        

    # def commit(self):
    
    # def read_last_commit_serial(self):
        # pass
        
    # def _select_one(self, col_names, table_name, where=None):
        # cursor = self._select(col_names, table_name, where)
        # return cursor.fetchone()
    
    # def _select_all(self, col_names, table_name, where=None):
        # cursor = self._select(col_names, table_name, where)
        # return cursor.fetchall()
        
    # def _select(self, col_names, table_name, where=None):
        # columns_str = ', '.join(col_names)
        # sql_cmd = "select {} from {}".format(columns_str, table_name)
        # if where:
            # sql_cmd += " where " + where
        # cursor = self._sql_execute(sql_cmd)
        # return cursor

    # def _sql_execute(self, sql_cmd):
        # if self._logging_enabled:
            # print(sql_cmd)
            
        # cursor = self._conn.cursor() 
        # cursor.execute(sql_cmd)
        # return cursor
        
#------------------------------------------------------------------------------
        
#------------------------------------------------------------------------------
  







# # ------------------------------------------------------------------------------
  
# class AttributeChange:

    # def __init__(self, attr, value):
        # self._attr = attr
        # self._value = value

    # @property
    # def attr(self):
        # return self._attr
        
    # @property
    # def obj_type(self):
        # return self._attr.obj_type

    # @property
    # def attr_name(self):
        # return self._attr.name
        
    # @property
    # def value(self):
        # return self._value
        
# # ------------------------------------------------------------------------------

# class Attribute:

    # def __init__(self, obj_type, name):
        # self._obj_type = obj_type
        # self._name = name
        
    # @property
    # def obj_type(self):
        # return self._obj_type

    # @property
    # def name(self):
        # return self._name

