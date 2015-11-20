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

#------------------------------------------------------------------------------

class Context:

    def __init__(self, root_dir):
        self._root_dir = root_dir
        self._config = Config()
        
    @property
    def config(self):
        return self._config
    
    # def read_icon(self, icon_name):
        # icon_dir = self._get_icon_dir()
        # path = os.path.join(icon_dir, icon_name)
        # return wx.Icon(path, wx.BITMAP_TYPE_ICO)

    # def read_bitmap(self, bmp_name):
        # icon_dir = self._get_icon_dir()
        # path = os.path.join(icon_dir, bmp_name)
        # return wx.Bitmap(path)
        
    @property
    def icon_dir(self):
        return self._root_dir / 'etc' / 'icons'
    
#------------------------------------------------------------------------------

class Config:
    
    @property
    def app_title(self):
        return 'CC-PIM'
        
    @property
    def frame_pos(self):
        return (0,0)
        
    @property
    def frame_size(self):
        return (1200, 800)
     
    @property
    def search_width(self):
        return 400
        
    @property
    def margin(self):
        return 5
     