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
from PySide.QtGui import QListWidgetItem, QInputDialog
from PySide.QtCore import Qt
from pysidegui._ui_.ui_mainwindow import Ui_MainWindow
from pysidegui.contacteditdialog import ContactEditDialog
from pysidegui.htmlview import ContactHtmlCreator
from modeling.repository import Repository
from modeling.contactmodel import ContactModel, ContactID


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
        self._show_contact_id = None
        self._enable_show_details = True

        self._update_list()
        self.ui.search_edit.setFocus()
        
        self.ui.action_new_contact.triggered.connect(self.on_new_contact)
        self.ui.action_edit_contact.triggered.connect(self.on_edit_contact)
        self.ui.action_save_all.triggered.connect(self.on_save_all)
        self.ui.action_revert_changes.triggered.connect(self.on_revert_changed)
        self.ui.search_edit.textChanged.connect(self.on_search_text_changed)
        self.ui.search_result_list.currentItemChanged.connect(self.on_cur_list_item_changed)
        self.ui.search_result_list.itemActivated.connect(self.on_list_item_activated)
        self.ui.html_view.click_link_observers.append(self.on_html_view_click_link)

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
            self._update_icons()
            self._update_list(select_contact_id=new_contact.id)
            self._update_html_view(new_contact.id)

    def on_edit_contact(self):
        self._edit_show_contact()
        
    def on_search_text_changed(self, new_text):
        self._update_list()
        
    def on_cur_list_item_changed(self, item, previous_item):
        self.ui.action_edit_contact.setEnabled(item is not None)

        if self._enable_show_details:
            contact_id = None if item is None else item.data(Qt.UserRole)
            self._update_html_view(contact_id)

    def on_html_view_click_link(self, href_str):
        contact_id = ContactID.create_from_string(href_str)
        self._update_html_view(contact_id)

    def on_list_item_activated(self, item):
        self._show_contact_id = item.data(Qt.UserRole)
        self._edit_show_contact()

    def _edit_show_contact(self):
        contact_id = self._show_contact_id
        if contact_id is None:
            return

        contact = self._contact_model.get(contact_id)
        dlg = ContactEditDialog(self, contact, self._contact_model)
        if dlg.exec() != dlg.Accepted:
            return

        self._contact_model.add_changes(
            date_changes=dlg.date_changes,
            fact_changes=dlg.fact_changes
        )

        self._update_icons()
        self._update_list()
        self._update_html_view(contact_id)

    def _select_contact(self, contact_id):
        list_ctrl = self.ui.search_result_list
        for i in range(list_ctrl.count()):
            item = list_ctrl.item(i)
            if item.data(Qt.UserRole) == contact_id:
                list_ctrl.setCurrentItem(item)
                break


    def on_save_all(self):
        comment, ok = QInputDialog.getText(None, 'Commit', 'please enter a comment')
        if ok:
            self._contact_model.commit(comment, self._contact_repo)
            self._update_icons()

    def on_revert_changed(self):
        date_changes, fact_changes = self._contact_repo.aggregate_revisions()
        self._contact_model = ContactModel(date_changes, fact_changes)
        self._update_icons()
        self._update_list(select_contact_id=None)
        self._update_html_view(contact_id=None)

    def _update_icons(self):
        exists_uncommited_changes = self._contact_model.exists_uncommited_changes()
        self.ui.action_save_all.setEnabled(exists_uncommited_changes)
        self.ui.action_revert_changes.setEnabled(exists_uncommited_changes)

    def _update_list(self, select_contact_id=None):
        self._enable_show_details = False
        old_cur_contact_id = self._get_cur_list_contact_id()

        sorted_contacts = self._get_sorted_contacts_from_keywords()
        self.ui.search_result_list.clear()
        for contact in sorted_contacts:
            self._add_contact_item(contact)

        if select_contact_id is None:
            select_contact_id = old_cur_contact_id
        if select_contact_id:
            self._select_contact(select_contact_id)

        self._enable_show_details = True

    def _get_cur_list_contact_id(self):
        old_cur_list_item = self.ui.search_result_list.currentItem()
        if old_cur_list_item:
            return old_cur_list_item.data(Qt.UserRole)

    def _get_sorted_contacts_from_keywords(self):
        keywords_str = self.ui.search_edit.text()
        keywords = [x.strip() for x in keywords_str.split() if x.strip() != '']
        filtered_contacts = self._iter_filtered_contacts(keywords)
        return self._sort_contacts(filtered_contacts)

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
        new_item.setData(Qt.UserRole, contact.id)
        return new_item

    def _update_html_view(self, contact_id):
        self._show_contact_id = contact_id
        if contact_id:
            contact = self._contact_model.get(contact_id)
            html_text = ContactHtmlCreator(contact, self._contact_model).create_html_text()
        else:
            html_text = ''
        self.ui.html_view.setText(html_text)
