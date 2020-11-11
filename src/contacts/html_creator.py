# Copyright (C) 2020  Christian Czepluch
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

from collections import defaultdict
from typing import List, Dict, Any

from contacts.basetypes import Fact
from contacts.contactmodel import Contact, ContactModel


class ContactHtmlCreator:

    def __init__(self, contact: Contact, contact_model: ContactModel):
        self._contact = contact
        self._contact_model = contact_model
        self._lines: List[str] = []

    def create_html_text(self) -> str:
        self._lines.clear()
        self._add_header()
        self._add_title()
        self._add_table()
        self._add_footer()
        return '\n'.join(self._lines)

    def _add_header(self) -> None:
        self._add('<html>')
        self._add('<head>')
        self._add('</head>')
        self._add('<body>')

    def _add_title(self) -> None:
        self._add(f'<h1>{self._contact.title}</h1>')

    def _add_table(self) -> None:
        self._add('<table>')
        for attr in self._contact.iter_attributes():
            for fact in self._contact.get_facts(attr.name):
                if fact.is_valid:
                    val = self._contact_model.get_fact_value(fact)
                    href_obj = self._contact_model.get_fact_object(fact)
                    self._add_row(attr.name, val, fact, href_obj)
        back_facts = self._create_back_facts()
        for attr in self._contact.iter_back_attributes():
            for fact in back_facts.get(attr.name, []):
                if fact.is_valid:
                    subject = self._contact_model.get_fact_subject(fact)
                    val = subject.title
                    self._add_row(attr.name, val, fact, subject)
        self._add('</table)>')

    def _create_back_facts(self) -> Dict[str, List[Fact]]:
        back_facts = defaultdict(list)  # attr_name -> [fact]
        for fact in self._contact_model.iter_back_facts(self._contact):
            predicate = self._contact_model.predicates[fact.predicate_serial]
            ref = predicate.value_type
            back_facts[ref.target_attributename].append(fact)
        return back_facts

    def _add_row(self, attr_name: str, val: Any, fact: Fact, href_obj):
        self._add('  <tr>')
        self._add(f'    <td>{attr_name}:</td>')
        if href_obj:
            self._add(f'    <td><a href="{href_obj.id}">{val}</a></td>')
        else:
            self._add(f'    <td><b>{val}</b></td>')
        self._add('  </tr>')

    def _add_footer(self):
        self._add('</body>')
        self._add('</html>')

    def _add(self, line):
        self._lines.append(line)