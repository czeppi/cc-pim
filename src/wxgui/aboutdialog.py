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
# Programm erhalten haben. Wenn nicht, siehe <http://www.gnu.org/licenses/>.

import wx


class AboutDialog(wx.Dialog):

    def __init__(self, parent):
        pos = parent.GetPosition() + (50, 50)
        wx.Dialog.__init__(self, parent, -1, "???", pos=pos, 
            style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
        
        # panel
        self.panel = wx.Panel(self)
            
        # hsizer1
        hsizer1 = wx.BoxSizer(wx.HORIZONTAL)
        hsizer1.Add((10, 0))
        hsizer1.Add(self.panel, 1, wx.EXPAND)
        hsizer1.Add((10, 0))
        
        # buttons
        ok_button     = wx.Button(self, wx.ID_OK,     'OK')
        cancel_button = wx.Button(self, wx.ID_CANCEL, 'Cancel')
        
        # hsizer2
        hsizer2 = wx.BoxSizer(wx.HORIZONTAL)
        hsizer2.Add((10, 0), 1)
        hsizer2.Add(ok_button)
        hsizer2.Add((10, 0))
        hsizer2.Add(cancel_button)
        hsizer2.Add((10, 0), 1)
        
        # vsizer
        vsizer = wx.BoxSizer(wx.VERTICAL)
        vsizer.Add((0,5))
        vsizer.Add(hsizer1, 1, wx.EXPAND)
        vsizer.Add((0,10))
        vsizer.Add(hsizer2, 0, wx.EXPAND)
        vsizer.Add((0,10))
        
        self.SetSizer(vsizer)
        self.Fit()
        
