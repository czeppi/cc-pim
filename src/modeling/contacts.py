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
from .basetypes import Name, Date, EMail, PhoneNumber, Url, Str, Text, Ref


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

    def __init__(self, name, value_type):
        self.name = name
        self.value_type = value_type
    
        
class ContactObject:

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

    def contains_keyword(self, keyword):
        lower_keyword = keyword.lower()
        return any(lower_keyword in str(fact.value).lower()
                   for fact_list in self._facts_map.values()
                   for fact in fact_list)

    def contains_all_keywords(self, keywords):
        return all(self.contains_keyword(x) for x in keywords)
        
        
class Person(ContactObject):

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


class Company(ContactObject):

    type_id = ContactTypes.company.value
    type_name = 'person'
    attributes = OrderedDict()
    last_serial = 0

    @property
    def title(self):
        names = [x.value for x in self._facts_map['name']]
        if names:
            return names[-1]
        else:
            return '???'


class Address(ContactObject):

    type_id = ContactTypes.address.value
    type_name = 'person'
    attributes = OrderedDict()
    last_serial = 0

    @property
    def title(self):
        streets = [x.value for x in self._facts_map['street']]
        if streets:
            return streets[-1]
        else:
            return '???'


def _create_contact_object(type_id, obj_serial):
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

    
class Contacts:

    predicates = OrderedDict()
    for serial, subject_class, name, object_type in _iter_predicates_data():
        predicates[serial] = Predicate(serial, subject_class, name, object_type)
        subject_class.attributes[name] = Attribute(name, object_type)
        
    @staticmethod
    def iter_object_classes(self):
        yield Person
        yield Company
        yield Address
        
    def __init__(self, date_changes, fact_changes):
        self._date_changes = date_changes
        self._fact_changes = fact_changes
        self._revision_number = None
        self._init_data()

    def _init_data(self):
        self._data = {}  # (type_id, serial) -> ContactObject
        for fact in self._fact_changes.values():
            predicate = self.predicates[fact.predicate_serial]
            type_id = predicate.subject_class.type_id
            obj_serial = fact.subject_serial
            obj_id = (type_id, obj_serial)
            obj = self._data.get(obj_id, None)
            if obj is None:
                obj = _create_contact_object(type_id, obj_serial)
                self._data[obj_id] = obj
            obj.add_fact(predicate.name, fact)

    def iter_objects(self):
        yield from self._data.values()

    def update(self):
        pass
        
    def commit(self, comment, user=None):
        pass
        
    def revert_changes(self):
        pass
        
    def get(self, type_id, obj_serial):
        return self._data[type_id][obj_serial]
        
    def find(self, search_parameters):
        pass
        
    # def add(self, new_obj):
    #     obj_map = self._data[new_obj.type_id]
    #     new_serial = len(obj_map) + 1
    #     assert new_serial not in obj_map
    #     obj_map[new_serial] = new_obj
    #
    # def change(self, serial, obj):
    #     obj_map = self._data[new_obj.type_id]
    #     assert serial in obj_map
    #     obj_map[serial] = person



        
  # class ContactMetaModel:

    # def __init__(self):
        # self._init_relation_types()
        # self._init_object_types()
    
    # def _init_relation_types(self):
        # self._relation_types = []
        # for relation_type_serial, subject_class, subject_attr_name, object_class:  # subject_multiplicity, object_multiplicity
            # new_realation_type = RelationType(relation_type_serial, subject_class, subject_attr_name, object_class, object_attr_name)
            # if isinstance(object_class, Ref):
                # ref = object_class
                # new_relation_type = RelationType(relation_type_serial, subject_class, subject_attr_name, ref.obj_class, ref.attr_name=
            # else:
                # new_relation_type = RelationType(relation_type_serial, subject_class, subject_attr_name, object_class)
            # self._relation_types.append(new_realation_type)
            
    # def _init_object_types(self):
        # self._object_types  = OrderedDict()
        # self._init_subject_types()
        # self._init_object_attributes()
        
    # def _init_subject_types(self):
        # for rel_type in self._relation_types:
            # object_type_name = rel_type.subject_type_name
            # if object_type_name not in self._object_types:
                # self._object_types.append(
                    # ObjectType(object_type_name))
        
    # def _init_object_attributes(self)
        # for rel_type in self._relation_types:
            # object_type = self._object_types[rel_type.subject_type_name]
            # object_type.add_attribute(rel_type.subject_attr_name, rel_type.value_type)
            
            # if isinstance(rel_type.value_type, Link):
                # link = rel_type.value_type
                # if link.type_name not in self._object_types:
                    # self._object_types.append(
                        # ObjectType(link.type_name))
                # object_type = self._object_types[link.type_name]
                # object_type.add_backlink_attribute(link.type_name, link.attr_name)
                
