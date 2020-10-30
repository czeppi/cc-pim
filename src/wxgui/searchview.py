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

import wx

        
class SearchView(wx.Panel):

    def __init__(self, parent, context):
        self._context = context
        wx.Panel.__init__(self, parent, style=wx.BORDER_SUNKEN)
        self._init_controls()

        margin = (context.config.margin, context.config.margin)
        input_sizer = wx.BoxSizer(wx.HORIZONTAL)
        input_sizer.Add(margin)
        input_sizer.Add(self._search_bitmap,     0, wx.EXPAND)
        input_sizer.Add(margin)
        input_sizer.Add(self._search_edit_ctrl,  1, wx.EXPAND)
        input_sizer.Add(self._search_type_combo, 0, wx.EXPAND)
        
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(input_sizer,            0, wx.EXPAND)
        main_sizer.Add(self._result_list_ctrl, 1, wx.EXPAND)
        self.SetSizer(main_sizer)

    def _init_controls(self):
        self._search_bitmap     = self._create_search_bitmap()
        self._search_edit_ctrl  = self._create_search_edit_ctrl()
        self._search_type_combo = self._create_search_type_combo()
        self._result_list_ctrl  = self._create_result_list_ctrl()
        
    def _create_search_bitmap(self):
        bmp = wx.Bitmap(str(self._context.system.icon_dir / 'search.ico'), wx.BITMAP_TYPE_ICO)
        return wx.StaticBitmap(self, -1, bmp)
    
    def _create_search_edit_ctrl(self):
        search_edit_ctrl = wx.TextCtrl(self, size=(200,-1), style=wx.TE_PROCESS_ENTER)
        search_edit_ctrl.Bind(wx.EVT_TEXT_ENTER, self.on_search_text_enter)
        return search_edit_ctrl
        
    def _create_search_type_combo(self):
        search_type_combo = wx.ComboBox(self, -1, choices=[],
                                        style=wx.CB_READONLY)
        search_type_combo.Bind(wx.EVT_COMBOBOX, self.on_search_type_combo)
        return search_type_combo
        
    def _create_result_list_ctrl(self):
        return wx.ListCtrl(self)
        
    def on_search_text_enter(self, event):
        pass
        
    def on_search_type_combo(self, event):
        pass