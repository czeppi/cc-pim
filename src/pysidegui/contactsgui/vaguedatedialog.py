# Copyright (C) 2016  Christian Czepluch
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

from PySide2.QtCore import QRegExp
from PySide2.QtGui import QRegExpValidator
from PySide2.QtWidgets import QDialog, QWidget

from contacts.basetypes import VagueDate
from pysidegui._ui2_.ui_vaguedatedialog import Ui_VagueDateDialog


class VagueDateDialog(QDialog):
    def __init__(self, parent: QWidget, vague_date: VagueDate):
        super().__init__(parent)
        self.ui = Ui_VagueDateDialog()
        self.ui.setupUi(self)
        self._vague_date = vague_date
        
        self._init_title()
        self._init_date_edit()
        
    def _init_title(self) -> None:
        if self._vague_date is None:
            self.setWindowTitle('New Vague Date')
        else:
            self.setWindowTitle(f'Edit Vague Date #{self._vague_date.serial}')
                
    def _init_date_edit(self) -> None:
        if self._vague_date is not None:
            self.ui.lineEdit.setText(str(self._vague_date))
        rex = QRegExp(VagueDate.dialog_rex)
        validator = QRegExpValidator(rex)
        self.ui.lineEdit.setValidator(validator)

        # self.ui.lineEdit.setText('')
        # self.ui.lineEdit.setReadOnly(True)
    
    @property
    def text(self):
        return self.ui.lineEdit.text()
