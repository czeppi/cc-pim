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
        events = db.create_table('events')
        events.add_col('date', Date())
        events.add_col('name', Name())
        events.add_col('remarks', Text())
        
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
        
        addresses = db.create_table('addresses')
        addresses.add_col('street', Str())
        addresses.add_col('street_no', Str(re=r'[0-9]{1:5}[a-z]?'))  # '13-15' bisher nicht möglich
        addresses.add_col('hint', Str())
        addresses.add_col('city', Name())
        addresses.add_col('postcode', Str())
        addresses.add_col('country', Name())
        
        person_main_addresses = db.create_table('person_main_addresses')
        person_main_addresses.add_col('person', Foreignkey(persons))
        person_main_addresses.add_col('address', Foreignkey(addresses))
        person_main_addresses.add_col('valid_since', Foreignkey(events))
        
        person_further_addresses = db.create_table('person_further_addresses')
        person_further_addresses.add_col('person', Foreignkey(persons))
        person_further_addresses.add_col('address', Foreignkey(addresses))
        person_further_addresses.add_col('valid_since', Foreignkey(events))
        person_further_addresses.add_col('valid_until', Foreignkey(events))
        
        address_landline_phones = db.create_table('address_landline_phones')
        address_landline_phones.add_col('address', Foreignkey(addresses))
        address_landline_phones.add_col('number', Phonenumber())
        address_landline_phones.add_col('valid_since', Foreignkey(events))
        address_landline_phones.add_col('valid_until', Foreignkey(events))
        
        keywords = db.create_table('keywords')
        keywords.add_col('word', Str())
        
        keyword_synonyms = db.create_table('keyword_synonyms')
        keyword_synonyms.add_col('keyword', Foreignkey(keywords))
        keyword_synonyms.add_col('synonym', Str())
        
        person_keywords = db.create_table('person_keywords')
        person_keywords.add_col('person', Foreignkey(persons))
        person_keywords.add_col('word', Foreignkey(keywords))
        
        person_remarks = db.create_table('person_remarks')
        person_remarks.add_col('person', Foreignkey(persons))
        person_remarks.add_col('remark', Text())
        
        person_emails = db.create_table('person_emails')
        person_emails.add_col('person', Foreignkey(persons))
        person_emails.add_col('email', EMail())
        person_emails.add_col('valid_since', Foreignkey(events))
        person_emails.add_col('valid_until', Foreignkey(events))
        person_emails.add_col('enabled', Bool())
        
        person_homepages = db.create_table('person_homepages')
        person_homepages.add_col('person', Foreignkey(persons))
        person_homepages.add_col('url', URL())
        person_homepages.add_col('valid_since', Foreignkey(events))
        person_homepages.add_col('valid_until', Foreignkey(events))
        
        person_companies = db.create_table('person_companies')
        person_companies.add_col('person', Foreignkey(persons))
        person_companies.add_col('company', Foreignkey(companies))
        person_companies.add_col('address', Foreignkey(addresses))
        person_companies.add_col('phone', Phonenumber())
        person_companies.add_col('mobile', Phonenumber())
        person_companies.add_col('valid_since', Foreignkey(events))
        person_companies.add_col('valid_until', Foreignkey(events))
        
        
        

#-------------------------------------------------------------------------------
    
