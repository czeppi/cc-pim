##########################################
## CC-PIM                               ##
## Copyright 2013 by Christian Czepluch ##
##########################################

from collections import OrderedDict
from enum import Enum
import datetime

#-------------------------------------------------------------------------------

class Model:
    def __init__(self):
        self._tables = {}  # name -> Table
        
    def add_table(self, name:str):
        if name in self._tables:
            raise Exception(name)
        new_table = Table(name)
        self._tables[new_table] = new_table
        
    def remove_table(self, name:str):
        assert isinstance(name, str)
        if name not in self._tables:
            raise Exception(name)
        del self._tables[name]
        
    def rename_table(self, old_name:str, new_name:str):
        assert isinstance(old_name, str)
        assert isinstance(new_name, str)
        if old_name not in self._tables:
            raise Exception(old_name)
        if new_name in self._tables:
            raise Exception(new_name)
        self._tables[new_name] = self._tables[old_name]
        del self._tables[name]
        
    def find_table(self, table_name):
        return self._tables(table_name, None)
        
#-------------------------------------------------------------------------------
    
class Table:
    def __init__(self, name:str):
        assert isinstance(name, str)
        self._name = name
        self._columns = OrderedDict()
        self._next_row_id = 1
        self._rows = {}  # serial => Row
        
    @property
    def name(self):
        return self._name
        
    @property
    def columns(self):
        return self._columns.values()
        
    def new_row_id(self):
        new_row_id = self._next_row_id
        self._next_row_id += 1
        return new_row_id
        
    def add_col(self, name:str, type:'ColumnType'):
        assert isinstance(name, str)
        assert isinstance(type, ColumnType)
        if name in self.columns:
            raise Exception('{} {}'.format(self.name, name))
        new_col = Column(self, name, type)
        self.columns.append(new_col)
        return new_col
        
    def remove_col(self, name:str):
        assert isinstance(name, str)
        if name not in self.columns:
            raise Exception('{} {}'.format(self.name, name))
        del self._columns[name]
        
    def add_row(self, data):
        new_row_id = self.new_row_id()
        new_row = Row(self, new_row_id, data)
        self._rows[new_row_id] = new_row
        return new_row
        
    def remove_row(self, row_id:int):
        assert isinstance(row_id, int)
        if row_id not in self._rows:
            raise Exception(str(row_id))
        del self._rows[new_row_id]
        
    def set_value(self, row_id:int, col_name:str, new_value):
        assert isinstance(row_id, int)
        assert isinstance(col_name, str)
        if row_id not in self._rows:
            raise Exception('{} {}'.format(self.name, row_id))
        row = self._rows[row_id]
        if col_name not in self._columns:
            raise Exception('{} {}'.format(self.name, col_name))
        row[col_name] = new_value
        
    def get_value(self, row_id:int, col_name:str):
        assert isinstance(row_id, int)
        assert isinstance(col_name, str)
        if row_id not in self._rows:
            raise Exception('{} {}'.format(self.name, row_id))
        row = self._rows[row_id]
        if col_name not in self._columns:
            raise Exception('{} {}'.format(self.name, col_name))
        return row.get(col_name, None)
    
#-------------------------------------------------------------------------------

class Column:
    def __init__(self, table:Table, name:str, col_type:'ColumnType'):
        assert isinstance(table, Table)
        assert isinstance(name, str)
        assert isinstance(col_type, ColumnType)
        self._table = table
        self._name = name
        self._col_type = col_type

    @property
    def table(self):
        return self._table
     
    @property
    def name(self):
        return self._name
        
    @property
    def col_type(self):
        return self._col_type
        
#-------------------------------------------------------------------------------

class Row:
    def __init__(self, table:Table, id:int, data:map):
        assert isinstance(table, Table)
        assert isinstance(id, int)
        assert isinstance(data, map)
        self._table = table
        self._id = id
        self._data = data
        
    @property
    def table(self):
        return self._table
        
    @property
    def id(self):
        return self._id
        
    @property
    def data(self):
        return self._data

#-------------------------------------------------------------------------------

class ColumnType:
    pass
    
#-------------------------------------------------------------------------------

class Int(ColumnType):
    def __init__(self, min=None, max=None):
        self.min = min
        self.max = max
    
#-------------------------------------------------------------------------------

class Float(ColumnType):
    def __init__(self, min=None, max=None, eps=None):
        self.min = min
        self.max = max
        self.eps = eps
    
#-------------------------------------------------------------------------------

class _Str(ColumnType):
    def __init__(self, max_len=None, re=None):
        self.max_len = max_len
        self.re = re
    
#-------------------------------------------------------------------------------

class Name(_Str):
    def __init__(self):
        Str.__init__(self, max_len=30, re=r'[A-Z][a-z\-]*[a-z]')

#-------------------------------------------------------------------------------

class Text(_Str):
    def __init__(self):
        Str.__init__(self)
    
#-------------------------------------------------------------------------------

class Bool(ColumnType):
    pass    
    
#-------------------------------------------------------------------------------

class Date(ColumnType):
    pass

#-------------------------------------------------------------------------------

class Ref(ColumnType):
    def __init__(self, table, col, multiplicity):
        self.table = table
        self.col = col
        self.multiplicity = multiplicity
    
#-------------------------------------------------------------------------------

class BackRef(ColumnType):
    def __init__(self, table, col, ref):
        self.table = table
        self.col = col
        self.ref = ref
    
#-------------------------------------------------------------------------------

class List(ColumnType):
    def __init__(self, item_type):
        self.item_type = item_type
        
#-------------------------------------------------------------------------------

class Multiplicity(Enum):
    one2one = 1
    one2many = 2
    many2one = 3
    many2many = 4