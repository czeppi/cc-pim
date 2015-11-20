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

import wx

class config:
    app_title = 'CC-PIM'
    frame_pos = (0,0)
    frame_size = (800, 600)


#------------------------------------------------------------------------------
        
class Frame(wx.Frame):

    def __init__(self, start_fpath):
        self._start_fpath = start_fpath
        wx.Frame.__init__(self, None, -1, config.app_title, 
            config.frame_pos, config.frame_size)
        self._create_simple_win()

    def _create_simple_win(self):
        text_ctrl = wx.TextCtrl(self, value="bla", style=wx.TE_MULTILINE)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(text_ctrl, 1, wx.EXPAND)
        self.SetSizer(sizer)
        
