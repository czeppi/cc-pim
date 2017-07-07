# Copyright (C) 2015  Christian Czepluch
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

from collections import OrderedDict, defaultdict
from enum import Enum
from functools import total_ordering

from contacts.basetypes import Date, EMail, PhoneNumber, Url, Str, Text, Ref


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
        self._back_facts_map = defaultdict(list)
        
    @classmethod
    def iter_attributes(cls):
        yield from cls.attributes.values()
        
    @classmethod
    def iter_back_attributes(cls):
        yield from cls.back_attributes.values()

    @classmethod
    def get_attribute(cls, attr_name):
        if attr_name in cls.attributes:
            return cls.attributes[attr_name]
        else:
            return cls.back_attributes[attr_name]
    
    @classmethod
    def find_attribute(cls, attr_name):
        attr = cls.attributes.get(attr_name, None)
        if attr is None:
            attr = cls.back_attributes.get(attr_name, None)
        return attr

    @property
    def id(self):
        return ContactID(self.type_id, self.serial)

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

    def copy(self):
        new_contact = _create_contact(self.type_id, self.serial)
        for attr_name, fact_list in self._facts_map.items():
            for fact in fact_list:
                new_contact.add_fact(attr_name, fact.copy())
        return new_contact


class Person(Contact):

    type_id = ContactTypes.person.value
    type_name = 'person'
    attributes = OrderedDict()
    back_attributes = OrderedDict()
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
            return '#' + str(self.serial)
        return ' '.join(names_parts)


class Company(Contact):

    type_id = ContactTypes.company.value
    type_name = 'company'
    attributes = OrderedDict()
    back_attributes = OrderedDict()
    last_serial = 0

    @property
    def title(self):
        names = [x.value for x in self._facts_map['name']]
        if names:
            return names[-1]
        else:
            return '#' + str(self.serial)


class Address(Contact):

    type_id = ContactTypes.address.value
    type_name = 'address'
    attributes = OrderedDict()
    back_attributes = OrderedDict()
    last_serial = 0

    @property
    def title(self):
        parts = []
        parts += [x.value for x in self._facts_map['street']]
        parts += [x.value for x in self._facts_map['city']]
        parts += [x.value for x in self._facts_map['phone']]
        return ', '.join(parts)


def _create_contact(type_id, obj_serial):
    cls_map = {
        Person.type_id:  Person,
        Company.type_id: Company,
        Address.type_id: Address,
    }
    return cls_map[type_id](obj_serial)


@total_ordering
class ContactID:

    type_id_map = {
        Person.type_id:  Person,
        Company.type_id: Company,
        Address.type_id: Address,
    }

    type_name_map = {
        Person.type_name:  Person,
        Company.type_name: Company,
        Address.type_name: Address,
    }

    @staticmethod
    def type_id2name(type_id):
        return ContactID.type_id_map[type_id].type_name

    @staticmethod
    def type_name2id(type_name):
        return ContactID.type_name_map[type_name].type_id

    @staticmethod
    def create_from_string(id_str):
        for type_name, cls in ContactID.type_name_map.items():
            n = len(type_name)
            if id_str[:n] == type_name:
                return ContactID(cls.type_id, int(id_str[n:]))
        raise ValueError(id_str)

    def __init__(self, type_id, serial):
        self.type_id = type_id
        self.serial = serial

    def __str__(self):
        type_name = ContactID.type_id2name(self.type_id)
        return type_name + str(self.serial)

    def __eq__(self, other):
        return (self.type_id, self.serial) == (other.type_id, other.serial)

    def __lt__(self, other):
        return (self.type_id, self.serial) < (other.type_id, other.serial)

    @property
    def type_serial(self):
        return (self.type_id, self.serial)


def _iter_predicates_data():
    yield  1, Person,  'lastname',         Str
    yield  2, Person,  'firstname',        Str
    yield  3, Person,  'nickname',         Str
    yield  4, Person,  'day_of_birth',     Date
    yield  5, Person,  'day_of_death',     Date
    yield  6, Person,  'private_address',  Ref(Address, 'resident')
    yield  7, Person,  'private_email',    EMail
    yield  8, Person,  'private_mobile',   PhoneNumber
    yield  9, Person,  'private_url',      Url
    yield 10, Person,  'company',          Ref(Company, 'employee')
    yield 11, Person,  'business_address', Ref(Address, 'people')
    yield 12, Person,  'business_email',   EMail
    yield 13, Person,  'business_phone',   PhoneNumber
    yield 14, Person,  'keywords',         Str
    yield 15, Person,  'remark',           Text
    yield 16, Person,  'child',            Ref(Person, 'parent')
    yield 17, Person,  'partner',          Ref(Person, 'partner')
    yield 18, Company, 'name',             Str
    yield 19, Company, 'owner',            Str
    yield 20, Company, 'address',          Ref(Address, 'company')
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
    for serial, subject_class, name, object_type in _iter_predicates_data():
        if isinstance(object_type, Ref):
            ref = object_type
            ref.target_class.back_attributes[ref.target_attributename] = \
                Attribute(ref.target_attributename, subject_class, serial)

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
        self._init_last_date_serial()

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
        self._last_fact_serial = max((fact.serial for fact in self._fact_changes.values()), default=0)

    def _init_last_date_serial(self):
        self._last_date_serial = max((date.serial for date in self._date_changes.values()), default=0)

    def iter_objects(self):
        yield from self._data.values()

    def iter_back_facts(self, obj):
        for fact in self._fact_changes.values():
            predicate = self.predicates[fact.predicate_serial]
            if isinstance(predicate.value_type, Ref):
                ref = predicate.value_type
                if ref.target_class.type_id == obj.type_id \
                and int(fact.value) == obj.serial:
                    yield fact

    def update(self):
        pass

    def iter_dates(self):
        yield from self._date_changes.values()

    def get_date(self, date_serial):
        return self._date_changes[date_serial]

    def contains(self, contact_id):
        return contact_id.type_serial in self._data
        
    def get(self, contact_id):
        return self._data[contact_id.type_serial]
#        return self._data.get((type_id, obj_serial), '{}.{}?'.format(type_id, obj_serial))
        
    def find(self, search_parameters):
        pass

    def get_fact_value(self, fact):
        predicate = self.predicates[fact.predicate_serial]
        if isinstance(predicate.value_type, Ref):
            ref = predicate.value_type
            type_id = ref.target_class.type_id
            serial = int(fact.value)
            if serial == 0:
                return ''
            else:
                obj = self.get(ContactID(type_id, serial))
                return obj.title
        else:
            return fact.value

    def get_fact_subject(self, fact):
        predicate = self.predicates[fact.predicate_serial]
        type_id = predicate.subject_class.type_id
        subject_id = (type_id, fact.subject_serial)
        return self._data.get(subject_id, None)

    def get_fact_object(self, fact):
        predicate = self.predicates[fact.predicate_serial]
        if isinstance(predicate.value_type, Ref):
            ref = predicate.value_type
            type_id = ref.target_class.type_id
            serial = int(fact.value)
            if serial != 0:
                return self.get(ContactID(type_id, serial))

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

    def create_date_serial(self):
        new_serial = self._last_date_serial + 1
        self._last_date_serial = new_serial
        return new_serial
