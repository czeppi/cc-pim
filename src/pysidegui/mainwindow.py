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

from collections import OrderedDict
from PySide.QtGui import QMainWindow
from PySide.QtGui import QLabel
from PySide.QtGui import QCompleter
from PySide.QtGui import QListWidgetItem, QInputDialog
from PySide.QtCore import Qt
from pysidegui._ui_.ui_mainwindow import Ui_MainWindow
from pysidegui.contacteditdialog import ContactEditDialog
from context import Context
from modeling.repository import Repository
from modeling.contactmodel import ContactModel


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
        self._contact_model = ContactModel(date_changes, fact_changes)


        # self._notes_model = NotesModel(context)
        # self._notes_model.read()
        
        # keywords = self._notes_model.calc_keywords()
        # self.ui.search_edit.init_completer(keywords)
        
        self._update_list()
        self.ui.search_edit.setFocus()
        
        self.ui.action_new_contact.triggered.connect(self.on_new_contact)
        self.ui.action_edit_contact.triggered.connect(self.on_edit_contact)
        self.ui.action_save_all.triggered.connect(self.on_save_all)
        self.ui.action_revert_changes.triggered.connect(self.on_revert_changed)
        self.ui.search_edit.textChanged.connect(self.on_search_text_changed)
        self.ui.search_result_list.currentItemChanged.connect(self.on_cur_list_item_changed)
        self.ui.search_result_list.itemActivated.connect(self.on_list_item_activated)
        
    def on_new_contact(self):
        type_map = OrderedDict((x.type_name, x) for x in self._contact_model.iter_object_classes())
        type_name, ok = QInputDialog.getItem(self, 'new', 'select a type', list(type_map.keys()), editable=False)
        if ok:
            contact_cls = type_map[type_name]
            new_contact = self._contact_model.create_contact(contact_cls.type_id)

            dlg = ContactEditDialog(self, new_contact, self._contact_model)
            if dlg.exec() == dlg.Accepted:
                self._contact_model.add_changes(
                    date_changes=dlg.date_changes,
                    fact_changes=dlg.fact_changes
                )
            self._update_list()
            self._update_icons()
            self._select_contact(new_contact.id)

    def on_edit_contact(self):
        cur_item = self.ui.search_result_list.currentItem()
        if cur_item is None:
            raise Exception('')
            
        self._edit_item(cur_item)
        
    def on_search_text_changed(self, new_text):
        stripped_text = new_text.strip()
        #if new_text == '' or len(stripped_text) > 0 and stripped_text[-1] == ',':
        self._update_list()
        
    def on_cur_list_item_changed(self, item, previous_item):
        self.ui.action_edit_contact.setEnabled(item is not None)

        if item is not None:
            type_id, obj_serial = item.data(Qt.UserRole)
#            print('type_id={}, serial={}'.format(type_id, obj_serial))
            contact = self._contact_model.get(type_id, obj_serial)
            html_text = contact.get_html_text(self._contact_model)
        else:
            html_text = ''
        
        #self.ui.html_edit.setText(html_text)
        self.ui.output_edit.setText(html_text)
        
    def on_list_item_activated(self, item):
        self._edit_item(item)
        
    def _edit_item(self, item):
        contact_id = item.data(Qt.UserRole)
        type_id, obj_serial = contact_id
        contact = self._contact_model.get(type_id, obj_serial)

        dlg = ContactEditDialog(self, contact, self._contact_model)
        if dlg.exec() == dlg.Accepted:
            self._contact_model.add_changes(
                date_changes=dlg.date_changes,
                fact_changes=dlg.fact_changes
            )
            # if note.last_revision.have_values_changed(dlg_values):
            #     new_note_rev = note.create_new_revision(**dlg_values)
            #     self._notes_model.add_note_revision(new_note_rev)
            #
            #     html_text = note.last_revision.get_html_text()
            #     self.ui.html_edit.setText(html_text)

        self._update_list()
        self._update_icons()
        self._select_contact(contact_id)

    def _select_contact(self, contact_id):
        target_type_id, target_serial = contact_id
        list_ctrl = self.ui.search_result_list
        for i in range(list_ctrl.count()):
            item = list_ctrl.item(i)
            cur_data = item.data(Qt.UserRole)
            type_id, contact_serial = item.data(Qt.UserRole) # !! data() returns list - why ever !!
            if (type_id, contact_serial) == (target_type_id, target_serial):
                list_ctrl.setCurrentItem(item)
                break

    def _update_icons(self):
        exists_uncommited_changes = self._contact_model.exists_uncommited_changes()
        self.ui.action_save_all.setEnabled(exists_uncommited_changes)
        self.ui.action_revert_changes.setEnabled(exists_uncommited_changes)

    def on_save_all(self):
        comment, ok = QInputDialog.getText(None, 'Commit', 'please enter a comment')
        if ok:
            self._contact_model.commit(comment, self._contact_repo)
            self._update_icons()

    def on_revert_changed(self):
        date_changes, fact_changes = self._contact_repo.aggregate_revisions()
        self._contact_model = ContactModel(date_changes, fact_changes)
        self._update_list()
        self._update_icons()

    def _update_list(self):
        keywords_str = self.ui.search_edit.text()
        keywords = [x.strip() for x in keywords_str.split(',') if x.strip() != '']
        filtered_contacts = self._iter_filtered_contacts(keywords)
        sorted_contacts = self._sort_contacts(filtered_contacts)
        
        self.ui.search_result_list.clear()
        for contact in sorted_contacts:
            self._add_contact_item(contact)
            
    def _iter_filtered_contacts(self, keywords):
        for contact in self._contact_model.iter_objects():
            if contact.contains_all_keywords(keywords):
                yield contact

    def _sort_contacts(self, contacts):
        return sorted(contacts, key=lambda x: x.id)
        
    def _add_contact_item(self, contact):
        new_item = self._create_new_list_item(contact)
        self.ui.search_result_list.addItem(new_item)
        
    def _create_new_list_item(self, contact):
        new_item = QListWidgetItem(contact.title)
        new_item.setData(Qt.UserRole, contact.id) # !! make [type_id, serial] from (type_id, serial)
        return new_item

