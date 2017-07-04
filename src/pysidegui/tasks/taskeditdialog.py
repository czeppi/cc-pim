#! /usr/bin/env python
#-*- coding: utf-8 -*-

# Copyright (C) 2013  Christian Czepluch
#
# This file is part of CC-PIM
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

from PySide.QtGui import QDialog
from PySide.QtGui import QApplication
from PySide.QtCore import Qt
from gui._ui_.ui_noteeditdialog import Ui_NoteEditDialog

from modeling.notesmodel import NoteRevision


class NoteEditDialog(QDialog):

    def __init__(self, parent, note, notes_model):
        super(NoteEditDialog, self).__init__(parent, f=Qt.WindowMaximizeButtonHint)
        self.ui = Ui_NoteEditDialog()
        self.ui.setupUi(self)
        
        self._note = note
        self._notes_model = notes_model
        self._init_title()
        self._init_splitter()
        self._init_id_edit()
        self._init_cat_combo()
        self._init_title_text()
        self._init_text_edit()
        self._init_preview()
        
        self._preview_updater = FastPreviewUpdater(self)
        self.showMaximized()
        
    def _init_title(self):
        title = "New Note" if self._note.is_empty() else "Edit Note"
        self.setWindowTitle(
            QApplication.translate(
                "NoteEditDialog", title, None, QApplication.UnicodeUTF8))
                
    def _init_splitter(self):
        self.ui.splitter.setStretchFactor(0, 2)
        self.ui.splitter.setStretchFactor(1, 3)
    
    def _init_id_edit(self):
        note = self._note
        self.ui.id_edit.setText(note.id)
        self.ui.id_edit.setReadOnly(True)
    
    def _init_cat_combo(self):
        note = self._note
        sorted_categories = self._notes_model.get_sorted_categories()
        self.ui.cat_combo.addItems(sorted_categories)
        
        cat_str = note.last_revision.category
        self.ui.cat_combo.setEditText(cat_str)
        
    def _init_title_text(self):
        note = self._note
        self.ui.title_edit.setText(note.last_revision.title)
        
        keywords = self._notes_model.calc_keywords()
        self.ui.title_edit.init_completer(keywords)
    
    def _init_text_edit(self):
        note = self._note
        char_format = self.ui.body_edit.currentCharFormat()
        char_format.setFontFixedPitch(True)  # geht nicht
        char_format.setFontFamily('New Courier')
        self.ui.body_edit.setCurrentCharFormat(char_format)
        self.ui.body_edit.setAcceptRichText(False)
        self.ui.body_edit.setText(note.last_revision.body)
    
    def _init_preview(self):
        note = self._note
        self.ui.preview.setText(note.last_revision.get_html_text())
        self.ui.preview.setReadOnly(True)
    
    def _update_preview(self):
        note = self._note
        values = note.last_revision.get_values()
        values.update(self.get_values())
        tmp_note_rev = NoteRevision(**values)
        html_text = tmp_note_rev.get_html_text()
        self.ui.preview.setText(html_text)
        
    def get_values(self):
        return {
            'title':    self.ui.title_edit.text(),
            'body':     self.ui.body_edit.toPlainText(),
            'category': self.ui.cat_combo.currentText(),
        }
        

class FastPreviewUpdater:

    def __init__(self, dialog):
        self._dialog = dialog
        self._dialog.ui.title_edit.textChanged.connect(self.on_text_changed)
        self._dialog.ui.body_edit.textChanged.connect(self.on_text_changed)
        
    def on_text_changed(self):
        self._dialog._update_preview()


class LazyPreviewUpdater:

    def __init__(self, dialog):
        self._dialog = dialog
        self._last_row = self._get_row()
        self._text_changed = False
        
        self._dialog.ui.body_edit.cursorPositionChanged.connect(self.on_cursor_pos_changed)
        self._dialog.ui.body_edit.textChanged.connect(self.on_text_changed)
        
    def on_cursor_pos_changed(self):
        row = self._get_row()
        if row != self._last_row and self._text_changed:
            self._dialog._update_preview()
            self._last_row = row
            self._text_changed = False
        
    def on_text_changed(self):
        self._text_changed = True

    def _get_row(self):
        cursor = self._dialog.ui.body_edit.textCursor()
        block = cursor.block()
        return block.firstLineNumber()
        
            