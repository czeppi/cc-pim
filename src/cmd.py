##########################################
## CC-PIM                               ##
## Copyright 2013 by Christian Czepluch ##
##########################################

from collections import OrderedDict
import datetime

#-------------------------------------------------------------------------------

class Command:
    def __init__(self, cmd_name:str, *parameters):
        assert isinstance(cmd_name, str)
        #print ('{}, {}'.format(cmd_name, parameters))
        
        self._cmd_name = cmd_name
        self._parameters = list(parameters)
        
    def create_json_list(self):
        return [self._cmd_name] + self._parameters
        
    def apply(self, model):
        cmd_name = self._cmd_name
        if cmd_name == 'add table':
            self._add_table(model)
        elif cmd_name == 'remove table':
            self._remove_table(model)
        elif cmd_name == 'rename table':
            self._rename_table(model)
        elif cmd_name == 'add col':
            self._add_col(model)
        elif cmd_name == 'remove col':
            self._remove_col(model)
        elif cmd_name == 'add row':
            self._add_row(model)
        elif cmd_name == 'set value':
            self._set_value(model)
        else:
            raise Exception(cmd_name)
            
    def _add_table(self, model):
        parameters = self._parameters
        if len(parameters) != 1:
            raise Exception('{} {}'.format(cmd_name, parameters))
        model.add_table(*parameters)
        
    def _remove_table(self, model):
        if len(parameters) != 1:
            raise Exception('{} {}'.format(cmd_name, parameters))
        model.remove_table(*parameters)
        
    def _rename_table(self, model):
        if len(parameters) != 2:
            raise Exception('{} {}'.format(cmd_name, parameters))
        model.rename_table(*parameters)
        
    def _add_col(self, model):
        if len(parameters) != 2:
            raise Exception('{} {}'.format(cmd_name, parameters))
        col_path = parameters[0]
        col_type = self._parse_col_type(parameters[1])
        table_name, col_name = self._split_col_path(col_path)
        table = self._get_table(table_name)
        table.add_col(col_name, col_type)
            
    def _remove_col(self, model):
        if len(parameters) != 1:
            raise Exception('{} {}'.format(cmd_name, parameters))
        col_path = parameters[0]
        table_name, col_name = self._split_col_path(col_path)
        table = self._get_table(table_name)
        table.remove_col(col_name)
            
    def _add_row(self, model):
        if len(parameters) < 2:
            raise Exception('{} {}'.format(cmd_name, parameters))
        row_path = parameters[0]
        table_name, row_id = self._split_row_path(row_path)
        table = self._get_table(table_name)
        table.add_row(row_id, *parameters[1:])
            
    def _set_value(self, model):
        if len(parameters) != 2:
            raise Exception('{} {}'.format(cmd_name, parameters))
        cell_path, new_value = parameters
        table_name, row_id, col_name = self._split_cell_path(cell_path)
        table = self._get_table(table_name)
        table.set_value(row_id, col_name, new_value)
            
    def _split_col_path(self, col_path):
        items = col_path.split('.')
        if len(items) != 2:
            raise Exception(col_path)
        table_name, col_name = items
        return table_name, col_name
        
    def _split_row_path(self, row_path):
        items = row_path.split('.')
        if len(items) != 2:
            raise Exception(row_path)
        table_name, row_id_str = items
        return table_name, int(row_id_str)
        
    def _split_cell_path(self, cell_path):
        items = col_path.split('.')
        if len(items) != 3:
            raise Exception(col_path)
        table_name, row_id_str, col_name = items
        return table_name, col_name, int(row_id_str)
        
    def _parse_col_type(self, col_type_str):
        raise Exception('not yet implemented')
        
    def _get_table(self, model, table_name):
        table = model.find_table(table_name)
        if table is None:
            raise Exception(cell_path)
        return table

