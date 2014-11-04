##########################################
## CC-PIM                               ##
## Copyright 2013 by Christian Czepluch ##
##########################################

# Import Log, der gelöschten Personen:
#
# G:\Eigene-Software\Python\cc-address\archive\data-02.zip:
#   - Biene Fragel => doppelt (Bianca Fragel)
#   - Rena Aglassinger
# G:\Eigene-Software\Python\cc-address\archive\data-06.zip:
#   - Christa Reeck? => doppelt
#   - Hermann Reeck? => doppelt
#   - Nicole Derbinski => doppelt
# G:\Eigene-Software\Python\cc-address\archive\data-07.zip:
#   - Uta => doppelt
# G:\Eigene-Software\Python\cc-address\archive\data-08.zip:
#   - Carola Begemann => Company
#   - Christian Jacob => Company
#   - Gritta Dunkel => Company
#   - Jörg Pagel => Company
#   - Yilmaz Kaakan => Company
# G:\Eigene-Software\Python\cc-address\archive\data-09.zip:
#   - Henner => doppelt
#   - Jari?  = Annette Jahreis
#   - Martin => doppelt (Martin Köbsch)

# Import Log, der gelöschten Companies:
#
# G:\Eigene-Software\Python\cc-pim\data\cc-address-import\data-06.zip:
  # - Kanustation Granzow => doppelt
  # - Virchow Krankenhaus => doppelt
  # - Virchow Krankenhaus => doppelt
# G:\Eigene-Software\Python\cc-pim\data\cc-address-import\data-09.zip:
  # - Bowling Hasenheide => doppelt (City-Bowling)
# G:\Eigene-Software\Python\cc-pim\data\cc-address-import\data-14.zip:
  # + => Rena, Second-Hand

import sys
from pathlib import Path
from zipfile import ZipFile
import csv
import io
from collections import Counter, OrderedDict
import json
import datetime
from difflib import SequenceMatcher
import logging

from db import Model, Table
from cmd import Command

class const:
    root_dir            = Path(sys.argv[0]).resolve().parents[1]
    #archive_dir         = root_dir.parent / 'cc-address' / 'archive'
    archive_dir         = root_dir / 'data' / 'cc-address-import'
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
    logging.basicConfig(filename='import.log',level=logging.DEBUG)

    revisions = Revisions()
    
    person_cmd_creator = TableCommandCreator(
        file_name=const.persons_filename,
        table_name='persons', 
        key_col_names=['Lastname', 'Firstname', 'Keywords'],
        show_col_names=['Lastname', 'Firstname'],
    )
        
    company_cmd_creator = TableCommandCreator(
        file_name=const.companies_filename,
        table_name='companies', 
        key_col_names=['Name', 'Keywords'],
        show_col_names=['Name'],
    )
    
    # persons_key = ('Lastname', 'Firstname', 'Keywords')
    # persons_table_name = 'persons'
    # prev_persons = CvsData(persons_table_name, persons_key)
    
    table_created = False
    for zip_path in const.zip_pathes:
        with ZipFile(str(zip_path)) as data_zip:
            logging.info('{}:'.format(zip_path))
            
            zip_mtime    = zip_path.stat().st_mtime
            zip_datetime = datetime.datetime.fromtimestamp(zip_mtime)
            
            cmd_list = []
            if not table_created:
                cmd_list += [Command('crate table', 'persons'), Command('crate table', 'companies')]
                table_created = True
                
            for cmd_creator in [person_cmd_creator, company_cmd_creator]:
            #for cmd_creator in [company_cmd_creator]:
                fh = data_zip.open(cmd_creator.file_name)
                cmd_list += cmd_creator.create_commands(fh)

            # persons_file = data_zip.open(const.persons_filename)
            # persons = CvsData(persons_table_name, persons_key)
            # persons.read(persons_file)
            
            # cols_comparer = ColumnsComparer(prev_persons.cols_name, persons.cols_name)
            # cols_diff = cols_comparer.compare()
            # #logging.debug(cols_diff)
            # cmd_list += cols_diff.create_cmd_list(persons_table_name)

            # persons.init_id2rows(prev_persons, cols_diff.mapping)
            
            # rows_id_diff = RowsIdDiff(prev_persons, persons)
            # cmd_list += rows_id_diff.create_cmd_list(persons_table_name)
            
            # PrintChangedRows(prev_persons, persons, rows_id_diff)
            
            # for row_id in rows_id_diff.common_id_list:
                # row1 = prev_persons.get_row(row_id)
                # row2 = persons.get_row(row_id)
                # rows_comparer = RowsComparer(row1, row2, cols_diff)
                # rows_diff = rows_comparer.compare()
                # #logging.debug(rows_diff)
                # cmd_list += rows_diff.create_cmd_list(persons_table_name)

            # for row_id in rows_id_diff.added_id_list:
                # row2 = persons.get_row(row_id)
                # cmd_list += row2.create_cmd_list(persons_table_name)
                
            revisions.append(
                Revision(zip_datetime, cmd_list))
                
            # prev_persons = persons
                
    out_path = const.out_dir / const.json_filename
    out_path.open('w').write(revisions.create_json_string())
            
#-------------------------------------------------------------------------------

class TableCommandCreator:
    def __init__(self, file_name, table_name, key_col_names, show_col_names):
        self.file_name = file_name
        self.table_name = table_name
        self.key_col_names = key_col_names
        self.show_col_names = show_col_names
        self.prev_data = CvsData(table_name, key_col_names)
        
    def create_commands(self, fh):
        cmd_list = []
        cvs_data = CvsData(self.table_name, self.key_col_names)
        cvs_data.read(fh)
        
        cols_comparer = ColumnsComparer(self.prev_data.cols_name, cvs_data.cols_name)
        cols_diff = cols_comparer.compare()
        #logging.debug(cols_diff)
        cmd_list += cols_diff.create_cmd_list(self.table_name)

        cvs_data.init_id2rows(self.prev_data, cols_diff.mapping)
        
        rows_id_diff = RowsIdDiff(self.prev_data, cvs_data)
        cmd_list += rows_id_diff.create_cmd_list(self.table_name)
        
        self._LogChangedRows(cvs_data, rows_id_diff)
        
        for row_id in rows_id_diff.common_id_list:
            row1 = self.prev_data.get_row(row_id)
            row2 = cvs_data.get_row(row_id)
            rows_comparer = RowsComparer(row1, row2, cols_diff)
            rows_diff = rows_comparer.compare()
            # logging.debug(rows_diff)
            cmd_list += rows_diff.create_cmd_list(self.table_name)

        for row_id in rows_id_diff.added_id_list:
            row2 = cvs_data.get_row(row_id)
            cmd_list += row2.create_cmd_list(self.table_name)
            
        self.prev_data = cvs_data
        return cmd_list

    def _LogChangedRows(self, cur_cvs_data, rows_id_diff):
        remove_rows = ['- ' + self._RowString(self.prev_data.get_row(row_id).data)
                       for row_id in rows_id_diff.removed_id_list]
                       
        added_rows  = ['+ ' + self._RowString(cur_cvs_data.get_row(row_id).data)
                       for row_id in rows_id_diff.added_id_list]
                         
        common_rows = ['== ' + self._RowString(cur_cvs_data.get_row(row_id).data)
                       for row_id in rows_id_diff.common_id_list]
                       
        for line in sorted(remove_rows + added_rows, key=lambda x: x[2:] + x[0]):
            logging.debug('  {}'.format(line))
    #    for line in sorted(common_rows):
    #        logging.debug('  {}'.format(line))

    def _RowString(self, row_data):
        return ' '.join([str(row_data[x]) for x in self.show_col_names])
        
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
        text_wrapper = io.TextIOWrapper(fh, encoding='Windows-1252') # nicht latin-1, wegen €-Zeichen
        reader = csv.DictReader(text_wrapper, delimiter=const.entry_sep, skipinitialspace=True)
        self.cols_name = reader.fieldnames
        self.rows_data = list(reader)
            
        self._init_key2row()

    def _init_key2row(self):
        self._key2row = {}
        for i in range(len(self.rows_data)):
            row = Row(self, i)
            key = tuple(row.data[x] for x in self._key_col_names)
            if key in self._key2row:
                raise Exception(key)
            self._key2row[key] = row

    def init_id2rows(self, other, col_mapping):
        self._id2row = {}
        self._transfer_ids(other, col_mapping)
        self._fill_up_ids(other._next_id)
    
    def _transfer_ids(self, other, col_mapping):
        rows_key_mapper = RowsKeyMapper(other._key2row, self._key2row, col_mapping)
        rows_key_map = rows_key_mapper.map()
        
        for other_key, self_key in rows_key_map.items():
            self_row  = self._key2row[self_key]
            other_row = other._key2row[other_key]
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
        
    def __str__(self):
        items = ['{}: {}'.format(x, self._row_data[x]) for x in self._cvs_data.cols_name if len(self._row_data[x]) > 0]
        return '{' + ', '.join(items) + '}'
        
    def __repr__(self):
        return str(self)
        
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
        return [Command('add row', table_name, self.id, *[self._row_data[x] for x in self._cvs_data.cols_name])]
        
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
        cmd_list  = [Command('remove col', table_name, x)        for x      in self.removed_col_names]
        cmd_list += [Command('add col',    table_name, x, 'str') for x      in self.added_col_names]
        cmd_list += [Command('rename col', table_name, x1, x2)   for x1, x2 in self.mapping.items() if x1 != x2]
        return cmd_list
        
#---------------------------------------------------------------------------

class RowsKeyMapper:
    def __init__(self, key2row1:'{str:Row}', key2row2:'{str:Row}', cols_mapping):
        assert isinstance(key2row1, dict)
        assert isinstance(key2row2, dict)
        assert isinstance(cols_mapping, dict)
        self.key2row1 = key2row1
        self.key2row2 = key2row2
        self.cols_mapping = cols_mapping
        
    def map(self):
        keys1 = set(self.key2row1.keys())
        keys2 = set(self.key2row2.keys())
        
        key_mapping = {x: x for x in keys1 & keys2}
        
        removed_key_set = keys1 - keys2
        added_key_set   = keys2 - keys1
        ratio_counter = self._create_ratio_counter(removed_key_set, added_key_set)
        
        for (key1, key2), ratio in ratio_counter.most_common():
            if ratio >= 2.5 and key1 in removed_key_set and key2 in added_key_set:
                row1 = self.key2row1[key1]
                row2 = self.key2row2[key2]
                
                logging.debug('  ratio={}'.format(ratio))
                logging.debug('    {}'.format(row1))
                logging.debug('    {}'.format(row2))
                
                key_mapping[key1] = key2
                removed_key_set.remove(key1)
                added_key_set.remove(key2)
                
        return key_mapping
            
    def _create_ratio_counter(self, removed_key_set, added_key_set):
        ratio_counter = Counter()
        for key1 in removed_key_set:
            for key2 in added_key_set:
                row1 = self.key2row1[key1]
                row2 = self.key2row2[key2]
                ratio = self._calc_row_ratio(row1, row2)
                ratio_counter[(key1, key2)] = ratio
        return ratio_counter
        
    def _calc_row_ratio(self, row1, row2):
        # if not self._are_firstname_equal(row1, row2):
            # return 0.0
        
        n_sum = 0
        ratio_sum = 0.0
        
        for col_name1, col_name2 in self.cols_mapping.items():
            val1 = row1.data[col_name1]
            val2 = row2.data[col_name2]
            n = len(val1)  # Länge des alten Wertes! (möglich wäre auch der des Kürzeren)
            n_sum += n
            ratio = self._calc_val_ratio(val1, val2)
            ratio_sum += n * ratio
        return ratio_sum / (n_sum ** 0.5)  # noch unklar, sollte irgendwo zwischen ratio_sum/n_sum und ratio_sum liegen
        
    # def _are_firstname_equal(self, row1, row2):
        # firstname1 = row1.data['Firstname'].lower()
        # firstname2 = row2.data['Firstname'].lower()
        # n = min(len(firstname1), len(firstname2))
        # return firstname1[:n] == firstname2[:n]
            
    def _calc_val_ratio(self, val1, val2):
        matcher = SequenceMatcher(a=val1, b=val2)
        return matcher.ratio()
        
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
        #cmd_list += [Command('add row',    table_name, x) for x in self.added_id_list]
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
        assert row1.id == row2.id
        self.row_id = row1.id
        self.row1 = row1
        self.row2 = row2
        self.diff_list = []
        
    def add(self, col_name2, value2):
        self.diff_list.append(
            RowDiff(self.row_id, col_name2, value2))
        
    def create_cmd_list(self, table_name) -> '[Command]':
        return [x.create_cmd(table_name) for x in self.diff_list]
    
#---------------------------------------------------------------------------

class RowDiff:
    def __init__(self, row_id, col_name, value):
        self.row_id   = row_id
        self.col_name = col_name
        self.value    = value
        
    def create_cmd(self, table_name) -> 'Command':
        return Command('set value', table_name, self.row_id, self.col_name, self.value)
        
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
