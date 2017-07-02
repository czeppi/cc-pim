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

from PySide.QtCore import Qt
from PySide.QtGui import QListWidgetItem
from PySide.QtGui import QMainWindow

from pysidegui._ui_.ui_mainwindow import Ui_MainWindow
from pysidegui.contacts.guifacade import ContactsGuiFacade


class MainWindow(QMainWindow):

    def __init__(self, context, parent=None):
        super(MainWindow, self).__init__(parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        
        self.ui.splitter.setStretchFactor(0, 0)
        self.ui.splitter.setStretchFactor(1, 1)

        self._contact_gui_facade = ContactsGuiFacade(context)

        self._cur_gui_facade = self._contact_gui_facade
        self._show_obj_id = None
        self._enable_show_details = True

        self._update_list()
        self.ui.search_edit.setFocus()
        
        self.ui.action_contacts.triggered.connect(self.on_contacts_mode)
        self.ui.action_notes.triggered.connect(self.on_notes_mode)
        self.ui.action_tasks.triggered.connect(self.on_tasks_mode)
        self.ui.action_contacts.setChecked(True)
        self.ui.action_notes.setChecked(False)
        self.ui.action_tasks.setChecked(False)

        self.ui.action_new_contact.triggered.connect(self.on_new_contact)
        self.ui.action_edit_contact.triggered.connect(self.on_edit_contact)
        self.ui.action_save_all.triggered.connect(self.on_save_all)
        self.ui.action_revert_changes.triggered.connect(self.on_revert_changed)
        self.ui.search_edit.textChanged.connect(self.on_search_text_changed)
        self.ui.search_result_list.currentItemChanged.connect(self.on_cur_list_item_changed)
        self.ui.search_result_list.itemActivated.connect(self.on_list_item_activated)
        self.ui.html_view.click_link_observers.append(self.on_html_view_click_link)

    def on_contacts_mode(self):
        self.ui.action_contacts.setChecked(True)
        self.ui.action_notes.setChecked(False)
        self.ui.action_tasks.setChecked(False)

    def on_notes_mode(self):
        self.ui.action_contacts.setChecked(False)
        self.ui.action_notes.setChecked(True)
        self.ui.action_tasks.setChecked(False)

    def on_tasks_mode(self):
        self.ui.action_contacts.setChecked(False)
        self.ui.action_notes.setChecked(False)
        self.ui.action_tasks.setChecked(True)

    def on_new_contact(self):
        new_obj_id = self._contact_gui_facade.new_object(frame=self)
        if new_obj_id is not None:
            self._update_icons()
            self._update_list(select_obj_id=new_obj_id)
            self._update_html_view(new_obj_id)

    def on_edit_contact(self):
        self._edit_show_contact()
        
    def on_list_item_activated(self, item):
        self._show_obj_id = item.data(Qt.UserRole)
        self._edit_show_contact()

    def _edit_show_contact(self):
        obj_id = self._show_obj_id
        if obj_id is None:
            return

        if self._contact_gui_facade.edit_object(obj_id, frame=self):
            self._update_icons()
            self._update_list()
            self._update_html_view(obj_id)

    def on_search_text_changed(self, new_text):
        self._update_list()
        
    def on_cur_list_item_changed(self, item, previous_item):
        self.ui.action_edit_contact.setEnabled(item is not None)

        if self._enable_show_details:
            obj_id = None if item is None else item.data(Qt.UserRole)
            self._update_html_view(obj_id)

    def on_html_view_click_link(self, href_str):
        obj_id = self._contact_gui_facade.get_id_from_href(href_str)
        self._update_html_view(obj_id)

    def on_save_all(self):
        if self._contact_gui_facade.save_all():
            self._update_icons()

    def on_revert_changed(self):
        if self._contact_gui_facade.revert_change():
            self._update_icons()
            self._update_list(select_obj_id=None)
            self._update_html_view(obj_id=None)

    def _update_icons(self):
        exists_uncommited_changes = self._contact_gui_facade.exists_uncommited_changes()
        self.ui.action_save_all.setEnabled(exists_uncommited_changes)
        self.ui.action_revert_changes.setEnabled(exists_uncommited_changes)

    def _update_list(self, select_obj_id=None):
        self._enable_show_details = False
        old_cur_obj_id = self._get_cur_list_obj_id()

        self.ui.search_result_list.clear()
        for obj_id in self._iter_sorted_ids_from_keywords():
            self._add_contact_item(obj_id)

        if select_obj_id is None:
            select_obj_id = old_cur_obj_id
        if select_obj_id:
            self._select_contact(select_obj_id)

        self._enable_show_details = True

    def _get_cur_list_obj_id(self):
        old_cur_list_item = self.ui.search_result_list.currentItem()
        if old_cur_list_item:
            return old_cur_list_item.data(Qt.UserRole)

    def _iter_sorted_ids_from_keywords(self):
        keywords_str = self.ui.search_edit.text()
        keywords = [x.strip() for x in keywords_str.split() if x.strip() != '']
        yield from self._contact_gui_facade.iter_sorted_ids_from_keywords(keywords)

    def _add_contact_item(self, obj_id):
        new_item = self._create_new_list_item(obj_id)
        self.ui.search_result_list.addItem(new_item)
        
    def _create_new_list_item(self, obj_id):
        title = self._contact_gui_facade.get_object_title(obj_id)
        new_item = QListWidgetItem(title)
        new_item.setData(Qt.UserRole, obj_id)
        return new_item

    def _select_contact(self, obj_id):
        list_ctrl = self.ui.search_result_list
        for i in range(list_ctrl.count()):
            item = list_ctrl.item(i)
            if item.data(Qt.UserRole) == obj_id:
                list_ctrl.setCurrentItem(item)
                break

    def _update_html_view(self, obj_id):
        self._show_obj_id = obj_id
        if obj_id:
            html_text = self._contact_gui_facade.get_html_text(obj_id)
        else:
            html_text = ''
        self.ui.html_view.setText(html_text)
