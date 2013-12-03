#! /usr/bin/env python
#-*- coding: utf-8 -*-

##########################################
## CC-PIM                               ##
## Copyright 2013 by Christian Czepluch ##
##########################################

import sys
import os.path

class const:
    src_dir             = os.path.dirname(sys.argv[0])
    data_dir            = os.path.join(src_dir, '../data/cc-address-import')
    persons_filename    = os.path.join(data_dir, "persons.csv")
    companies_filename  = os.path.join(data_dir, "companies.csv")
    entry_sep = ';'
    persons_keys = [
        'Lastname', 'Firstname', 'Nickname', 'Birthday', 'Keywords', 'Remarks',
        'Home Phone', 'Home Mobile', 'Home E-Mail', 'Home Street', 'Home City', 'Homepage',
        'Company', 'Business Phone', 'Business Mobile', 'Business E-Mail', 'Business Street', 'Business City',
    ]
    companies_keys = [
        'Name', 'Owner', 'Homepage', 'Keywords', 'Open Times', 'Remarks',
        'Phone', 'Mobile', 'E-Mail', 'Street', 'City',
    ]

#-------------------------------------------------------------------------------

def main():
    persons_data = ReadDataFile(const.persons_filename, 
                                const.persons_keys,
                                const.entry_sep)
    
    companies_data = ReadDataFile(const.companies_filename, 
                                  const.companies_keys,
                                  const.entry_sep)
                                  
    print('#persons={}, #companies={}'.format(len(persons_data), len(companies_data)))

#-------------------------------------------------------------------------------
    
def ReadDataFile(fname, keys, entry_sep):
    if not os.path.exists(fname):
        raise Exception(fname)
        
    # read -> lines
    fh = open(fname, 'r')
    lines = fh.readlines()
    fh.close()
    
    if len(lines) == 0:
        raise Exception(fname)
    
    # head
    head = SplitLine(lines[0], entry_sep)
    if head != keys:
        raise Exception("\n  keys = '%s'\n head = '%s'" % (str(keys), str(head)))
    
    # data
    data = []
    for line in lines[1:]:
        data.append(SplitLine(line, entry_sep))
    data.sort()
        
    return data

#---------------------------------------------------------------------------

def SplitLine(line, entry_sep):
    return list(map(lambda x: x.strip(), line.split(entry_sep)))

#---------------------------------------------------------------------------

if __name__ == '__main__':
    main()
