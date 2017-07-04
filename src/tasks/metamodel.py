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

from configparser import RawConfigParser
from collections import OrderedDict

from tasks.types import *


class MetaModel:

    def __init__(self, logging_enabled=False):
        self._logging_enabled = logging_enabled
        
    @property
    def structures(self):
        return self._structures.values()
        
    def read(self, pathname):
        self._structures = OrderedDict()
        config = RawConfigParser()
        config.optionxform = lambda x: x  # ansonsten werden Buchstaben der Attribute in Kleinbuchstaben umgewandelt
        config.read(pathname)
        for section_name in config.sections():
            new_struct = self._process_section(config[section_name])
            self._structures[new_struct.name] = new_struct
            
    def _process_section(self, section):
        if self._logging_enabled:
            print(section.name)
        new_struct = Structure(section.name)
        
        for key, value in section.items():
            if self._logging_enabled:
                print('{}: {}'.format(key, value))
            new_attr = Attribute(key, eval(value))
            new_struct.add_attribute(new_attr)
        return new_struct


class Structure:

    def __init__(self, name):
        self._name = name
        self._attributes = OrderedDict()
        
    @property
    def name(self):
        return self._name
        
    @property
    def attributes(self):
        return self._attributes.values()
        
    def attribute(self, name):
        return self._attributes[name]
        
    def add_attribute(self, attribute):
        self._attributes[attribute.name] = attribute


class Attribute:

    def __init__(self, name, type):
        self._name = name
        self._type = type
        
    @property
    def name(self):
        return self._name
    
    @property
    def type(self):
        return self._type
    

if __name__ == '__main__':

    context = Context()
    meta_model = MetaModel()
    meta_model.read(context.metamodel_pathname)
