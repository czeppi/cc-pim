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
   
GUI = 'wx'
   
import sys
import traceback
if GUI == 'wx':
    import wx
    import wxgui.frame
elif GUI == 'pyside':
    from PySide.QtCore import *
    from PySide.QtGui import *
    from pysidegui.mainwindow import MainWindow
 
#-------------------------------------------------------------------------------

def main():
    if GUI == 'wx':
        start_wx_app()
    elif GUI == 'pyside':
        start_pyside_app()

#-------------------------------------------------------------------------------

def start_wx_app():
    start_fpath = None
    if len(sys.argv) > 1:
        start_fpath = sys.argv[1]

    app = wx.App()
        
    try:
        frame = wxgui.frame.Frame(start_fpath)
        frame.Show()
    except Exception as _e:
        wx.MessageBox(traceback.format_exc(), "Exception")
        
    app.MainLoop()
    
#-------------------------------------------------------------------------------

def start_pyside_app():
    app = QApplication(sys.argv)
    frame = MainWindow()
    frame.show()
    sys.exit(app.exec_())

#-------------------------------------------------------------------------------

if __name__ == '__main__':
    main()
