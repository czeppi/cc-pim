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
#------------------------------------------------------------------------------

class Repo:

    def __init__(self, path):
        self._path = path
        self._conn = ...
        self._revisions = []
        self._logging_enabled = False

    def update(self):
        pass
        
    def commit(self, comment, changes):
        new_revision_number = ...
        cur_timestamp = ...
        new_revision = Revision(new_revision_number, cur_timestamp, comment, changes)
        
    def get_contacts(self, revision_number=None):
        revisions = self._revisions if (revision_number is None) else self._revisions[:revision_number+1]
        contacts = Contacts()
        for revision in revisions:
            for attr_change in revision.changes:
                self._update_contacts(contacts, attr_change)
        return contacts
            
    def _update_contacts(self, contacts, attr_change):
            
   
   
   
   
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

    def _sql_execute(self, sql_cmd):
        if self._logging_enabled:
            print(sql_cmd)
            
        cursor = self._conn.cursor() 
        cursor.execute(sql_cmd)
        return cursor
    
#------------------------------------------------------------------------------

class Relation:

    def __init__(self, serial, subject, predicate, object):
        self._serial = serial
        self._subject = subject
        self._predicate = predicate
        self._object = object

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
        
class Revision: # alias Commit

    def __init__(self, serial, timestamp, comment="", changes=[]):
        self._serial = serial
        self._timestamp = timestamp
        self._comment = comment
        self._changes = changes
        
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
    def changes(self):
        return self._changes
        
#------------------------------------------------------------------------------
  
class FactChange:

    def __init__(self, serial, fact, revision_serial):
        self.serial = serial
        self.fact = fact
        self.revision_serial = revision_serial







#------------------------------------------------------------------------------
  
class AttributeChange:

    def __init__(self, attr, value):
        self._attr = attr
        self._value = value

    @property
    def attr(self):
        return self._attr
        
    @property
    def obj_type(self):
        return self._attr.obj_type

    @property
    def attr_name(self):
        return self._attr.name
        
    @property
    def value(self):
        return self._value
        
#------------------------------------------------------------------------------

class Attribute:

    def __init__(self, obj_type, name):
        self._obj_type = obj_type
        self._name = name
        
    @property
    def obj_type(self):
        return self._obj_type

    @property
    def name(self):
        return self._name

