#! /usr/bin/env python
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

from PySide.QtGui import QMainWindow
from PySide.QtGui import QLabel
from PySide.QtGui import QCompleter
from PySide.QtGui import QListWidgetItem
from PySide.QtCore import Qt
from pysidegui._ui_.ui_mainwindow import Ui_MainWindow
from context import Context
#from modeling.notesmodel import NotesModel
#from modeling.notesmodel import Note
from modeling.repository import Repository
from modeling.contacts import Contacts


class MainWindow(QMainWindow):

    def __init__(self, context, parent=None):
        super(MainWindow, self).__init__(parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        
        self.ui.splitter.setStretchFactor(0, 0)
        self.ui.splitter.setStretchFactor(1, 1)

        self._contact_repo = Repository(context.contacts_db_path)
        self._contact_repo.reload()
        date_changes, fact_changes = self._contact_repo.aggregate_revisions()
        self._contacts = Contacts(date_changes, fact_changes)


        # self._notes_model = NotesModel(context)
        # self._notes_model.read()
        
        # keywords = self._notes_model.calc_keywords()
        # self.ui.search_edit.init_completer(keywords)
        
        self._update_list()
        self.ui.search_edit.setFocus()
        
        # self.ui.action_new_note.triggered.connect(self.on_new_note)
        # self.ui.action_edit_note.triggered.connect(self.on_edit_note)
        self.ui.search_edit.textChanged.connect(self.on_search_text_changed)
        self.ui.search_result_list.currentItemChanged.connect(self.on_cur_list_item_changed)
        self.ui.search_result_list.itemActivated.connect(self.on_list_item_activated)
        
    def on_new_note(self):
        new_note = self._notes_model.create_new_note()
        dlg = NoteEditDialog(self, note=new_note, notes_model=self._notes_model)
        if dlg.exec() == dlg.Accepted:
            dlg_values = dlg.get_values()  # { attr-name -> new-value }
            new_note_rev = new_note.create_new_revision(**dlg_values)
            self._notes_model.add_note_revision(new_note_rev)
            new_note2 = self._notes_model.get_note(new_note_rev.note_id)
            new_item = self._create_new_list_item(new_note2)
            
            self.ui.search_result_list.insertItem(0, new_item)
            self.ui.search_result_list.setCurrentItem(new_item)

    def on_edit_note(self):
        cur_item = self.ui.search_result_list.currentItem()
        if cur_item is None:
            raise Exception('')
            
        self._edit_item(cur_item)
        
    def on_search_text_changed(self, new_text):
        stripped_text = new_text.strip()
        #if new_text == '' or len(stripped_text) > 0 and stripped_text[-1] == ',':
        self._update_list()
        
    def on_cur_list_item_changed(self, item, previous_item):
        self.ui.action_edit_note.setEnabled(item is not None)

        if item is not None:
            note_id = item.data(Qt.UserRole)
            note = self._notes_model.get_note(note_id)
            html_text = note.last_revision.get_html_text()
        else:
            html_text = ''
        
        self.ui.html_edit.setText(html_text)
        
    def on_list_item_activated(self, item):
        self._edit_item(item)
        
    def _edit_item(self, item):
        note_id = item.data(Qt.UserRole)
        note = self._notes_model.get_note(note_id)
            
        dlg = NoteEditDialog(self, note, notes_model=self._notes_model)
        if dlg.exec() == dlg.Accepted:
            dlg_values = dlg.get_values()  # { attr-name -> new-value }
            if note.last_revision.have_values_changed(dlg_values):
                new_note_rev = note.create_new_revision(**dlg_values)
                self._notes_model.add_note_revision(new_note_rev)
                
                html_text = note.last_revision.get_html_text()
                self.ui.html_edit.setText(html_text)
    
    def _update_list(self):
        keywords_str = self.ui.search_edit.text()
        keywords = [x.strip() for x in keywords_str.split(',') if x.strip() != '']
        filtered_contacts = self._iter_filtered_contacts(keywords)
        sorted_contacts = self._sort_contacts(filtered_contacts)
        
        self.ui.search_result_list.clear()
        for contact in sorted_contacts:
            self._add_contact_item(contact)
            
        # self._add_test_item('aaa', foreign_key=1)
        # self._add_test_item('bbb', foreign_key=2)
        # self._add_test_item('ccc', foreign_key=3)

    def _add_test_item(self, header, foreign_key):
        new_item = QListWidgetItem(header)
        new_item.setData(Qt.UserRole, foreign_key)
        self.ui.search_result_list.addItem(new_item)
            
    def _iter_filtered_contacts(self, keywords):
        for contact in self._contacts.iter_objects():
            if contact.contains_all_keywords(keywords):
                yield contact

    def _sort_contacts(self, contacts):
        return sorted(contacts, key=lambda x: x.id)
        
    def _add_contact_item(self, contact):
        new_item = self._create_new_list_item(contact)
        self.ui.search_result_list.addItem(new_item)
        
    def _create_new_list_item(self, contact):
        new_item = QListWidgetItem(contact.title)
        new_item.setData(Qt.UserRole, contact.id)
        return new_item
