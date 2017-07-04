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

import os
import sqlite3

from context import Context
from tasks.metamodel import MetaModel


class DB:

    def __init__(self, sqlite_path, meta_model, logging_enabled=False):
        self._sqlite_path = sqlite_path
        self._meta_model = meta_model
        self._logging_enabled = logging_enabled
        self._init_tables()
        
    def _init_tables(self):
        self._tables = {}
        for struct in self.meta_model.structures:
            new_table = Table(struct, self)
            self._tables[struct.name] = new_table

    @property
    def meta_model(self):
        return self._meta_model
        
    @property
    def tables(self):
        return self._tables.values()
        
    def table(self, table_name):
        return self._tables[table_name]
        
    @property
    def conn(self):
        return self._conn
        
    def create(self):
        self._del_db_if_exists()
        self.open()
        self._create_tables()
        self._conn.commit()
        
    def _del_db_if_exists(self):
        if self._sqlite_path.exists():
            self._sqlite_path.remove()
            
    def _create_tables(self):
        for table in self.tables:
            table.create()
            
    def open(self):
        self._conn = sqlite3.connect(self._sqlite_path)
        self._conn.row_factory = sqlite3.Row
        
    def execute_sql(self, sql_cmd):
        if self._logging_enabled:
            print(sql_cmd)
        cursor = self._conn.cursor() 
        cursor.execute(sql_cmd)
        return cursor
        
    def commit(self):
        self._conn.commit()
        

class Table:

    def __init__(self, struct, db):
        self._struct = struct
        self._db = db
        
    @property
    def name(self):
        return self._struct.name
        
    @property
    def attributes(self):
        return self._struct.attributes
        
    def attribute(self, name):
        return self._struct.attribute(name)
        
    def create(self):
        fields = [x.name + ' ' + x.type.get_sqlite3_typename()
                  for x in self.attributes]
        sql_cmd = "create table {} ({})".format(
            self.name, ', '.join(fields))
        self._execute_sql(sql_cmd)
        
    def insert_row(self, row):
        values = ['"{}"'.format(row.value(x.name)) for x in self.attributes]
        sql_cmd = 'insert into {} values ({})'.format(
            self.name, ', '.join(values))
        self._execute_sql(sql_cmd)
        
    def update_row(self, id, values):
        row = Row(values, self)
        value_list = ['{}="{}"'.format(x, row.value(x)) for x in row.value_keys()]
        sql_cmd = 'update {} set {} where id = "{}"'.format(
            self.name, ', '.join(value_list), id)
        self._execute_sql(sql_cmd)
        self._db.commit()
        
    def select(self, col_names=[], where_str=''):
        if not col_names:
            col_names = '*'
        sql_cmd = "select {} from {} {}".format(col_names, self.name, where_str)
        cursor = self._execute_sql(sql_cmd)
        return cursor.fetchall()
        
    def _execute_sql(self, sql_cmd):
        return self._db.execute_sql(sql_cmd)
        

class Row:

    def __init__(self, values, table):
        self._values = values
        self._table = table
        
    def value(self, key):
        value = self._values[key]
        attribute = self._table.attribute(key)
        return attribute.type.convert_to_db(value)
        
    def value_keys(self):
        return [x.name for x in self._table.attributes if x.name in self._values]
        
    
if __name__ == '__main__':
    context = Context()
    meta_model = MetaModel(context.logging_enabled)
    meta_model.read(context.metamodel_pathname)
    db = DB(context.sqlite3_pathname, meta_model)
    db.create()
