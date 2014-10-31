##########################################
## CC-PIM                               ##
## Copyright 2013 by Christian Czepluch ##
##########################################

import sys
from pathlib import Path
from zipfile import ZipFile
import csv
import io
from collections import Counter, OrderedDict
import json
import datetime
from db import Model, Table
from cmd import Command

class const:
    root_dir            = Path(sys.argv[0]).resolve().parents[1]
    archive_dir         = root_dir.parent / 'cc-address' / 'archive'
    out_dir             = root_dir
    # zip_pathes          = list(archive_dir.glob('data-01.zip'))
    zip_pathes          = sorted(list(archive_dir.glob('data-??.zip')) +
                                 list(archive_dir.glob('data-11-rekronstruiert.zip')))
    persons_filename    = 'persons.csv'
    companies_filename  = 'companies.csv'
    entry_sep           = ';'
    json_filename       = 'import.json'
    json_ident          = 4  # None

#-------------------------------------------------------------------------------

def main():
    revisions = Revisions()
    
    persons_key = ('Lastname', 'Firstname')
    persons_table_name = 'persons'
    prev_persons = CvsData(persons_table_name, persons_key)
    table_created = False
    for zip_path in const.zip_pathes:
        with ZipFile(str(zip_path)) as data_zip:
            print('{}:'.format(zip_path))
            
            zip_mtime    = zip_path.stat().st_mtime
            zip_datetime = datetime.datetime.fromtimestamp(zip_mtime)
            
            cmd_list = []
            if not table_created:
                cmd_list += [Command('crate table', 'persons'), Command('crate table', 'companies')]
                table_created = True

            persons_file = data_zip.open(const.persons_filename)
            persons = CvsData(persons_table_name, persons_key)
            persons.read(persons_file)
            persons.init_id2rows(prev_persons)
            
            #print(len(persons.cols_name))
            #print(persons.rows_data[0])
            
            cols_comparer = ColumnsComparer(prev_persons.cols_name, persons.cols_name)
            cols_diff = cols_comparer.compare()
            #print(cols_diff)
            cmd_list += cols_diff.create_cmd_list(persons_table_name)
            
            rows_id_diff = RowsIdDiff(prev_persons, persons)
            cmd_list += rows_id_diff.create_cmd_list(persons_table_name)
            
            for row_id in rows_id_diff.common_id_list:
                row1 = prev_persons.get_row(row_id)
                row2 = persons.get_row(row_id)
                rows_comparer = RowsComparer(row1, row2, cols_diff)
                rows_diff = rows_comparer.compare()
                # print(rows_diff)
                cmd_list += rows_diff.create_cmd_list(persons_table_name)

            for row_id in rows_id_diff.added_id_list:
                row2 = persons.get_row(row_id)
                cmd_list += row2.create_cmd_list(persons_table_name)
                
            revisions.append(
                Revision(zip_datetime, cmd_list))
                
            prev_persons = persons
                
    out_path = const.out_dir / const.json_filename
    out_path.open('w').write(revisions.create_json_string())
            
#-------------------------------------------------------------------------------

class CvsData:
    def __init__(self, table_name, key_col_names):
        self._key_col_names = key_col_names
        self._key2row = {}
        self._id2row = {}
        self._next_id = 1
        self.table_name = table_name
        self.cols_name = []
        self.rows_data = []
        
    def read(self, fh):
        print('fh: {}'.format(type(fh)))
        text_wrapper = io.TextIOWrapper(fh, encoding='latin-1')
        reader = csv.DictReader(text_wrapper, delimiter=const.entry_sep, skipinitialspace=True)
        self.cols_name = reader.fieldnames
        self.rows_data = list(reader)
            
        self._init_key2row()

    def _init_key2row(self):
        self._key2row = {}
        for i in range(len(self.rows_data)):
            row = Row(self, i)
            key = (row.data[x] for x in self._key_col_names)
            if key in self._key2row:
                raise Exception(key)
            self._key2row[key] = row

    def init_id2rows(self, other):
        self._id2row = {}
        self._transfer_ids(other)
        self._fill_up_ids(other._next_id)
    
    def _transfer_ids(self, other):
        common_keys = set(self._key2row.keys()) &  set(other._key2row.keys())
        for key in common_keys:
            self_row  = self._key2row[key]
            other_row = other._key2row[key]
            self_row.set_id(other_row.id)
            self._id2row[other_row.id] = self_row

    def _fill_up_ids(self, next_id):
        for key, row in self._key2row.items():
            if row.id is None:
                row.set_id(next_id)
                self._id2row[next_id] = row
                next_id += 1
        self._next_id = next_id
        
    def row_id_set(self):
        return set(self._id2row.keys())
        
    def get_row(self, row_id):
        return self._id2row[row_id]
    
#---------------------------------------------------------------------------

class Row:
    def __init__(self, cvs_data, index):
        self._cvs_data  = cvs_data
        self._row_data  = cvs_data.rows_data[index]
        self._index     = index
        self._id        = None
        
    @property
    def id(self):
        return self._id
        
    @property
    def data(self):
        return self._row_data
        
    @property
    def table_name(self):
        return self._cvs_data.table_name
        
    def set_id(self, row_id):
        assert self._id is None
        self._id = row_id
        
    def create_cmd_list(self, table_name) -> '[Command]':
        return [Command('set value', table_name, self.id, x, self._row_data[x])
                for x in self._cvs_data.cols_name
                if self._row_data[x] not in (None, '')]
        
#---------------------------------------------------------------------------

class ColumnsComparer:
    def __init__(self, col_list1, col_list2):
        self.cols1 = col_list1
        self.cols2 = col_list2
        
    def compare(self):
        diff = ColumnsDiff()
        # if self.cols1 == self.cols2:
            # return diff
            
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
                diff.map_col(col1, col2)
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
                diff.map_col(col1, col2)
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
        self.removed_col_names = []
        self.added_col_names = []
        self.mapping = {}
        
    def __str__(self):
        lines  = ['-{}'.format(x) for x in self.removed_col_names]
        lines += ['+{}'.format(x) for x in self.added_col_names]
        lines += ['{} -> {}'.format(x, y) for x, y in self.mapping.items()]
        return '  ' + '\n  '.join(lines)
        
    def __repr__(self):
        return str(self)
        
    def remove_col(self, col_name):
        self.removed_col_names.append(col_name)
        
    def add_col(self, col_name):
        self.added_col_names.append(col_name)
        
    def map_col(self, col_name_old, col_name_new):
        self.mapping[col_name_old] = col_name_new
        
    def create_cmd_list(self, table_name) -> '[Command]':
        cmd_list  = [Command('remove col', table_name, x)      for x      in self.removed_col_names]
        cmd_list += [Command('add col',    table_name, x)      for x      in self.added_col_names]
        cmd_list += [Command('rename col', table_name, x1, x2) for x1, x2 in self.mapping.items() if x1 != x2]
        return cmd_list
        
#---------------------------------------------------------------------------

class RowsIdDiff:
    def __init__(self, cvs_data1:'CvsData', cvs_data2:'CvsData'):
        assert isinstance(cvs_data1, CvsData)
        assert isinstance(cvs_data2, CvsData)
        self.cvs_data1 = cvs_data1
        self.cvs_data2 = cvs_data2
        
        ids1 = cvs_data1.row_id_set()
        ids2 = cvs_data2.row_id_set()
        
        self.removed_id_list = list(ids1 - ids2)
        self.added_id_list   = list(ids2 - ids1)
        self.common_id_list  = list(ids1 & ids2)

    def create_cmd_list(self, table_name) -> '[Command]':
        cmd_list  = [Command('remove row', table_name, x) for x in self.removed_id_list]
        cmd_list += [Command('add row',    table_name, x) for x in self.added_id_list]
        return cmd_list
        
#---------------------------------------------------------------------------

class RowsComparer:
    def __init__(self, row1:'Row', row2:'Row', col_diff:'ColumnsDiff'):
        assert isinstance(row1, Row)
        assert isinstance(row2, Row)
        assert isinstance(col_diff, ColumnsDiff)
        self.row1 = row1
        self.row2 = row2
        self._col_diff = col_diff
        
    def compare(self) -> 'RowsDiff':
        diff = RowsDiff(self.row1, self.row2)
        
        # common columns
        for col_name1, col_name2 in self._col_diff.mapping.items():
            val1 = self.row1.data[col_name1]
            val2 = self.row2.data[col_name2]
            if val1 != val2:
                diff.add(col_name2, val2)
                
        # new columns
        for col_name2 in self._col_diff.added_col_names:
            val2 = self.row2.data[col_name2]
            if val2 is not None and val2 != '':
                diff.add(col_name2, val2)
            
        return diff
        
#---------------------------------------------------------------------------

class RowsDiff:
    def __init__(self, row1:'Row', row2:'Row'):
        assert isinstance(row1, Row)
        assert isinstance(row2, Row)
        self.row1 = row1
        self.row2 = row2
        self.diff_list = []
        
    def add(self, col_name2, value2):
        self.diff_list.append(
            RowDiff(col_name2, value))
        
    def create_cmd_list(self, table_name) -> '[Command]':
        return [x.create_cmd(table_name) for x in self.diff_list]
    
#---------------------------------------------------------------------------

class RowDiff:
    def __init__(self, col_name, value):
        self.col_name = col_name
        self.value    = value
        
    def create_cmd(self, table_name) -> 'Command':
        return Command('set value', table_name, row_id, self.col_name, value)
        
#---------------------------------------------------------------------------

class Revision:
    def __init__(self, date_time:datetime.datetime, cmd_list:'[Command]'):
        self.date = date_time
        self.user = 'Christian Czepluch'
        self.action = 'import'
        self.cmd_list = cmd_list
        
    def create_json_dict(self)->{str:str}:
        return OrderedDict([
            ("date",    self.date.strftime('%Y-%m-%d_%H:%M:%S')),
            ("user",    self.user),
            ("action",  self.action),
            ("changes", [x.create_json_list() for x in self.cmd_list]),
        ])

#---------------------------------------------------------------------------

class Revisions:
    def __init__(self):
        self._revisions = []
        
    def append(self, revision:Revision):
        assert isinstance(revision, Revision)
        self._revisions.append(revision)
        
    def create_json_string(self)->{str:str}:
        data = [x.create_json_dict() for x in self._revisions]
        return json.dumps(data, sort_keys=False, indent=const.json_ident)

#---------------------------------------------------------------------------

if __name__ == '__main__':
    main()
