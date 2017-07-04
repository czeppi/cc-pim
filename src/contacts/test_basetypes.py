# Copyright (C) 2016  Christian Czepluch
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

import unittest
import os
import sys
sys.path += [
    os.path.join(os.path.dirname(__file__), '..'),
]
from contacts.basetypes import VagueDate


class TestVagueDate(unittest.TestCase):

    def test_valid_dates(self):
        for x in self._iter_valid_vague_dates():
            vague_date = VagueDate(x)
            self.assertTrue(str(vague_date) == x)

    @staticmethod
    def _iter_valid_vague_dates():
        yield '30.04.2016'
        yield '~30.04.2016'
        yield '30.04.~2016'
        yield '~30.04.~2016'

    def test_invalid_dates(self):
        for x in self._iter_invalid_vague_dates():
            self.assertRaises(Exception, VagueDate.__init__, x)
        
    @staticmethod
    def _iter_invalid_vague_dates():
        yield '01.04.2016'
        yield '30.4.2016'
        yield '30.04.16'
        yield '2016-04-16'
        yield '16-04-16'
        yield '160430'

        
if __name__ == '__main__':
    unittest.main()
        