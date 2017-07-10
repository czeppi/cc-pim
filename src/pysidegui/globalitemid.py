# Copyright (C) 2017  Christian Czepluch
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

from functools import total_ordering
from enum import Enum
import re


class GlobalItemTypes(Enum):

    person = 1
    company = 2
    address = 3
    task = 4


@total_ordering
class GlobalItemID:

    def __init__(self, item_type: GlobalItemTypes, serial: int):
        self._type = item_type
        self._serial = serial

    def __str__(self):
        type_name = self._type.name
        return type_name + str(self.serial)  # f'{self._serial:05}'

    def __eq__(self, other):
        return (self._type, self._serial) == (other._type, other._serial)

    def __lt__(self, other):
        return (self._type, self._serial) < (other._type, other._serial)

    @property
    def serial(self):
        return self._serial

    @property
    def type(self):
        return self._type

    @staticmethod
    def create_from_string(id_str):
        rex = re.compile(r"(?P<type>[a-zA-Z]+)(?P<serial>[0-9)])+")
        match = rex.match(id_str)
        if not match:
            raise ValueError(id_str)

        item_type = GlobalItemTypes[match.group('type')]
        serial = int(match.group('serial'))
        return GlobalItemID(item_type, serial)
