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
from contacts.contactmodel import Person, Attribute
from contacts.repository import Repository


class TestContactModel(unittest.TestCase):

    def setUp(self):
        self._repo = Repository()

    def test_add_person(self):
        n = self._repo.count_persons()
        new_id = self._repo.add_person(_create_person1_attributes())
        self.assertTrue(self._repo.count_persons() == n + 1)

    def test_find_persons(self):
        n = 0
        for person in self._repo.find_persons(text='Lutz'):
            self.assertTrue(isinstance(person, Person))
            n += 1
        self.assertTrue(n > 0)

    def test_get_person(self):
        person_serial = self._repo.add_person(_create_person1_attributes())
        person = self._repo.find_person(person_serial)
        self.assertTrue(isinstance(person, Person))


class TestPerson(unittest.TestCase):

    def test_iter_attribute(self):
        n = 0
        for attr in Person.iter_attributes():
            self.assertTrue( isinstance(attr, Attribute) )
            n += 1
        self.assertTrue(n > 0)

    # def test_get_attribute(self):
    #     attr = Person.get_attribute('name')
    #     self.assertTrue( isinstance(attr, Attribute) )
    #
    # def test_iter_facts(self):
    #     person = Person( _create_person1_attributes() )
    #     for name_fact in person.iter_facts('name'):
    #         self.assertTrue( isinstance(name_fact, str) )

    # def test_add_facts(self):
    #     person = Person( _create_person1_attributes() )
    #     address1 = Address( _create_address1_attributes() )
    #     fact_serial = person.add_fact('address', address1, t_begin=None, t_end=None)
    #     n1 = person.count_facts()
    #
    #     address2 = Address( _create_address2_attributes() )
    #     person.change_fact(fact_serial, 'address', address2, t_begin=None, t_end=None)
    #     n2 = person.count_facts()
    #     self.assertTrue( n1 + 1 == n2 )
    #
    # def test_change_fact(self):
    #     person = Person( _create_person1_attributes() )
    #     address1 = Address( _create_address1_attributes() )
    #     fact_serial = person.add_fact('address', address1, t_begin=None, t_end=None)
    #     n1 = person.count_facts()
    #
    #     address2 = Address( _create_address2_attributes() )
    #     person.change_fact(fact_serial, 'address', address2, t_begin=None, t_end=None)
    #     n2 = person.count_facts()
    #     self.assertTrue( n1 == n2 )


def _create_person1_attributes():
    return {
        'first_name': 'Max',
        'last_name': 'Mustermann',
        'e-mail': 'max@mustermann.de',
        'birth_date': '01.01.1970',
    }


def _create_address1_attributes():
    return {
        'street': 'Musterstraße 1',
        'place': '12345 Berlin',
    }


def _create_address2_attributes():
    return {
        'street': 'Musterstraße 2',
        'place': '12345 Berlin',
    }

        
if __name__ == '__main__':
    unittest.main()
