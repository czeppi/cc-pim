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

from core import Name, Date, EMail, PhoneNumber, Url, Str


class Fact:

    def __init__(self, serial, predicate_serial, object_serial, value, time_begin=None, time_end=None):
        self.serial = serial
        self.predicate_serial = predicate_serial
        self.object_serial = object_serial
        self.value = value
        self.time_begin = time_begin
        self.time_end = time_end


class ObjectTypes(Enum):
    person = 1
    company = 2
    address = 3


# class ObjectType:

    # def __init__(self, serial):
        # self.serial = serial
        # self.attributes = []

    
# person_type  = ObjectType(ObjectTypes.person)
# company_type = ObjectType(ObjectTypes.company)
# address_type = ObjectType(ObjectTypes.address)


class Object:

    def __init__(self, type, serial, values)
        self.type = type
        self.serial = serial
        self.values = values
        
    def iter_attributes(self):
        yield from self.attributes
        
        
class Person(Object):

    serial = ObjectTypes.person
    attributes = [...]

    def __init__(self, values):
        super(self).__init__(person_type, values)
        
    @property
    def title(self):
        return self.get_value('first_name') + self.get_value('last_name')
        
        

def iter_predicates_data(): 
    yield  1, Person,  'lastname',         Str
    yield  2, Person,  'firstname',        Str
    yield  3, Person,  'nickname',         Str
    ...   
        
        
        
        
        
        
        
        
        
        
        
#------------------------------------------------------------------------------

class RelationType:

    last_serial = 0
    
    def __init__(self, subject_type, predicate, object_type, multiplicity):´
        self.serial = self.last_serial + 1
        self.subject_type = subject_type
        self.predicate = predicate
        self.object_type = object_type
        self.multiplicity = multiplicity
        self.last_serial = self.serial
        
#------------------------------------------------------------------------------

class RelationFactory:

    def __init__(self):
        self._type_id2last_serial = defaultdict(0)
        
    def create_relation(relation_type_id):
        new_serial = self._type_id2last_serial[relation_type_id] + 1
        self._type_id2last_serial[relation_type_id] = new_serial
        return Relation(relation_type_id, new_serial)
    

class Relation:

    def __init__(self, relation_type_id, serial, subject, predicate, object):
        self._type_id = relation_type_id
        self._serial = serial


#------------------------------------------------------------------------------

class ContactType(Enum):
    person = 1
    company = 2
    address = 3
    

class ContactMetaModel:

    def __init__(self):
        self._init_relation_types()
        self._init_object_types()
    
    def _init_relation_types(self):
        self._relation_types = []
        for relation_type_serial, subject_class, subject_attr_name, object_class:  # subject_multiplicity, object_multiplicity
            new_realation_type = RelationType(relation_type_serial, subject_class, subject_attr_name, object_class, object_attr_name)
            if isinstance(object_class, Ref):
                ref = object_class
                new_relation_type = RelationType(relation_type_serial, subject_class, subject_attr_name, ref.obj_class, ref.attr_name=
            else:
                new_relation_type = RelationType(relation_type_serial, subject_class, subject_attr_name, object_class)
            self._relation_types.append(new_realation_type)
            
    def _init_object_types(self):
        self._object_types  = OrderedDict()
        self._init_subject_types()
        self._init_object_attributes()
        
    def _init_subject_types(self):
        for rel_type in self._relation_types:
            object_type_name = rel_type.subject_type_name
            if object_type_name not in self._object_types:
                self._object_types.append(
                    ObjectType(object_type_name))
        
    def _init_object_attributes(self)
        for rel_type in self._relation_types:
            object_type = self._object_types[rel_type.subject_type_name]
            object_type.add_attribute(rel_type.subject_attr_name, rel_type.value_type)
            
            if isinstance(rel_type.value_type, Link):
                link = rel_type.value_type
                if link.type_name not in self._object_types:
                    self._object_types.append(
                        ObjectType(link.type_name))
                object_type = self._object_types[link.type_name]
                object_type.add_backlink_attribute(link.type_name, link.attr_name)
                
                
                
            
        
        
            
    # def _iter_relation_types(self):
        # yield 'person.lastname',         Str
        # yield 'person.firstname',        Str
        # yield 'person.nickname',         Str
        # yield 'person.day_of_birth',     Date
        # yield 'person.day_of_death',     Date
        # yield 'person.private_address',  'address.residents'
        # yield 'person.private_email',    EMail
        # yield 'person.private_mobile',   PhoneNumber
        # yield 'person.private_url',      Url
        # yield 'person.company',          'company.employees'
        # yield 'person.business_address', 'address.people'
        # yield 'person.business_email',   EMail
        # yield 'person.business_phone',   PhoneNumber
        # yield 'person.keywords',         Str
        # yield 'person.remark',           Text
        # yield 'person.children',         'person.parents'
        # yield 'person.partner',          'person.partner'
        # yield 'company.name',            Str
        # yield 'company.owner',           Str
        # yield 'company.address',         'address.companies'
        # yield 'company.homepage',        Url
        # yield 'company.phone',           PhoneNumber
        # yield 'company.mobile',          PhoneNumber
        # yield 'company.email',           EMail
        # yield 'company.open_times',      Str
        # yield 'company.keywords',        Str
        # yield 'company.remark',          Text
        # yield 'address.street',          Str
        # yield 'address.city',            Str
        # yield 'address.country',         Str
        # yield 'address.phone',           PhoneNumber
        
    def _iter_relation_types(self):
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
        yield 16, Person,  'children',         Ref(Person, 'parents')
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
        
    # def iter_object_types(self):
        # yield PersonType
        # yield CompanyType
        # yield AddressType
        
    def iter_object_types(self):
        
    
class ContactModel:

    _relation_types = [
        RelationType(Person, 'private_adress',  Address, '*-*'),
        RelationType(Person, 'business_adress', Address, '*-*'),
        RelationType(Person, 'parent_child',    Person,  '2-*'),
        RelationType(Person, 'partner',         Person,  '1-1'),
        RelationType(Person, 'private_mobile',  Phone,   '1-*'),
    ]

    def __init__(self):
        self._persons = {}
        self._companies = {}
        self._addresses = {}
        
    def update(self):
        pass
        
    def get_person(self, person_id):
        return self._persons[person_id]
        
    def get_company(self, company_id):
        return self._companys[company_id]
        
    def get_address(self, address_id):
        return self._addresss[address_id]
        
    def find_persons(self, search_parameters):
        yield from self._find_objects(ContactType.person, search_parameters)
        
    def find_companies(self, search_parameters):
        yield from self._find_objects(ContactType.company, search_parameters)
        
    def find_addresses(self, search_parameters):
        yield from self._find_objects(ContactType.address, search_parameters)
        
    def _find_objects(self, object_type, search_parameters):
        pass

#------------------------------------------------------------------------------

class Object:

    def __init__(self):
        

#------------------------------------------------------------------------------

# class ObjectType:

    # def __init__(self):
        # self._attribute_map = OrderedDict()
        # for attr_name, attr_type in self.iter_attributes():
            # self._attribute_map[attr_name] = attr_type

    # @property
    # def name(self):
        # raise Exception("abstract type")
        
    # def find_attribute(self, attr_name):
        # return self._attribute_map.get(attr_name, None)
        
    # def get_attribute(self, attr_name):
        # return self._attribute_map[attr_name]

#------------------------------------------------------------------------------

# class PersonType(ObjectType):

    # @property
    # def name(self):
        # return 'person'
        
    # def iter_attributes(self):
        # yield 'lastname', Str
        # yield 'firstname', Str
        # yield 'nickname', Str
        # yield 'day_of_birth', Date
        # yield 'day_of_death', Date
        # yield 'private_address', Address
        # yield 'private_email', EMail
        # yield 'private_mobile', PhoneNumber
        # yield 'private_url', Url
        # yield 'business_address', Address
        # yield 'business_email', EMail
        # yield 'business_phone', PhoneNumber
        # yield 'keywords', Str
        # yield 'remark', Text
        # yield 'child', Person
        # yield 'partner', Person

#------------------------------------------------------------------------------

# class AddressType(ObjectType):

    # @property
    # def name(self):
        # return 'address'
        
    # def iter_attributes(self):
        # yield 'street', Str
        # yield 'city', Str
        # yield 'country', Str
        # yield 'phone', PhoneNumber

#------------------------------------------------------------------------------

# class CompanyType(ObjectType):

    # @property
    # def name(self):
        # return 'company'
        
    # def iter_attributes(self):
        # yield 'name', Str
        # yield 'owner', Str
        # yield 'address', Address
        # yield 'homepage', Url
        # yield 'phone', PhoneNumber
        # yield 'mobile', PhoneNumber
        # yield 'email', EMail
        # yield 'open_times', Str
        # yield 'keywords', Str
        # yield 'remark', Text
        
#==============================================================================

class ContactObject:

    def __init__(self, type_name)
        self._type_name = type_name
        self._values = {}  # name -> list of values
        
    @property
    def type(self):
        return self._type
        
    def get_attr_value(self, attr_name):
        return self._values[attr_name]
        
    def get_attr_type(self, attr_name):
        for a_name, a_type in self.iter_attributes():
            if a_name == attr_name:
                return a_type
        raise Exception('Attribute-type {} not found'.format(attr_name))

#------------------------------------------------------------------------------

class Person(ContactObject):

    type_name = 'person'

    def __init__(self):
        ContactObject.__init__(self, PersonType())

    @static_method
    def iter_attributes():
        yield 'lastname', Str, None
        yield 'firstname', Str, None
        yield 'nickname', Str, None
        yield 'day_of_birth', Date, None
        yield 'day_of_death', Date, None
        yield 'private_address', Address, 'residents'
        yield 'private_email', EMail, None
        yield 'private_mobile', PhoneNumber, None
        yield 'private_url', Url, None
        yield 'company', Company, 'employees'
        yield 'business_address', Address, None
        yield 'business_email', EMail, None
        yield 'business_phone', PhoneNumber, None
        yield 'keywords', Str, None
        yield 'remark', Text, None
        yield 'child',   Person, 'parent'
        yield 'partner', Person, 'partner'
        
#------------------------------------------------------------------------------
       
class Company(ContactObject):

    type_name = 'company'

    def __init__(self):
        ContactObject.__init__(self, CompanyType())
        
    @static_method
    def iter_attributes():
        yield 'name', Str
        yield 'owner', Str
        yield 'address', Address
        yield 'homepage', Url
        yield 'phone', PhoneNumber
        yield 'mobile', PhoneNumber
        yield 'email', EMail
        yield 'open_times', Str
        yield 'keywords', Str
        yield 'remark', Text
        
#------------------------------------------------------------------------------
       
class Address(ContactObject):

    type_name = 'address'

    def __init__(self):
        ContactObject.__init__(self, AddressType())

    @static_method
    def iter_attributes():
        yield 'street', Str
        yield 'city', Str
        yield 'country', Str
        yield 'phone', PhoneNumber
        