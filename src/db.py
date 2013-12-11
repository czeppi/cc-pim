#! /usr/bin/env python
#-*- coding: utf-8 -*-

##########################################
## CC-PIM                               ##
## Copyright 2013 by Christian Czepluch ##
##########################################


#-------------------------------------------------------------------------------

class DB:
    def __init__(self):
        self.tables = {}
        self._next_table_id = 1
        
    def create_table(self, name):
        new_table_id = self._next_table_id
        new_table = Table(new_table_id, name)
        self.tables[new_table_id] = new_table
        self._next_table_id += 1
        return new_table_id

#-------------------------------------------------------------------------------
    
class Table:
    def __init__(self, id, name):
        self.id = id
        self.name = name
        self.columns = {}
        self._next_col_id = 1
        self._next_row_id = 1
        
    def add_col(self, col_name, col_type):
        new_id = self._next_col_id
        new_col = Column(new_id, col_name, col_type)
        self.columns[new_id] = new_col
        self._next_col_id += 1
        return new_col
        
    def add_row(self, **values):
        new_id = self._next_row_id
        new_row = Row(new_id, **values)
        self.rows[new_id] = new_row
        self._next_row_id += 1
        return new_row
    
#-------------------------------------------------------------------------------

class Column:
    def __init__(self, id, name, col_type):
        self.id = id
        self.name = name
        self.col_type = col_type
        
#-------------------------------------------------------------------------------

class Row:
    def __init__(self, id, **values):
        self.id = id
        self.values = values

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