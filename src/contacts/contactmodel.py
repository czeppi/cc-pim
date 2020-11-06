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

from __future__ import annotations
from collections import OrderedDict, defaultdict
from enum import Enum
from functools import total_ordering
import re
from typing import Any, Dict, Iterator, Optional, List, Iterable, Tuple

from contacts.basetypes import Date, EMail, PhoneNumber, Url, Str, Text, Ref, Fact, VagueDate
from contacts.repository import Repository


class ContactType(Enum):

    PERSON = 1
    COMPANY = 2
    ADDRESS = 3


class Predicate:

    def __init__(self, serial: int, subject_class: Contact, name: str, value_type: Any):
        self.serial = serial
        self.subject_class = subject_class
        self.name = name
        self.value_type = value_type

        
class Attribute:

    def __init__(self, name: str, value_type: Any, predicate_serial: int):
        self.name = name
        self.value_type = value_type
        self.predicate_serial = predicate_serial
    
        
class Contact:

    contact_type = None
    type_name = None
    attributes = None
    back_attributes = None
    last_serial = None

    def __init__(self, serial: int):
        self.serial = serial
        self._facts_map: Dict[str, List[Fact]] = defaultdict(list)  # attr-name -> list of facts
        self._back_facts_map: Dict[str, List[Fact]] = defaultdict(list)

    @property
    def title(self) -> str:
        raise NotImplemented()

    @classmethod
    def iter_attributes(cls) -> Iterator[Attribute]:
        yield from cls.attributes.values()
        
    @classmethod
    def iter_back_attributes(cls) -> Iterator[Attribute]:
        yield from cls.back_attributes.values()

    @classmethod
    def get_attribute(cls, attr_name: str) -> Attribute:
        if attr_name in cls.attributes:
            return cls.attributes[attr_name]
        else:
            return cls.back_attributes[attr_name]
    
    @classmethod
    def find_attribute(cls, attr_name: str) -> Optional[Attribute]:
        attr = cls.attributes.get(attr_name, None)
        if attr is None:
            attr = cls.back_attributes.get(attr_name, None)
        return attr

    @property
    def id(self) -> ContactID:
        return ContactID(self.contact_type, self.serial)

    def add_fact(self, attr_name: str, fact: Fact) -> None:
        self._facts_map[attr_name].append(fact)

    def get_facts(self, attr_name: str) -> List[Fact]:
        return self._facts_map.get(attr_name, [])

    def get_fact(self, fact_serial: int) -> Optional[Fact]:
        for facts in self._facts_map.values():
            for fact in facts:
                if fact.serial == fact_serial:
                    return fact

    def contains_keyword(self, keyword: str) -> bool:
        lower_keyword = keyword.lower()
        return any(lower_keyword in str(fact.value).lower()
                   for fact_list in self._facts_map.values()
                   for fact in fact_list)

    def contains_all_keywords(self, keywords: Iterable[str]) -> bool:
        return all(self.contains_keyword(x) for x in keywords)

    def does_meet_the_criteria(self, search_words: Iterable[str], category: str) -> bool:
        if category and category != self.contact_type.name.lower():
            return False
        return all(self.contains_keyword(x) for x in search_words)

    def copy(self) -> Contact:
        new_contact = _create_contact(self.contact_type, self.serial)
        for attr_name, fact_list in self._facts_map.items():
            for fact in fact_list:
                new_contact.add_fact(attr_name, fact.copy())
        return new_contact


class Person(Contact):

    contact_type = ContactType.PERSON
    type_name = contact_type.name
    attributes: Dict[str, Attribute] = OrderedDict()
    back_attributes: Dict[str, Attribute] = OrderedDict()
    last_serial = 0

    @property
    def title(self) -> str:
        first_names = [x.value for x in self._facts_map['firstname']]
        last_names = [x.value for x in self._facts_map['lastname']]
        names_parts = []
        if first_names:
            names_parts.append(first_names[-1])
        if last_names:
            names_parts.append(last_names[-1])
        if len(names_parts) == 0:
            return '#' + str(self.serial)
        return ' '.join(names_parts)


class Company(Contact):

    contact_type = ContactType.COMPANY
    type_name = contact_type.name
    attributes: Dict[str, Attribute] = OrderedDict()
    back_attributes: Dict[str, Attribute] = OrderedDict()
    last_serial = 0

    @property
    def title(self) -> str:
        names = [x.value for x in self._facts_map['name']]
        if names:
            return names[-1]
        else:
            return '#' + str(self.serial)


class Address(Contact):

    contact_type = ContactType.ADDRESS
    type_name = contact_type.name
    attributes: Dict[str, Attribute] = OrderedDict()
    back_attributes: Dict[str, Attribute] = OrderedDict()
    last_serial = 0

    @property
    def title(self) -> str:
        parts = []
        parts += [x.value for x in self._facts_map['street']]
        parts += [x.value for x in self._facts_map['city']]
        parts += [x.value for x in self._facts_map['phone']]
        return ', '.join(parts)


def _create_contact(contact_type: ContactType, obj_serial: int) -> Contact:
    cls_map = {
        Person.contact_type:  Person,
        Company.contact_type: Company,
        Address.contact_type: Address,
    }
    return cls_map[contact_type](obj_serial)


@total_ordering
class ContactID:
    _REX = re.compile(r"(?P<type>[a-zA-Z]+)(?P<serial>[0-9]+)")

    @classmethod
    def create_from_string(cls, id_str: str) -> ContactID:
        match = cls._REX.match(id_str)
        if not match:
            raise ValueError(id_str)

        type_name = match.group('type').upper()
        contact_type = ContactType[type_name]
        serial = int(match.group('serial'))
        return ContactID(contact_type, serial)

    def __init__(self, contact_type: ContactType, serial: int):
        self.contact_type = contact_type
        self.serial = serial

    def __str__(self):
        return self.contact_type.name.lower() + str(self.serial)

    def __eq__(self, other):
        return (self.contact_type, self.serial) == (other.contact_type, other.serial)

    def __lt__(self, other):
        return (self.contact_type.value, self.serial) < (other.contact_type.value, other.serial)

    def __hash__(self):
        return hash((self.contact_type, self.serial))


def _iter_predicates_data() -> Iterator[Tuple[int, Contact, str, Any]]:
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
    def iter_object_classes() -> Iterator[Contact]:
        yield Person
        yield Company
        yield Address
        
    def __init__(self, date_changes: Dict[int, VagueDate], fact_changes: Dict[int, Fact]):
        self._date_changes = date_changes
        self._fact_changes = fact_changes
        self._uncommitted_date_changes: Dict[int, VagueDate] = {}
        self._uncommitted_fact_changes: Dict[int, Fact] = {}
        self._revision_number = None

        self._contacts: Dict[ContactID, Contact] = {}
        self._init_contacts()
        self._init_last_serial_map()
        self._last_fact_serial = self._calc_last_fact_serial()
        self._last_date_serial = self._init_last_date_serial()

    def _init_contacts(self) -> None:
        self._contacts.clear()
        for fact in self._fact_changes.values():
            predicate = self.predicates[fact.predicate_serial]
            contact_type = predicate.subject_class.contact_type
            obj_serial = fact.subject_serial
            contact_id = ContactID(contact_type, obj_serial)
            obj = self._contacts.get(contact_id, None)
            if obj is None:
                obj = _create_contact(contact_type, obj_serial)
                self._contacts[contact_id] = obj
            obj.add_fact(predicate.name, fact)

    def _init_last_serial_map(self) -> None:
        self._last_serial_map = {
            cls.contact_type: max((contact_id.serial for contact_id in self._contacts.keys()
                                   if contact_id.contact_type == cls.contact_type), default=0)
            for cls in self.iter_object_classes()
        }

    def _calc_last_fact_serial(self) -> int:
        return max((fact.serial for fact in self._fact_changes.values()), default=0)

    def _init_last_date_serial(self) -> int:
        return max((date.serial for date in self._date_changes.values()), default=0)

    def iter_objects(self) -> Iterator[Contact]:
        yield from self._contacts.values()

    def iter_back_facts(self, obj: Contact) -> Iterator[Fact]:
        for fact in self._fact_changes.values():
            predicate = self.predicates[fact.predicate_serial]
            if isinstance(predicate.value_type, Ref):
                ref = predicate.value_type
                if ref.target_class.contact_type == obj.contact_type \
                        and int(fact.value) == obj.serial:
                    yield fact

    def update(self) -> None:
        pass

    def iter_dates(self) -> Iterator[VagueDate]:
        yield from self._date_changes.values()

    def get_date(self, date_serial: int) -> VagueDate:
        return self._date_changes[date_serial]

    def contains(self, contact_id: ContactID) -> bool:
        return contact_id in self._contacts
        
    def get_contact(self, contact_id: ContactID) -> Contact:
        return self._contacts[contact_id]

    def find(self, search_parameters):
        pass

    def get_fact_value(self, fact: Fact) -> str:
        predicate = self.predicates[fact.predicate_serial]
        if isinstance(predicate.value_type, Ref):
            ref = predicate.value_type
            contact_type = ref.target_class.contact_type
            serial = int(fact.value)
            if serial == 0:
                return ''
            else:
                obj = self.get_contact(ContactID(contact_type, serial))
                return obj.title
        else:
            return fact.value

    def get_fact_subject(self, fact: Fact) -> Optional[Contact]:
        predicate = self.predicates[fact.predicate_serial]
        contact_type = predicate.subject_class.contact_type
        contact_id = ContactID(contact_type, fact.subject_serial)
        return self._contacts.get(contact_id, None)

    def get_fact_object(self, fact: Fact) -> Optional[Contact]:
        predicate = self.predicates[fact.predicate_serial]
        if isinstance(predicate.value_type, Ref):
            ref = predicate.value_type
            contact_type = ref.target_class.contact_type
            serial = int(fact.value)
            if serial != 0:
                return self.get_contact(ContactID(contact_type, serial))

    def add_changes(self, date_changes: Dict[int, VagueDate], fact_changes: Dict[int, Fact]):
        self._date_changes.update(date_changes)
        self._fact_changes.update(fact_changes)
        self._uncommitted_date_changes.update(date_changes)
        self._uncommitted_fact_changes.update(fact_changes)
        self._init_contacts()

    def exists_uncommitted_changes(self) -> bool:
        return len(self._uncommitted_date_changes) > 0 or len(self._uncommitted_fact_changes) > 0

    def commit(self, comment: str, repo: Repository) -> None:
        repo.commit(comment,
                    date_changes=self._uncommitted_date_changes,
                    fact_changes=self._uncommitted_fact_changes)
        self._uncommitted_date_changes.clear()
        self._uncommitted_fact_changes.clear()

    def create_contact(self, contact_type: ContactType) -> Contact:
        assert contact_type in self._last_serial_map
        new_serial = self._last_serial_map[contact_type] + 1
        self._last_serial_map[contact_type] = new_serial
        new_contact = _create_contact(contact_type, new_serial)
        return new_contact

    def create_fact_serial(self) -> int:
        new_serial = self._last_fact_serial + 1
        self._last_fact_serial = new_serial
        return new_serial

    def create_date_serial(self) -> int:
        new_serial = self._last_date_serial + 1
        self._last_date_serial = new_serial
        return new_serial
