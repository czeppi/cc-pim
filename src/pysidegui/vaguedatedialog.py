#! /usr/bin/env python
#-*- coding: utf-8 -*-

# Copyright (C) 2016  Christian Czepluch
#
# This file is part of CC-Notes.
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

from PySide.QtGui import QDialog, QLineEdit, QRegExpValidator
from PySide.QtCore import QRegExp
from pysidegui._ui_.ui_vaguedatedialog import Ui_VagueDateDialog
from modeling.basetypes import VagueDate


class VagueDateDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.ui = Ui_VagueDateDialog()
        self.ui.setupUi(self)
        
        self._init_title()
        self._init_date_edit()
        
    def _init_title(self):
        self.setWindowTitle("New Vague Date")
                
    def _init_date_edit(self):
        rex = QRegExp(VagueDate.dialog_rex)
        validator = QRegExpValidator(rex) #, 0)
        self.ui.lineEdit.setValidator(validator)

        #self.ui.lineEdit.setText('')
        #self.ui.lineEdit.setReadOnly(True)
    
    @property
    def text(self):
        return self.ui.lineEdit.text()