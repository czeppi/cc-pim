#! /usr/bin/env python3

# Copyright (C) 2015  Christian Czepluch
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

from collections import OrderedDict, defaultdict
from enum import Enum
from modeling.basetypes import Name, Date, EMail, PhoneNumber, Url, Str, Text, Ref


class ContactTypes(Enum):

    person = 1
    company = 2
    address = 3


class Predicate:

    def __init__(self, serial, subject_class, name, value_type):
        self.serial = serial
        self.subject_class = subject_class
        self.name = name
        self.value_type = value_type

        
class Attribute:

    def __init__(self, name, value_type, predicate_serial):
        self.name = name
        self.value_type = value_type
        self.predicate_serial = predicate_serial
    
        
class Contact:

    def __init__(self, serial):
        self.serial = serial
        self._facts_map = defaultdict(list)  # attr-name -> list of facts
        
    @classmethod
    def iter_attributes(cls):
        yield from cls.attributes.values()
        
    @classmethod
    def get_attribute(cls, attr_name):
        return cls.attributes[attr_name]
    
    @classmethod
    def find_attribute(cls, attr_name):
        return cls.get(attr_name, None)

    @property
    def id(self):
        return self.type_id, self.serial

    def add_fact(self, attr_name, fact):
        self._facts_map[attr_name].append(fact)

    def get_facts(self, attr_name):
        return self._facts_map.get(attr_name, [])

    def get_fact(self, fact_serial):
        for facts in self._facts_map.values():
            for fact in facts:
                if fact.serial == fact_serial:
                    return fact

    def contains_keyword(self, keyword):
        lower_keyword = keyword.lower()
        return any(lower_keyword in str(fact.value).lower()
                   for fact_list in self._facts_map.values()
                   for fact in fact_list)

    def contains_all_keywords(self, keywords):
        return all(self.contains_keyword(x) for x in keywords)

    def get_html_text(self, contact_model):
        creator = ContactHtmlCreator(self, contact_model)
        return creator.create_html_text()

    def copy(self):
        new_contact = _create_contact(self.type_id, self.serial)
        for attr_name, fact_list in self._facts_map.items():
            for fact in fact_list:
                new_contact.add_fact(attr_name, fact.copy())
        return new_contact


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
                #val = self._get_fact_value(fact, attr)
                val = self._contact_model.get_fact_value(fact, attr)
                self._add('  <tr>')
                self._add('    <td>{}</td>'.format(attr.name))
                self._add('    <td>{}</td>'.format(val))
                self._add('  </tr>')
        self._add('</table)>')

    def _add_footer(self):
        self._add('</body>')
        self._add('</html>')

    def _add(self, line):
        self._lines.append(line)

        
class Person(Contact):

    type_id = ContactTypes.person.value
    type_name = 'person'
    attributes = OrderedDict()
    last_serial = 0

    @property
    def title(self):
        first_names = [x.value for x in self._facts_map['firstname']]
        last_names  = [x.value for x in self._facts_map['lastname']]
        names_parts = []
        if first_names:
            names_parts.append(first_names[-1])
        if last_names:
            names_parts.append(last_names[-1])
        if len(names_parts) == 0:
            return '???'
        return ' '.join(names_parts)


class Company(Contact):

    type_id = ContactTypes.company.value
    type_name = 'company'
    attributes = OrderedDict()
    last_serial = 0

    @property
    def title(self):
        names = [x.value for x in self._facts_map['name']]
        if names:
            return names[-1]
        else:
            return '???'


class Address(Contact):

    type_id = ContactTypes.address.value
    type_name = 'address'
    attributes = OrderedDict()
    last_serial = 0

    @property
    def title(self):
        streets = [x.value for x in self._facts_map['street']]
        if streets:
            return streets[-1]
        else:
            return '???'


def _create_contact(type_id, obj_serial):
    cls_map = {
        Person.type_id:  Person,
        Company.type_id: Company,
        Address.type_id: Address,
    }
    return cls_map[type_id](obj_serial)


def _iter_predicates_data():
    yield  1, Person,  'lastname',         Str
    yield  2, Person,  'firstname',        Str
    yield  3, Person,  'nickname',         Str
    yield  4, Person,  'day_of_birth',     Date
    yield  5, Person,  'day_of_death',     Date
    yield  6, Person,  'private_address',  Ref(Address, 'residents')
    yield  7, Person,  'private_email',    EMail
    yield  8, Person,  'private_mobile',   PhoneNumber
    yield  9, Person,  'private_url',      Url
    yield 10, Person,  'company',          Ref(Company, 'employees')
    yield 11, Person,  'business_address', Ref(Address, 'people')
    yield 12, Person,  'business_email',   EMail
    yield 13, Person,  'business_phone',   PhoneNumber
    yield 14, Person,  'keywords',         Str
    yield 15, Person,  'remark',           Text
    yield 16, Person,  'child',            Ref(Person, 'parents')
    yield 17, Person,  'partner',          Ref(Person, 'partner')
    yield 18, Company, 'name',             Str
    yield 19, Company, 'owner',            Str
    yield 20, Company, 'address',          Ref(Address, 'companies')
    yield 21, Company, 'homepage',         Url
    yield 22, Company, 'mobile',           PhoneNumber
    yield 23, Company, 'email',            EMail
    yield 24, Company, 'open_times',       Str
    yield 25, Company, 'keywords',         Str
    yield 26, Company, 'remark',           Text
    yield 27, Address, 'street',           Str
    yield 28, Address, 'city',             Str
    yield 29, Address, 'country',          Str
    yield 30, Address, 'phone',            PhoneNumber

    
class ContactModel:

    predicates = OrderedDict()
    for serial, subject_class, name, object_type in _iter_predicates_data():
        predicates[serial] = Predicate(serial, subject_class, name, object_type)
        subject_class.attributes[name] = Attribute(name, object_type, serial)
        
    @staticmethod
    def iter_object_classes():
        yield Person
        yield Company
        yield Address
        
    def __init__(self, date_changes, fact_changes):
        self._date_changes = date_changes
        self._fact_changes = fact_changes
        self._uncommited_date_changes = {}
        self._uncommited_fact_changes = {}
        self._revision_number = None
        self._init_data()
        self._init_last_serial_map()
        self._init_last_fact_serial()

    def _init_data(self):
        self._data = {}  # (type_id, serial) -> ContactObject
        for fact in self._fact_changes.values():
            predicate = self.predicates[fact.predicate_serial]
            type_id = predicate.subject_class.type_id
            obj_serial = fact.subject_serial
            obj_id = (type_id, obj_serial)
            obj = self._data.get(obj_id, None)
            if obj is None:
                obj = _create_contact(type_id, obj_serial)
                self._data[obj_id] = obj
            obj.add_fact(predicate.name, fact)

    def _init_last_serial_map(self):
        self._last_serial_map = {
            cls.type_id: max((serial for type_id, serial in self._data.keys() if type_id == cls.type_id), default=0)
            for cls in self.iter_object_classes()
        }

    def _init_last_fact_serial(self):
        self._last_fact_serial = max(fact.serial for fact in self._fact_changes.values())

    def iter_objects(self):
        yield from self._data.values()

    def update(self):
        pass

    def contains(self, type_id, obj_serial):
        return (type_id, obj_serial) in self._data
        
    def get(self, type_id, obj_serial):
        return self._data[(type_id, obj_serial)]
#        return self._data.get((type_id, obj_serial), '{}.{}?'.format(type_id, obj_serial))
        
    def find(self, search_parameters):
        pass

    def get_fact_value(self, fact, attr):
        if isinstance(attr.value_type, Ref):
            type_id = attr.value_type.target_class.type_id
            serial = int(fact.value)
            if serial == 0:
                return ''
            else:
                obj = self.get(type_id, serial)
                return obj.title
        else:
            return fact.value

    def add_changes(self, date_changes, fact_changes):
        self._date_changes.update(date_changes)
        self._fact_changes.update(fact_changes)
        self._uncommited_date_changes.update(date_changes)
        self._uncommited_fact_changes.update(fact_changes)
        self._init_data()

    def exists_uncommited_changes(self):
        return len(self._uncommited_date_changes) > 0 or len(self._uncommited_fact_changes) > 0

    def commit(self, comment, repo):
        repo.commit(comment,
                    date_changes=self._uncommited_date_changes,
                    fact_changes=self._uncommited_fact_changes)
        self._uncommited_date_changes.clear()
        self._uncommited_fact_changes.clear()

    def create_contact(self, type_id):
        assert type_id in self._last_serial_map
        new_serial = self._last_serial_map[type_id] + 1
        self._last_serial_map[type_id] = new_serial
        new_contact = _create_contact(type_id, new_serial)
        return new_contact

    def create_fact_serial(self):
        new_serial = self._last_fact_serial + 1
        self._last_fact_serial = new_serial
        return new_serial




