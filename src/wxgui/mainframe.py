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

from wxgui.aboutdialog import AboutDialog
from wxgui.searchview import SearchView
from wxgui.notebook import Notebook

#------------------------------------------------------------------------------
        
class MainFrame(wx.Frame):

    def __init__(self, context):
        self._context = context
        cfg = context.config
        wx.Frame.__init__(self, None, -1, cfg.app_title, cfg.frame_pos, cfg.frame_size)
        icon = wx.Icon( str(self._context.icon_dir / 'info.ico'), wx.BITMAP_TYPE_ICO)
        self.SetIcon(icon)
        self._create_menubar()
        self._create_toolbar()
        self._create_splitter_window()
        self._create_statusbar()

    def _create_menubar(self):
        self._menubar = wx.MenuBar()
        
        # helpmenu
        menu = wx.Menu()
        self._add_menuitem(menu, 'About', '', self.on_menu_help_about)
        self._menubar.Append(menu, 'Help')
        
        self.SetMenuBar(self._menubar)
        
    def _add_menuitem(self, menu, text, description, handler):
        new_id = wx.NewId()
        menu.Append(new_id, text, description)
        self.Bind(wx.EVT_MENU, handler, id=new_id)
        return new_id
        
    def _create_toolbar(self):
        toolbar = wx.Frame.CreateToolBar(self)
        self._add_toolitem(toolbar, "info.ico", self.on_menu_help_about, tooltip='')
        toolbar.Realize()

    def _add_toolitem(self, toolbar, icon_name, handler, tooltip=""):
        new_id = wx.NewId()
        bmp = wx.Bitmap(str(self._context.icon_dir / 'info.ico'), wx.BITMAP_TYPE_ICO)
        toolbar.AddTool(new_id, '', bmp, shortHelp=tooltip)        
        self.Bind(wx.EVT_TOOL, handler, id=new_id)
        return new_id
        
    def _create_splitter_window(self):
        self._splitter  = wx.SplitterWindow (self, -1, style=wx.SP_LIVE_UPDATE)
        self._search_view  = SearchView(self._splitter, self._context)
        self._notebook_win = Notebook(self._splitter, self._context)
        
        self._splitter.SplitVertically (self._search_view, self._notebook_win, self._context.config.search_width)
        
    def _create_statusbar(self):
        bar = wx.Frame.CreateStatusBar(self, 2)
        self.GetStatusBar().SetStatusWidths([-1, 50])
        
    def on_menu_help_about(self, event):
        dlg = AboutDialog(self)
        if dlg.ShowModal() == wx.ID_OK:
            # wx.MessageBox('OK', 'on_menu_help_About')
            pass
        
        