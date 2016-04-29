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

import re


class Name:
    pass


class Date:
    pass


class EMail:
    pass


class PhoneNumber:
    pass


class Url:
    pass


class Str:
    pass


class Text:
    pass


class Keywords:
    pass

    
class Ref:

    def __init__(self, target_class, target_attributename):
        self.target_class = target_class
        self.target_attributename = target_attributename
        

class VagueDate:  # oder InexactDate, InaccurateDate, ImproperDate
    
    rex = re.compile(r"(((?P<tilde_day>~)?(?P<day>[0-9]{2})\.)?(?P<tilde_month>~)?(?P<month>[0-9]{2})\.)?(?P<tilde_year>~)?(?P<year>[0-9]{4})$")
    
    def __init__(self, date_as_string, serial=0):
        self.serial = serial
        
        m = self.rex.match(date_as_string)
        assert m

        self.day,   self.is_day_exact   = self._get_value_and_is_exact(m, 'day')
        self.month, self.is_month_exact = self._get_value_and_is_exact(m, 'month')
        self.year,  self.is_year_exact  = self._get_value_and_is_exact(m, 'year')
            
    def _get_value_and_is_exact(self, m, part_name):
        val_str = m.group(part_name)
        if val_str:
            return int(val_str), (m.group('tilde_' + part_name) != '~')
        else:
            return None, None

    def _check_invariant(self):
        d, m, y = self.day, self.month, self.year
        
        assert d is None or isinstance(d, int)
        assert m is None or isinstance(m, int)
        assert isinstance(y, int)
        
        if d is None:
            assert self.is_day_exact is None
        else:
            assert isinstance(self.is_day_exact, bool)
            
        if m is None:
            assert self.is_month_exact is None
            assert d is None
        else:
            assert isinstance(self.is_month_exact, bool)
            
        assert isinstance(self.is_year_exact, bool)
        
        assert 1 <= d <= 31
        assert 1 <= m <= 12
        assert 1900 <= y <= 2100
            
    def __str__(self):
        s = ''
        if self.day:
            if not self.is_day_exact:
                s += '~'
            s += '{:02}.'.format(self.day)
        if self.month:
            if not self.is_month_exact:
                s += '~'
            s += '{:02}.'.format(self.month)
        if not self.is_year_exact:
            s += '~'
        s += '{:04}'.format(self.year)
        return s
    

class SearchParameter:

    def __init__(self, text, upper_lower_sensitive=False, whole_word=False, regex=False):
        self.text = text
        self.upper_lower_sensitive = upper_lower_sensitive
        self.whole_word = whole_word
        self.regex = regex


class Fact:

    def __init__(self, serial, predicate_serial, subject_serial, value,
                 note=None, date_begin_serial=None, date_end_serial=None, is_valid=True):
        self.serial = serial
        self.predicate_serial = predicate_serial
        self.subject_serial = subject_serial
        self.value = value
        self.note = note
        self.date_begin_serial = date_begin_serial
        self.date_end_serial = date_end_serial
        self.is_valid = is_valid

    def copy(self):
        return Fact(
            serial=self.serial,
            predicate_serial=self.predicate_serial,
            subject_serial=self.subject_serial,
            value=self.value,
            note=self.note,
            date_begin_serial=self.date_begin_serial,
            date_end_serial=self.date_end_serial,
            is_valid=self.is_valid
        )
