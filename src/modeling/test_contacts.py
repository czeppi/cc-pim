#! /usr/bin/env python3

# Copyright (C) 2016  Christian Czepluch
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

import unittest
from contacts import Person, Contacts, Attribute


class TestPerson(unittest.TestCase):

    def test_get_attribute(self):
        self.assertTrue( Person.get_attribute('lastname').name == 'lastname' )


class TestContacts(unittest.TestCase):

    def test_xxx(self):
        self.assertTrue(True)

        
if __name__ == '__main__':
    unittest.main()
                