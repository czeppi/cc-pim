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

import sys
from collections import OrderedDict
from configparser import RawConfigParser
from pathlib import Path
from typing import Dict, ValuesView, Any

from context import Context, Config
from tasks.tasktypes import Date, ID, Int, Ref, String, XmlString  # necessary for MetaModel._process_section()


class MetaModel:

    def __init__(self, logging_enabled: bool = False):
        self._logging_enabled = logging_enabled
        self._structures: Dict[str, Structure] = OrderedDict()

    @property
    def structures(self):
        return self._structures.values()
        
    def read(self, config_path: Path) -> None:
        self._structures.clear()
        config = RawConfigParser()
        config.optionxform = lambda x: x  # necessary, for prevent letters to convert in small letters
        config.read(str(config_path))
        for section_name in config.sections():
            new_struct = self._process_section(config[section_name])
            self._structures[new_struct.name] = new_struct
            
    def _process_section(self, section):
        if self._logging_enabled:
            print(section.name)
        new_struct = Structure(section.name)
        
        for key, value in section.items():
            if self._logging_enabled:
                print(f'{key}: {value}')
            new_attr = Attribute(key, eval(value))
            new_struct.add_attribute(new_attr)
        return new_struct


class Structure:

    def __init__(self, name: str):
        self._name = name
        self._attributes: Dict[str, Attribute] = OrderedDict()
        
    @property
    def name(self) -> str:
        return self._name
        
    @property
    def attributes(self) -> ValuesView[Attribute]:
        return self._attributes.values()
        
    def attribute(self, name: str) -> Attribute:
        return self._attributes[name]
        
    def add_attribute(self, attribute: Attribute) -> None:
        self._attributes[attribute.name] = attribute


class Attribute:

    def __init__(self, name: str, type_: Any):
        self._name = name
        self._type = type_
        
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def type(self) -> Any:
        return self._type
    

if __name__ == '__main__':
    start_dir = Path(sys.argv[0]).resolve().parent
    root_dir = start_dir.parent
    context = Context(root_dir, Config())
    meta_model = MetaModel()
    meta_model.read(context.tasks_metamodel_path)
