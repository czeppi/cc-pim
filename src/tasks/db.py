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
import sqlite3
from pathlib import Path
from typing import Dict, ValuesView, Optional, Any

from tasks.metamodel import MetaModel, Structure


class DB:

    def __init__(self, sqlite_path: Path, meta_model_: MetaModel, logging_enabled: bool = False):
        self._sqlite_path = sqlite_path
        self._meta_model = meta_model_
        self._logging_enabled = logging_enabled
        self._tables = self._create_table_map(meta_model_)
        self._conn: Optional[sqlite3.Connection] = None
        
    def _create_table_map(self, meta_model_: MetaModel) -> Dict[str, Table]:
        tables = {}
        for struct in meta_model_.structures:
            new_table = Table(struct, self)
            tables[struct.name] = new_table
        return tables

    @property
    def meta_model(self) -> MetaModel:
        return self._meta_model
        
    @property
    def tables(self) -> ValuesView[Table]:
        return self._tables.values()
        
    def table(self, table_name: str) -> Table:
        return self._tables[table_name]
        
    @property
    def conn(self) -> sqlite3.Connection:
        return self._conn
        
    def create(self) -> None:
        self._del_db_if_exists()
        self.open()
        self._create_tables()
        self._conn.commit()
        
    def _del_db_if_exists(self) -> None:
        if self._sqlite_path.exists():
            self._sqlite_path.unlink()
            
    def _create_tables(self) -> None:
        for table in self.tables:
            table.create()
            
    def open(self) -> None:
        sqlite_pathname = str(self._sqlite_path)
        self._conn = sqlite3.connect(sqlite_pathname)
        self._conn.row_factory = sqlite3.Row
        
    def execute_sql(self, sql_cmd: str) -> sqlite3.Cursor:
        if self._logging_enabled:
            print(sql_cmd)
        cursor = self._conn.cursor()
        cursor.execute(sql_cmd)
        return cursor
        
    def commit(self) -> None:
        self._conn.commit()
        

class Table:

    def __init__(self, struct: Structure, db_: DB):
        self._struct = struct
        self._db = db_
        
    @property
    def name(self) -> str:
        return self._struct.name
        
    @property
    def attributes(self):
        return self._struct.attributes
        
    def attribute(self, name: str):
        return self._struct.attribute(name)
        
    def create(self) -> None:
        fields = [x.name + ' ' + x.type.sqlite3_typename
                  for x in self.attributes]
        fields_str = ', '.join(fields)
        sql_cmd = f"create table {self.name} ({fields_str})"
        self._execute_sql(sql_cmd)

    def clear(self) -> None:
        sql_cmd = f"delete from {self.name}"
        self._execute_sql(sql_cmd)

    def insert_row(self, row: Row) -> None:
        values = [f'"{row.value(x.name)}"' for x in self.attributes]
        values_str = ', '.join(values)
        sql_cmd = f'insert into {self.name} values ({values_str})'
        self._execute_sql(sql_cmd)
        
    def update_row(self, values: Dict[str, Any], where_str: str) -> None:
        value_list = [f'{key}="{value}"' for key, value in values.items()]
        values_str = ', '.join(value_list)
        sql_cmd = f'update {self.name} set {values_str} where {where_str}'
        self._execute_sql(sql_cmd)

    def select(self, where_str: str = ''):
        sql_cmd = f"select * from {self.name}"
        if where_str:
            sql_cmd += f' where {where_str}'
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
