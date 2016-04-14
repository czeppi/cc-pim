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

#------------------------------------------------------------------------------

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
    
class Keywords:
    pass

#------------------------------------------------------------------------------

class Revision:
    # serial, timestamp, comment
    pass
    
#------------------------------------------------------------------------------

class Event:
    # id, text
    pass

#------------------------------------------------------------------------------

class Timepoint:
    # id, year, month, day, event-id
    pass
    
#------------------------------------------------------------------------------
    
class Relation:
    # object, predicat, subject, t_begin, t_end, comment, revison_serial
    pass

#------------------------------------------------------------------------------

class SearchParameter:

    def __init__(self, text, upper_lower_sensitive=False, whole_word=False, regex=False):
        self.text = text
        self.upper_lower_sensitive = upper_lower_sensitive
        self.whole_word = whole_word
        self.regex = regex
