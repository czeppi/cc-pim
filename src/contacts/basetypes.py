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
import re
import datetime
from re import Match
from typing import Tuple, Optional


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

    dialog_rex = r"(((~)?(01|02|03|04|05|06|07|08|09|10|11|12|13|14|15|16|17|18|19|20|" \
                 r"21|22|23|24|25|26|27|28|29|30|31)(\?)?\.)?" \
                 r"(~)?(01|02|03|04|05|06|07|08|09|10|11|12)(\?)?\.)?(~)?((19|20)[0-9]{2})(\?)?"
    rex_text = r"(((?P<tilde_day>~)?(?P<day>[0-9]{2})(?P<day_unsure>\?)?\.)?" \
               r"(?P<tilde_month>~)?(?P<month>[0-9]{2})(?P<month_unsure>\?)?\.)?" \
               r"(?P<tilde_year>~)?(?P<year>[0-9]{4})(?P<year_unsure>\?)?"
    rex = re.compile(rex_text + "$")

    def __init__(self, date_as_string: str, serial: int = 0):
        self.serial = serial
        
        m = self.rex.match(date_as_string)
        if not m:
            if re.compile(self.dialog_rex):
                raise ValueError('too short')
            else:
                raise ValueError("don't match regular expression")

        self.day,   self.is_day_exact,   self.is_day_sure   = self._get_value_exact_and_sure(m, 'day')
        self.month, self.is_month_exact, self.is_month_sure = self._get_value_exact_and_sure(m, 'month')
        self.year,  self.is_year_exact,  self.is_year_sure  = self._get_value_exact_and_sure(m, 'year')

        self._check_date()

    @staticmethod
    def _get_value_exact_and_sure(m: Match, part_name: str) -> Tuple[Optional[int], Optional[bool], Optional[bool]]:
        val_str = m.group(part_name)
        if val_str:
            return int(val_str), (m.group('tilde_' + part_name) != '~'), (m.group(part_name + '_unsure') != '?')
        else:
            return None, None, None

    def _check_date(self) -> None:
        day = self.day
        if day is None:
            day = 1
        month = self.month
        if month is None:
            month = 1
        datetime.date(self.year, month, day)  # raise a ValueError, if invalid

    def _check_invariant(self) -> None:
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
            s += f'{self.day:02}.'
            if not self.is_day_sure:
                s += '?'
        if self.month:
            if not self.is_month_exact:
                s += '~'
            s += f'{self.month:02}.'
            if not self.is_month_sure:
                s += '?'
        if not self.is_year_exact:
            s += '~'
        s += f'{self.year:04}'
        if not self.is_year_sure:
            s += '?'
        return s
    

class SearchParameter:

    def __init__(self, text: str, upper_lower_sensitive: bool = False, whole_word: bool = False, regex: bool = False):
        self.text = text
        self.upper_lower_sensitive = upper_lower_sensitive
        self.whole_word = whole_word
        self.regex = regex


class Fact:

    def __init__(self, serial: int, predicate_serial: int, subject_serial: int, value: Optional[str],
                 note: Optional[str] = None,
                 date_begin_serial: Optional[int] = None,
                 date_end_serial: Optional[int] = None,
                 is_valid: bool = True):
        self.serial = serial
        self.predicate_serial = predicate_serial
        self.subject_serial = subject_serial
        self.value = value
        self.note = note
        self.date_begin_serial = date_begin_serial
        self.date_end_serial = date_end_serial
        self.is_valid = is_valid

    def copy(self) -> Fact:
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
