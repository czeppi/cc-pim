#! /usr/bin/env python
#-*- coding: utf-8 -*-

# Copyright (C) 2014  Christian Czepluch
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

class Context:
    blog_pathname = "g:/cc/Blogs/BTC.txt"
    blog_dir = "g:/cc/Blogs"
    blog_names = [
        "BTC",
        "Info",
        "Produkte",
        "Programme",
        "Programmierung",
    ]
    metamodel_pathname = '../etc/notes.ini'
    sqlite3_pathname = '../etc/notes.sqlite3'
    no_keywords_pathname = '../etc/no-keywords.txt'
    template_pathname = '../etc/template.txt'    
    user_css_pathname = '../etc/user.css'    
    logging_enabled = False
    out_dir = '../out'