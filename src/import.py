##########################################
## CC-PIM                               ##
## Copyright 2013 by Christian Czepluch ##
##########################################

import sys
from pathlib import Path
from zipfile import ZipFile
import csv
import io
from collections import Counter
import json
import datetime
from db import Model, Table
from cmd import Command

class const:
    root_dir            = Path(sys.argv[0]).resolve().parents[2]
    archive_dir         = root_dir / 'cc-address' / 'archive'
    # zip_pathes          = list(archive_dir.glob('data-01.zip'))
    zip_pathes          = sorted(list(archive_dir.glob('data-??.zip')) +
                                 list(archive_dir.glob('data-11-rekronstruiert.zip')))
    persons_filename    = 'persons.csv'
    companies_filename  = 'companies.csv'
    entry_sep           = ';'
    # persons_keys = [
        # 'Lastname', 'Firstname', 'Nickname', 'Birthday', 'Keywords', 'Remarks',
        # 'Home Phone', 'Home Mobile', 'Home E-Mail', 'Home Street', 'Home City', 'Homepage',
        # 'Company', 'Business Phone', 'Business Mobile', 'Business E-Mail', 'Business Street', 'Business City',
    # ]
    # companies_keys = [
        # 'Name', 'Owner', 'Homepage', 'Keywords', 'Open Times', 'Remarks',
        # 'Phone', 'Mobile', 'E-Mail', 'Street', 'City',
    # ]

#-------------------------------------------------------------------------------

def main():
    revisions = Revisions()
    revisions.append(
        Revision(datetime.datetime.today(), [
            Command('crate table', ['persons']), 
            Command('crate table', ['companies']),
            ]
        )
    )
    
    prev_persons = CvsData()
    for zip_path in const.zip_pathes:
        with ZipFile(str(zip_path)) as data_zip:
            print('{}:'.format(zip_path))
            persons_file = data_zip.open(const.persons_filename)
            persons = CvsData(persons_file)
            #print(len(persons.cols))
            #print(persons.rows[0])
            
            cols_comparer = ColumnsComparer(prev_persons.cols, persons.cols)
            cols_diff = cols_comparer.compare()
            print(cols_diff)
            
            rows_comparer = RowsComparer(prev_persons, persons)
            rows_diff = rows_comparer.compare()
            print(rows_diff)
            
            rows_diff.transfer_ids()
            persons.fill_up_ids(next_id=prev_persons.next_id)
            
            prev_persons = persons
            
            cmd_list = cols_diff.create_cmd_list() + rows_diff.create_cmd_list()
            # cols_json_data = cols_diff.create_json_data()
            # rows_json_data = rows_diff.create_json_data()
            revisions.append(
                Revision(datetime.datetime.today(), cmd_list))
#            revisions.append(
#                create_json_revision(datetime.datetime.today(), cols_json_data + rows_json_data))
                
    #print(dump_json(revisions))
    print(revisions.json())
            
#-------------------------------------------------------------------------------

class CvsData:
    def __init__(self, fh=None):
        print('fh: {}'.format(type(fh)))
        if fh is None:
            self.cols = []
            self.rows = []
        else:
            text_wrapper = io.TextIOWrapper(fh, encoding='latin-1')
            reader = csv.DictReader(text_wrapper, delimiter=const.entry_sep, skipinitialspace=True)
            self.cols = reader.fieldnames
            self.rows = list(reader)
            
        self.next_id = 1
        self.row_key2id = {}
        
    def check(self):
        key_counter = Counter(self._create_key(row) for row in self.rows)
        for key, count in key_counter.items():
            if count == 2:
                rows = [row for row in self.rows if self._create_key(row) == key]
                row1, row2 = rows
                if row1 == row2:
                    print('## ERROR ==: 2x: {}'.format(key))
                else:
                    print('## ERROR ==: 2x: {}'.format(key))
            elif count > 2:
                print('## ERROR: {}x: {}'.format(count, key))
                
        # key_set = set(self._create_key(row) for row in self.rows) 
        # if len(key_set) < len(self.rows):
            # print('## ERROR: missing: {}'.format(len(self.rows) - len(key_set)))
            
    def create_row_map(self):
        row_map = {}
        for row in self.rows:
            key = self._create_key(row)
            val = row_map.get(key, None)
            if val is None:
                row_map[key] = row
            elif val != row_map[key]:
                raise Exception('')
        return row_map

    def _create_key(self, row):
        return row['Lastname'], row['Firstname'] #, row['Nickname']
        
    def set_row_id(self, row_key, id):
        assert id not in self.row_key2id
        self.row_key2id[row_key] = id
        
    def get_row_id(self, row_key):
        return self.row_key2id[row_key]
        
    def fill_up_ids(self, next_id):
        for row in self.rows:
            row_key = self._create_key(row)
            if row_key not in self.row_key2id:
                self.set_row_id(row_key, next_id)
                next_id += 1
        self.next_id = next_id
        
#---------------------------------------------------------------------------

class ColumnsComparer:
    def __init__(self, col_list1, col_list2):
        self.cols1 = col_list1
        self.cols2 = col_list2
        
    def compare(self):
        diff = ColumnsDiff()
        if self.cols1 == self.cols2:
            return diff
            
        n1 = len(self.cols1)
        n2 = len(self.cols2)
        n_min = min(n1, n2)
        
        # n_left
        n_left = 0
        for i in range(n_min):
            col1, col2 = self.cols1[i], self.cols2[i]
            if self._was_renamed(col1, col2):
                diff.map_col(col1, col2)
            elif col1 == col2:
                n_left = i + 1
            else:
                break
                
        # n_right
        n_right = 0
        for i in range(n_min - n_left):
            col1, col2 = self.cols1[-i], self.cols2[-i]
            if self._was_renamed(col1, col2):
                diff.map_col(col1, col2)
            elif col1 == col2:
                n_right = i + 1
            elif col1 != col2:
                break
                
        # diff
        for i in range(n_left, n1 - n_right):
            diff.remove_col(self.cols1[i])
            
        for i in range(n_left, n2 - n_right):
            diff.add_col(self.cols2[i])
            
        return diff
        
    def _was_renamed(self, col1, col2):
        renaming_map = {
            'Home Address':     'Home Street',
            'Home Town':        'Home City',
            'Business Address': 'Business Street',
            'Business Town':    'Business City',
        }
        return renaming_map.get(col1, None) == col2
            
#---------------------------------------------------------------------------

class ColumnsDiff:
    def __init__(self):
        self.removed_cols = []
        self.added_cols = []
        self.mapping = {}
        
    def __str__(self):
        lines  = ['-{}'.format(x) for x in self.removed_cols]
        lines += ['+{}'.format(x) for x in self.added_cols]
        lines += ['{} -> {}'.format(x, y) for x, y in self.mapping.items()]
        return '  ' + '\n  '.join(lines)
        
    def __repr__(self):
        return str(self)
        
    def remove_col(self, col_name):
        self.removed_cols.append(col_name)
        
    def add_col(self, col_name):
        self.added_cols.append(col_name)
        
    def map_col(self, col_name_old, col_name_new):
        self.mapping[col_name_old] = col_name_new
        
    # def create_json_data(self):
        # data = []
        # for col in self.removed_cols:
            # self._add_json_cmd(data, 'remove col', col)
        # for col in self.added_cols:
            # self._add_json_cmd(data, 'add col', col)
        # for old_name, new_name in self.mapping.items():
            # self._add_json_cmd(data, 'rename col', old_name, new_name)
        # return data
        
    # def _add_json_cmd(self, data, cmd, *args):
        # data.append(['{}'.format(cmd)] + ['{}'.format(x) for x in args])

    def create_cmd_list(self)->'[Command]':
        cmd_list  = [Command('remove col', [x])      for x      in self.removed_cols]
        cmd_list += [Command('add col',    [x])      for x      in self.added_cols]
        cmd_list += [Command('rename col', [x1, x2]) for x1, x2 in self.mapping.items()]
        return cmd_list
        
#---------------------------------------------------------------------------

class RowsComparer:
    def __init__(self, data1:'CvsData', data2:'CvsData'):
        assert isinstance(data1, CvsData)
        assert isinstance(data2, CvsData)
        self.data1 = data1
        self.data2 = data2
        
    def compare(self) -> 'RowsDiff':
        diff = RowsDiff(self.data1, self.data2)
        row_map1 = diff.map1
        row_map2 = diff.map2
        
        keys1 = set(row_map1.keys())
        keys2 = set(row_map2.keys())
        for key in keys1 - keys2:
            #diff.remove_row(row_map1[key])
            diff.remove_row(key)
        for key in keys2 - keys1:
            #diff.add_row(row_map2[key])
            diff.add_row(key)
        for key in keys1 & keys2:
            row1 = row_map1[key]
            row2 = row_map2[key]
            if row1 != row2:
                #diff.change_row(row1, row2)
                #print('## {}\n   {}'.format(row1, row2))
                diff.change_row(key)
        return diff
        
#---------------------------------------------------------------------------

class RowsDiff:
    def __init__(self, data1:'CvsData', data2:'CvsData'):
        self.data1 = data1
        self.data2 = data2
        self.map1 = data1.create_row_map()
        self.map2 = data2.create_row_map()
        self.removed_rows = []
        self.added_rows = []
        self.changed_rows = []

    def __str__(self):
        return self._summary()
        
    def _summary(self) -> str:
        lines  = [
            '{} removed'.format(len(self.removed_rows)),
            '{} added'.format(len(self.added_rows)),
            '{} changed'.format(len(self.changed_rows)),
        ]
        return '  ' + '\n  '.join(lines)
        
    def _details(self)->str:
        lines  = ['removed:']
        lines += ['  {}'.format(x) for x in self.removed_rows]
        lines += ['added:']
        lines += ['  {}'.format(x) for x in self.added_rows]
        lines += ['changed:']
        lines += ['  {} -> {}'.format(x, y) for x, y in self.changed_rows]
        return '\n'.join(lines)
        
    def __repr__(self):
        return str(self)
        
    def remove_row(self, row_key:str):
        self.removed_rows.append(row_key)
        
    def add_row(self, row_key:str):
        self.added_rows.append(row_key)
        
    def change_row(self, row_key:str):
        self.changed_rows.append(row_key)
        
    # def create_json_data(self)->[str]:
        # data = []
        # for row in self.removed_rows:
            # self._add_json_cmd(data, 'remove row', row)
        # for row in self.added_rows:
            # self._add_json_cmd(data, 'add row', row)
        # for old_row, new_row in self.changed_rows:
            # self._add_json_cmd(data, 'change row', old_row, new_row)
        # return data
            
    # def _add_json_cmd(self, data, cmd, *args):
        # data.append(['{}'.format(cmd)] + ['{}'.format(x) for x in args])
        
    def transfer_ids(self):
        for key in self.changed_rows:
            row_id = self.data1.get_row_id(key)
            self.data2.set_row_id(key, row_id)
            
    def create_cmd_list(self)->'[Command]':
        cmd_list  = [Command('remove row', [self.data1.get_row_id(x)])      for x      in self.removed_rows]
        cmd_list += [Command('add row',    [self.data2.get_row_id(x)])      for x      in self.added_rows]
        #cmd_list += [Command('rename row', [x1, x2]) for x1, x2 in self.changed_rows]
        return cmd_list
        
#---------------------------------------------------------------------------

# def create_first_json_revision(date_time:datetime.datetime)->{str:object}:
    # return create_json_revision(date_time, [
        # ['crate table', 'persons'], 
# #        ['crate table', 'companies'], 
    # ])

# #---------------------------------------------------------------------------

# def create_json_revision(date_time:datetime.datetime, changes):
    # return Revision(date_time, changes)
    
#---------------------------------------------------------------------------

class Revision:
    def __init__(self, date_time:datetime.datetime, cmd_list:'[Command]'):
        self.date = date_time
        self.user = 'Christian Czepluch'
        self.action = 'import'
        self.cmd_list = cmd_list
        
    def json(self)->{str:str}:
        return {
            "date":    self.date.strftime('%Y-%m-%d_%H:%M:%S'),
            "user":    self.user,
            "action":  self.action,
#            "changes": '[{}]'.format(', '.join(x.json() for x in self.cmd_list)),
            "changes": [x.json() for x in self.cmd_list],
        }

#---------------------------------------------------------------------------

class Revisions:
    def __init__(self):
        self._revisions = []
        
    def append(self, revision:Revision):
        assert isinstance(revision, Revision)
        self._revisions.append(revision)
        
    def json(self)->{str:str}:
        data = [x.json() for x in self._revisions]
        return json.dumps(data, sort_keys=True, indent=4)

#---------------------------------------------------------------------------

# def dump_json(data):
    # return json.dumps(data, sort_keys=True, indent=4)

#---------------------------------------------------------------------------

if __name__ == '__main__':
    main()
