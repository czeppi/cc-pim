#! /usr/bin/env python3
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
   
GUI = 'pyside'
   
import sys
import os.path
import traceback
from pathlib import Path

if GUI == 'wx':
    import wx
    import wxgui.mainframe
elif GUI == 'pyside':
    from PySide.QtCore import *
    from PySide.QtGui import *
    from pysidegui.mainwindow import MainWindow
    
from context import Context
 
#-------------------------------------------------------------------------------

def main():
    root_dir = None
    if len(sys.argv) > 0:
        start_dir = Path(sys.argv[0]).resolve().parent
        root_dir = start_dir.parent

    context = Context(root_dir)
    
    if GUI == 'wx':
        start_wx_app(context)
    elif GUI == 'pyside':
        start_pyside_app(context)

#-------------------------------------------------------------------------------

def start_wx_app(context):
    app = wx.App()
        
    try:
        frame = wxgui.mainframe.MainFrame(context)
        frame.Show()
    except Exception as _e:
        wx.MessageBox(traceback.format_exc(), "Exception")
        
    app.MainLoop()
    
#-------------------------------------------------------------------------------

def start_pyside_app(context):
    app = QApplication(sys.argv)
    frame = MainWindow(context)
    frame.show()
    sys.exit(app.exec_())

#-------------------------------------------------------------------------------

if __name__ == '__main__':
    main()
