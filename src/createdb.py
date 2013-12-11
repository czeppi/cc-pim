#! /usr/bin/env python
#-*- coding: utf-8 -*-

##########################################
## CC-PIM                               ##
## Copyright 2013 by Christian Czepluch ##
##########################################

from db import DB
from db import Name
from db import Text
from db import Str
from db import Date
from db import Foreignkey
from db import Phonenumber
from db import EMail
from db import URL

#-------------------------------------------------------------------------------

class AddressDBCreator:
    def __init__(self):
        pass
        
    def Create(self):
        db = DB()
        self.db = db
        
        self._CreateEvents(db)
        self._CreateKeywords(db)
        self._CreateAddresses(db)
        self._CreateCompanies(db)
        self._CreatePersons(db)
        
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
        
        company_addresses = db.create_table('company_addresses')
        company_addresses.add_col('company', Foreignkey(companies))
        company_addresses.add_col('address', Foreignkey(addresses))
        company_addresses.add_col('valid_since', Foreignkey(events))
        
        company_keywords = db.create_table('company_keywords')
        company_keywords.add_col('person', Foreignkey(persons))
        company_keywords.add_col('word', Foreignkey(keywords))
        
        company_remarks = db.create_table('company_remarks')
        company_remarks.add_col('person', Foreignkey(persons))
        company_remarks.add_col('remark', Text())
        
        company_urls = db.create_table('company_urls')
        company_urls.add_col('company', Foreignkey(companies))
        company_urls.add_col('url', URL)
        company_urls.add_col('valid_since', Foreignkey(events))
        company_urls.add_col('valid_until', Foreignkey(events))
        company_urls.add_col('remark', Str())

        company_landlines = db.create_table('company_landlines')
        company_landlines.add_col('company', Foreignkey(companies))
        company_landlines.add_col('landline', Phonenumber())
        company_landlines.add_col('remark', Str())
        company_landlines.add_col('valid_since', Foreignkey(events))
        company_landlines.add_col('valid_until', Foreignkey(events))
        company_landlines.add_col('enabled', Bool())
        
        company_mobiles = db.create_table('company_mobiles')
        company_mobiles.add_col('person', Foreignkey(persons))
        company_mobiles.add_col('company', Foreignkey(companies))
        company_mobiles.add_col('mobile', Phonenumber())
        company_mobiles.add_col('remark', Str())
        company_mobiles.add_col('valid_since', Foreignkey(events))
        company_mobiles.add_col('valid_until', Foreignkey(events))
        company_mobiles.add_col('enabled', Bool())
        
        company_emails = db.create_table('person_companie_emails')
        company_emails.add_col('person', Foreignkey(persons))
        company_emails.add_col('company', Foreignkey(companies))
        company_emails.add_col('email', EMail())
        company_emails.add_col('remark', Str())
        company_emails.add_col('valid_since', Foreignkey(events))
        company_emails.add_col('valid_until', Foreignkey(events))
        company_emails.add_col('enabled', Bool())
        
    def _CreatePersons(self, db):
        persons = db.create_table('persons')
        persons.add_col('first_name', Name())
        persons.add_col('birthday', Foreignkey(events))
        
        person_lastnames = db.create_table('person_lastnames')
        person_lastnames.add_col('person', Foreignkey(persons))
        person_lastnames.add_col('valid_since', Foreignkey(events))
        person_lastnames.add_col('name', Foreignkey(events))
        
        person_nicknames = db.create_table('person_nicknames')
        person_nicknames.add_col('person', Foreignkey(persons))
        person_nicknames.add_col('valid_since', Foreignkey(events))
        person_nicknames.add_col('name', Foreignkey(events))
        
        person_keywords = db.create_table('person_keywords')
        person_keywords.add_col('person', Foreignkey(persons))
        person_keywords.add_col('word', Foreignkey(keywords))
        
        person_remarks = db.create_table('person_remarks')
        person_remarks.add_col('person', Foreignkey(persons))
        person_remarks.add_col('remark', Text())
        
        person_main_addresses = db.create_table('person_main_addresses')
        person_main_addresses.add_col('person', Foreignkey(persons))
        person_main_addresses.add_col('address', Foreignkey(addresses))
        person_main_addresses.add_col('valid_since', Foreignkey(events))
        
        person_further_addresses = db.create_table('person_further_addresses')
        person_further_addresses.add_col('person', Foreignkey(persons))
        person_further_addresses.add_col('address', Foreignkey(addresses))
        person_further_addresses.add_col('remark', Str())
        person_further_addresses.add_col('valid_since', Foreignkey(events))
        person_further_addresses.add_col('valid_until', Foreignkey(events))
        
        person_emails = db.create_table('person_emails')
        person_emails.add_col('person', Foreignkey(persons))
        person_emails.add_col('email', EMail())
        person_emails.add_col('valid_since', Foreignkey(events))
        person_emails.add_col('valid_until', Foreignkey(events))
        person_emails.add_col('enabled', Bool())
        
        person_homepages = db.create_table('person_homepages')
        person_homepages.add_col('person', Foreignkey(persons))
        person_homepages.add_col('url', URL())
        person_homepages.add_col('remark', Str())
        person_homepages.add_col('valid_since', Foreignkey(events))
        person_homepages.add_col('valid_until', Foreignkey(events))
        
        person_companies = db.create_table('person_companies')
        person_companies.add_col('person', Foreignkey(persons))
        person_companies.add_col('company', Foreignkey(companies))
        person_companies.add_col('remark', Str())
        person_companies.add_col('valid_since', Foreignkey(events))
        person_companies.add_col('valid_until', Foreignkey(events))
        
        person_company_addresses = db.create_table('person_companie_addresses')
        person_company_addresses.add_col('person', Foreignkey(persons))
        person_company_addresses.add_col('company', Foreignkey(companies))
        person_company_addresses.add_col('address', Foreignkey(addresses))
        person_company_addresses.add_col('remark', Str())
        person_company_addresses.add_col('valid_since', Foreignkey(events))
        person_company_addresses.add_col('valid_until', Foreignkey(events))
        
        person_company_landlines = db.create_table('person_companie_landlines')
        person_company_landlines.add_col('person', Foreignkey(persons))
        person_company_landlines.add_col('company', Foreignkey(companies))
        person_company_landlines.add_col('landline', Phonenumber())
        person_company_landlines.add_col('remark', Str())
        person_company_landlines.add_col('valid_since', Foreignkey(events))
        person_company_landlines.add_col('valid_until', Foreignkey(events))
        person_company_landlines.add_col('enabled', Bool())
        
        person_company_mobiles = db.create_table('person_companie_mobiles')
        person_company_mobiles.add_col('person', Foreignkey(persons))
        person_company_mobiles.add_col('company', Foreignkey(companies))
        person_company_mobiles.add_col('mobile', Phonenumber())
        person_company_mobiles.add_col('remark', Str())
        person_company_mobiles.add_col('valid_since', Foreignkey(events))
        person_company_mobiles.add_col('valid_until', Foreignkey(events))
        person_company_mobiles.add_col('enabled', Bool())
        
        person_companie_emails = db.create_table('person_companie_emails')
        person_companie_emails.add_col('person', Foreignkey(persons))
        person_companie_emails.add_col('company', Foreignkey(companies))
        person_companie_emails.add_col('email', EMail())
        person_companie_emails.add_col('remark', Str())
        person_companie_emails.add_col('valid_since', Foreignkey(events))
        person_companie_emails.add_col('valid_until', Foreignkey(events))
        person_companie_emails.add_col('enabled', Bool())

    def _Create1toN(self, conn_name, name1, table1, name2, table2, 
                    with_remark=False, with_enabled=False):
        table = db.create_table(conn_name)
        table.add_col(name1, Foreignkey(table1))
        table.add_col(name2, Foreignkey(table2))
        table.add_col('valid_since', Foreignkey(events))
        if with_remark:
            table.add_col('remark', Str())
        if with_enabled:
            table.add_col('enabled', Bool())
    
    def _CreateNtoN(self, conn_name, name1, table1, name2, table2, 
                    with_remark=False, with_enabled=False):
        events = self.events_table
        
        table = db.create_table(conn_name)
        table.add_col(name1, Foreignkey(table1))
        table.add_col(name2, Foreignkey(table2))
        table.add_col('valid_since', Foreignkey(events))
        table.add_col('valid_until', Foreignkey(events))
        if with_remark:
            table.add_col('remark', Str())
        if with_enabled:
            table.add_col('enabled', Bool())
    
