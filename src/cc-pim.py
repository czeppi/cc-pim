# Copyright (C) 2014  Christian Czepluch
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

import sys
import traceback
from pathlib import Path

from context import Context, SystemResourceMgr, UserResourceMgr, GUI

if GUI == 'wx':
    import wx
    import wxgui.mainframe
elif GUI == 'pyside2':
    from PySide2.QtCore import *
    from PySide2.QtGui import *
    from PySide2.QtWidgets import *
    from pysidegui.mainwindow import MainWindow
    

def main():
    if len(sys.argv) != 2:
        raise Exception('usage: cc-pim.py <user-data-dir>')

    start_dir = Path(sys.argv[0]).resolve().parent
    root_dir = start_dir.parent
    etc_dir = root_dir / 'etc'
    user_dir = Path(sys.argv[1])
    if not user_dir.exists():
        raise Exception(f'user data dir "{user_dir}" does not exists.')

    context = Context(
        system=SystemResourceMgr(etc_dir),
        user=UserResourceMgr(user_dir))

    if GUI == 'wx':
        start_wx_app(context)
    elif GUI == 'pyside2':
        start_pyside_app(context)


def start_wx_app(context: Context):
    app = wx.App()
    try:
        frame = wxgui.mainframe.MainFrame(context)
        frame.Show()
    except Exception as _e:
        wx.MessageBox(traceback.format_exc(), "Exception")
        
    app.MainLoop()
    

def start_pyside_app(context: Context):
    app = QApplication()
    frame = MainWindow(context)
    frame.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
