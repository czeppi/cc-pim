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

from collections import defaultdict
from PySide.QtGui import QTextEdit


class HtmlView(QTextEdit):

    def __init__(self, parent):
        super().__init__(parent)
        self.click_link_observers = []

    def mousePressEvent(self, event):
        pos = event.pos()
        href_str = self.anchorAt(pos)
        super().mousePressEvent(event)

        #print('mouse-presse-event: pos: {}, anchor: {}'.format(pos, href_str))
        if href_str:
            for observer in self.click_link_observers:
                observer(href_str)


class ContactHtmlCreator:

    def __init__(self, contact, contact_model):
        self._contact = contact
        self._contact_model = contact_model

    def create_html_text(self):
        self._lines = []
        self._add_header()
        self._add_title()
        self._add_table()
        self._add_footer()
        return '\n'.join(self._lines)

    def _add_header(self):
        self._add('<html>')
        self._add('<head>')
        #self._add('  <style> table, td, th { border: 1px solid black; } </style>')
        self._add('</head>')
        self._add('<body>')

    def _add_title(self):
        self._add('<h1 align="center">{}</h1>'.format(self._contact.title))

    def _add_table(self):
        self._add('<table align="center" cellspacing="10" cellpadding="1">')
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

    def _create_back_facts(self):
        back_facts = defaultdict(list)  # attr_name -> [fact]
        for fact in self._contact_model.iter_back_facts(self._contact):
            predicate = self._contact_model.predicates[fact.predicate_serial]
            ref = predicate.value_type
            back_facts[ref.target_attributename].append(fact)
        return back_facts

    def _add_row(self, attr_name, val, fact, href_obj):
        self._add('  <tr>')
        self._add('    <td>{}:</td>'.format(attr_name))
        if href_obj:
            self._add('    <td><a href="{}">{}</a></td>'.format(str(href_obj.id), val))
        else:
            self._add('    <td><b>{}</b></td>'.format(val))
        self._add('  </tr>')

    def _add_footer(self):
        self._add('</body>')
        self._add('</html>')

    def _add(self, line):
        self._lines.append(line)