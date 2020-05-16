# Copyright (C) 2013  Christian Czepluch
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

from db import DB
from db import Name
from db import Text
from db import Str
from db import Date
from db import Foreignkey
from db import Phonenumber
from db import EMail
from db import URL


class AddressDBCreator:

    def __init__(self):
        pass
        
    def Create(self):
        db = DB()
        self.db = db
        
        self._CreateColumns()
        self._CreateEvents(db)
        self._CreateKeywords(db)
        self._CreateAddresses(db)
        self._CreateCompanies(db)
        self._CreatePersons(db)
        
    def _CreateColumnTypes(self):
        self._col_types = { name: type for name, type in self._IterColumn() }
        
    def _IterColumn(self):
        yield 'person', Foreignkey('persons')
        yield 'address', Foreignkey('addresses')
        yield 'remark', Str()
        yield 'enabled', Bool()
        yield 'company', Foreignkey('companies')
        yield 'valid_since', Foreignkey('events')
        yield 'valid_until', Foreignkey('events')
        yield 'mobile', Phonenumber()
        yield 'landline', Phonenumber()
        yield 'name', Name())
        yield 'keyword', Foreignkey('keywords')
        
    def _CreateEvents(self, db):
        events = db.create_table('events')
        events.add_col('date', Date())
        events.add_col('name', Name())
        events.add_col('remarks', Text())
        
    def _CreateKeywords(self, db):
        keywords = db.create_table('keywords')
        keywords.add_col('word', Str())
        
        keyword_synonyms = db.create_table('keyword_synonyms')
        keyword_synonyms.add_col('keyword', Foreignkey(keywords))
        keyword_synonyms.add_col('synonym', Str())
        
    def _CreateAddresses(self, db):
        addresses = db.create_table('addresses')
        addresses.add_col('street', Str())
        addresses.add_col('street_no', Str(re=r'[0-9]{1:5}[a-z]?'))  # '13-15' bisher nicht möglich
        addresses.add_col('hint', Str())
        addresses.add_col('city', Name())
        addresses.add_col('postcode', Str())
        addresses.add_col('country', Name())

        address_landline_phones = db.create_table('address_landline_phones')
        address_landline_phones.add_col('address', Foreignkey(addresses))
        address_landline_phones.add_col('number', Phonenumber())
        address_landline_phones.add_col('remark', Str())
        address_landline_phones.add_col('valid_since', Foreignkey(events))
        address_landline_phones.add_col('valid_until', Foreignkey(events))
        
    def _CreateCompanies(self, db):
        companies = db.create_table('companies')
        companies.add_col('name', Name())
        companies.add_col('owner', Name())
        
        self._CreateTable('company_addresses', 'company address valid_since remark')
        self._CreateTable('company_keywords',  'company keyword')
        self._CreateTable('company_remarks',   'company remark')
        self._CreateTable('company_urls',      'company url valid_since valid_until remark')
        self._CreateTable('company_emails',    'company email valid_since valid_until remark enabled')
        self._CreateTable('company_landlines', 'company landline valid_since valid_until remark enabled')
        self._CreateTable('company_mobiles',   'company mobile valid_since valid_until remark enabled')
        
    def _CreatePersons(self):
        persons = self.db.create_table('persons')
        persons.add_col('first_name', Name())
        persons.add_col('birthday', Foreignkey(events))
        
        self._CreateTable('person_lastnames',          'person name valid_since')
        self._CreateTable('person_nicknames',          'person name valid_since')
        self._CreateTable('person_main_addresses',     'person address valid_since remark')
        self._CreateTable('person_further_addresses',  'person address valid_since valid_until remark')
        self._CreateTable('person_keywords',           'person keyword')
        self._CreateTable('person_remarks',            'person remark')
        self._CreateTable('person_landlines',          'person landline valid_since valid_until remark enabled')
        self._CreateTable('person_mobiles',            'person mobile valid_since valid_until remark enabled')
        self._CreateTable('person_emails',             'person email valid_since valid_until remark enabled')
        self._CreateTable('person_homepages',          'person url valid_since valid_until remark')
        self._CreateTable('person_companies',          'person company valid_since valid_until remark')
        self._CreateTable('person_company_addresses',  'person company valid_since valid_until remark')
        self._CreateTable('person_companie_addresses', 'person company address valid_since valid_until remark')
        self._CreateTable('person_companie_landlines', 'person company landline valid_since valid_until remark enabled')
        self._CreateTable('person_companie_mobiles',   'person company mobile valid_since valid_until remark enabled')
        self._CreateTable('person_companie_emails',    'person company email valid_since valid_until remark enabled')

    def _CreateTable(self, table_name, col_names):
        table = self.db.create_table(table_name)
        for col_name in col_names.split():
            col_type = self._col_types[col_name]
            table.add_col(col_name, col_type)
    
    
