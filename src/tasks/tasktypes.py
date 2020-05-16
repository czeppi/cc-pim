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


class BaseType:

    def convert_to_db(self, value):
        return value


class Int(BaseType):
    sqlite3_typename = 'integer'


class String(BaseType):
    sqlite3_typename = 'text'  # !! Not 'string', otherwise '0123' will converted to '123' !!
        
    def convert_to_db(self, value):
        return value.replace('"', '""')
        

class ID(BaseType):
    sqlite3_typename = 'integer primary key'
    
    
class UserID(BaseType):
    sqlite3_typename = 'text'
    
    
class Ref(BaseType):
    sqlite3_typename = 'integer'  # ??

    def __init__(self, table_name, id_attribute_name):
        BaseType.__init__(self)
        self._table_name = table_name
        self._id_attribute_name = id_attribute_name


class Date(BaseType):
    sqlite3_typename = 'text'
    
    
class StringList(BaseType):
    sqlite3_typename = 'text'
    
    def convert_to_db(self, value):
        return value.replace('"', '""')  # besser ','.join(value)
    

class XmlString(String):
    pass
