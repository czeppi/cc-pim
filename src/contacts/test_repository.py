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
from contacts.repository import Repository, Revision
from contacts.basetypes import Fact


class TestRepo(unittest.TestCase):

    def setUp(self):
        self._repo = Repository()
        
    def test_empty_repo(self):
        n = self._repo.count_revisions()
        self.assertTrue(n == 0)
        
    def test_add_empty_revision(self):
        new_rev = self._repo.commit(comment='empty change', date_changes={}, fact_changes={})
        self.assertIsInstance(new_rev, Revision)
        self.assertEqual(new_rev.serial, 1)
        self._repo.reload()
        self.assertEqual(self._repo.count_revisions(), 1)

    def test_add_revision_with_one_new_fact(self):
        fact_changes = {
            self._repo.get_new_fact_serial(): Fact(serial=1, predicate_serial=1, subject_serial=1, value='Mustermann')
        }
        new_rev = self._repo.commit(comment='empty change',
                                    date_changes={},
                                    fact_changes=fact_changes)
        self.assertIsInstance(new_rev, Revision)
        self.assertEqual(new_rev.serial, 1)
        self.assertEqual(len(new_rev.fact_changes), 1)

        self._repo.reload()
        self.assertEqual(self._repo.count_revisions(), 1)
        rev = self._repo.get_revision(1)
        self.assertEqual(len(rev.fact_changes), 1)
        fact1 = rev.fact_changes[1]
        self.assertEqual(fact1.subject_serial, 1)
        self.assertEqual(fact1.value, 'Mustermann')


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
