# Copyright (C) 2015  Christian Czepluch
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

from __future__ import annotations
import sqlite3
import time
from pathlib import Path
from typing import Dict, Set, Optional, Iterable, Tuple

from contacts.basetypes import VagueDate, Fact


class Repository:

    def __init__(self, db_source=':memory:'):
        self._db_source = db_source
        self._revisions: Dict[int, Revision] = {}
        self._logging_enabled: bool = False
        self._create_conn()
        self._committed_date_serial_set: Set[int] = set()
        self._committed_fact_serial_set: Set[int] = set()
        self._uncommitted_date_serial_set: Set[int] = set()
        self._uncommitted_fact_serial_set: Set[int] = set()

    def _create_conn(self) -> None:
        exists_db = self._exists_db()
        self._conn = sqlite3.connect(str(self._db_source))
        self._conn.row_factory = sqlite3.Row
        if not exists_db:
            self._create_db()

    def _exists_db(self) -> bool:
        if self._db_source == ':memory:':
            return False
        else:
            return self._get_db_path().exists()

    def _get_db_path(self):
        if isinstance(self._db_source, Path):
            return self._db_source
        else:
            return Path(self._db_source)

    def _create_db(self) -> None:
        self._execute_sql("create table revisions (serial integer primary key, timestamp int, comment text)")
        self._execute_sql("create table dates (serial integer, revision int, date text)")
        self._execute_sql("create table facts (serial integer, revision int, predicate int, subject int, value text, " +
                          "note text, date_begin int, date_end int, is_valid int)")
        self._conn.commit()

    def count_revisions(self) -> int:
        return len(self._revisions)

    def get_new_date_serial(self) -> int:
        dates = self._committed_date_serial_set | self._uncommitted_date_serial_set
        new_serial = 1 if len(dates) == 0 else max(dates) + 1
        self._uncommitted_date_serial_set.add(new_serial)
        return new_serial

    def get_new_fact_serial(self) -> int:
        facts = self._committed_fact_serial_set | self._uncommitted_fact_serial_set
        new_serial = 1 if len(facts) == 0 else max(facts) + 1
        self._uncommitted_fact_serial_set.add(new_serial)
        return new_serial

    def reload(self) -> None:
        self._revisions.clear()
        self._load_revisions()
        self._load_dates()
        self._load_facts()

    def _load_revisions(self) -> None:
        for rev_no, timestamp, comment in self._execute_sql("select serial, timestamp, comment from revisions"):
            new_rev = Revision(rev_no, timestamp, comment)
            self._revisions[rev_no] = new_rev

    def _load_dates(self) -> None:
        for serial, rev_no, date_str in self._execute_sql("select serial, revision, date from dates"):
            self._revisions[rev_no].date_changes[serial] = VagueDate(date_str, serial=serial)

    def _load_facts(self) -> None:
        for serial, rev_no, predicate_serial, subject_serial, value, \
            note, date_begin_serial, date_end_serial, is_valid \
                in self._execute_sql("select serial, revision, predicate, subject, value, note, " +
                                     "date_begin, date_end, is_valid from facts"):
            self._revisions[rev_no].fact_changes[serial] = \
                Fact(serial, predicate_serial, subject_serial, value,
                     note, date_begin_serial, date_end_serial, is_valid)

    def update(self) -> None:
        pass

    def commit(self, comment: str,
               date_changes: Dict[int, VagueDate],
               fact_changes: Dict[int, Fact]) -> Revision:
        rev_no = max(self._revisions.keys(), default=0) + 1
        now = time.time()
        new_rev = Revision(rev_no, now, comment, date_changes, fact_changes)
        self._execute_sql("insert into revisions (serial, timestamp, comment) values (?, ?, ?)",
                          (rev_no, now, comment))
        self._revisions[rev_no] = new_rev

        for date_serial, date in new_rev.date_changes.items():
            self._execute_sql("insert into dates (serial, revision, date) values (?, ?, ?)",
                              (date_serial, rev_no, str(date)))
            if date_serial in self._uncommitted_date_serial_set:
                self._uncommitted_date_serial_set.remove(date_serial)
                self._committed_date_serial_set.add(date_serial)

        for fact_serial, fact in new_rev.fact_changes.items():
            self._execute_sql("insert into facts (serial, revision, predicate, subject, value, " +
                              "note, date_begin, date_end, is_valid) values (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                              (fact_serial, rev_no, fact.predicate_serial, fact.subject_serial, fact.value,
                               fact.note, fact.date_begin_serial, fact.date_end_serial, fact.is_valid))
            if fact_serial in self._uncommitted_fact_serial_set:
                self._uncommitted_fact_serial_set.remove(fact_serial)
                self._committed_fact_serial_set.add(fact_serial)
        self._conn.commit()

        return new_rev

    # def get_contacts(self, revision_number=None):
    #     revisions = self._revisions if (revision_number is None) else self._revisions[:revision_number+1]
    #     contacts = Contacts()
    #     for revision in revisions:
    #         for attr_change in revision.changes:
    #             self._update_contacts(contacts, attr_change)
    #     return contacts

    # def _update_contacts(self, contacts, attr_change):

    def _select_one(self, col_names: Iterable[str], table_name: str, where: Optional[str] = None) -> sqlite3.Row:
        cursor = self._select(col_names, table_name, where)
        return cursor.fetchone()

    def _select_all(self, col_names: Iterable[str], table_name: str,
                    where: Optional[str] = None) -> Iterable[sqlite3.Row]:
        cursor = self._select(col_names, table_name, where)
        return cursor.fetchall()

    def _select(self, col_names: Iterable[str], table_name: str, where: Optional[str] = None) -> sqlite3.Cursor:
        columns_str = ', '.join(col_names)
        sql_cmd = f"select {columns_str} from {table_name}"
        if where:
            sql_cmd += " where " + where
        cursor = self._execute_sql(sql_cmd)
        return cursor

    def _execute_sql(self, sql_cmd: str, values=None) -> sqlite3.Cursor:
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

    def get_revision(self, rev_no: int) -> Revision:
        return self._revisions[rev_no]

    def aggregate_revisions(self, rev_begin: Optional[int] = None,
                            rev_end: Optional[int] = None) -> Tuple[Dict[int, VagueDate], Dict[int, Fact]]:
        date_changes = {}
        fact_changes = {}
        for rev_no in sorted(self._revisions.keys()):
            if (rev_begin is None or rev_no >= rev_begin) \
                    and (rev_end is None or rev_no < rev_end):
                rev = self._revisions[rev_no]
                date_changes.update(rev.date_changes)
                fact_changes.update(rev.fact_changes)
        return date_changes, fact_changes


class Revision:  # alias Commit

    def __init__(self, serial: int,
                 timestamp: Optional[float] = None,
                 comment: str = "",
                 date_changes: Optional[Dict[int, VagueDate]] = None,
                 fact_changes: Optional[Dict[int, Fact]] = None):
        self._serial = serial
        if timestamp is None:
            timestamp = time.time()
        self._timestamp = timestamp
        self._comment = comment
        self._date_changes: Dict[int, VagueDate] = {} if date_changes is None else date_changes
        self._fact_changes: Dict[int, Fact] = {} if fact_changes is None else fact_changes  # serial -> Fact

    @property
    def serial(self) -> int:
        return self._serial

    @property
    def timestamp(self) -> float:
        return self._timestamp

    @property
    def comment(self) -> str:
        return self._comment

    @property
    def date_changes(self) -> Dict[int, VagueDate]:
        return self._date_changes

    @property
    def fact_changes(self) -> Dict[int, Fact]:
        return self._fact_changes
