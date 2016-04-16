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

from collections import OrderedDict
from enum import Enum
from basetypes import Name, Date, EMail, PhoneNumber, Url, Str, Text, Ref


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

    def __init__(self, values):
        self.values = values  # name -> list of values
        
    @classmethod
    def 
    
    @classmethod
    def iter_attributes(cls):
        yield from cls.attributes.values()
        
    @classmethod
    def get_attribute(cls, attr_name):
        return cls.attributes[attr_name]
    
    @classmethod
    def find_attribute(cls, attr_name):
        return cls.get(attr_name, None)

    def get_attr_value(self, attr_name):
        return self.values[attr_name]
        
        
class Person(ContactObject):

    type_serial = ContactTypes.person
    type_name = 'person'
    attributes = OrderedDict()
    last_serial = 0

    @property
    def title(self):
        return self.get_value('first_name') + self.get_value('last_name')
        

class Company(ContactObject):

    type_serial = ContactTypes.person
    type_name = 'person'
    attributes = OrderedDict()
    last_serial = 0

    
class Address(ContactObject):

    type_serial = ContactTypes.person
    type_name = 'person'
    attributes = OrderedDict()
    last_serial = 0


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
    yield 22, Company, 'phone',            PhoneNumber
    yield 23, Company, 'mobile',           PhoneNumber
    yield 24, Company, 'email',            EMail
    yield 25, Company, 'open_times',       Str
    yield 26, Company, 'keywords',         Str
    yield 27, Company, 'remark',           Text
    yield 28, Address, 'street',           Str
    yield 29, Address, 'city',             Str
    yield 30, Address, 'country',          Str
    yield 31, Address, 'phone',            PhoneNumber

    
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
        
    def __init__(self):
        self._fact_dates = {}
        self._persons = {}
        self._companies = {}
        self._addresses = {}
        
    def update(self):
        pass
        
    def commit(self, comment, user=None):
        pass
        
    def revert_changes(self):
        pass
        
    def get_person(self, person_serial):
        return self._persons[person_serial]
        
    def get_company(self, company_serial):
        return self._companies[company_serial]
        
    def get_address(self, address_serial):
        return self._addresss[address_serial]
        
    def find_persons(self, search_parameters):
        yield from self._find_objects(ContactType.person, search_parameters)
        
    def find_companies(self, search_parameters):
        yield from self._find_objects(ContactType.company, search_parameters)
        
    def find_addresses(self, search_parameters):
        yield from self._find_objects(ContactType.address, search_parameters)
        
    def _find_objects(self, object_type, search_parameters):
        pass
        
    def add_person(self, person):
        new_serial = len(self._persons) + 1
        assert new_serial not in self._persons
        self._persons[new_serial] = person

    def add_company(self, company):
        new_serial = len(self._companys) + 1
        assert new_serial not in self._companies
        self._companies[new_serial] = company

    def add_address(self, address):
        new_serial = len(self._addresses) + 1
        assert new_serial not in self._addresses
        self._addresses[new_serial] = address
        
    def change_person(self, serial, person):
        assert serial in self._persons
        self._persons[serial] = person

    def change_company(self, serial, company):
        assert serial in self._companies
        self._companies[serial] = company
        
    def change_address(self, serial, address):
        assert serial in self._addresses
        self._addresses[serial] = address


        
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
                
