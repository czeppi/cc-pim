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

from PySide2.QtCore import Qt
from PySide2 import QtGui
from PySide2.QtWidgets import QListWidgetItem
from PySide2.QtWidgets import QMainWindow

from context import Context
from pysidegui._ui2_.ui_mainwindow import Ui_MainWindow
from pysidegui.contactsgui.contactsgui import ContactsGui
from pysidegui.tasksgui.tasksgui import TasksGui


class MainWindow(QMainWindow):

    def __init__(self, context: Context, parent=None):
        super().__init__(parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.ui.splitter.setStretchFactor(0, 0)
        self.ui.splitter.setStretchFactor(1, 1)

        self._data_icons = self._create_data_icons(context)

        self._contacts_gui = ContactsGui(context)
        self._tasks_gui = TasksGui()

        self._cur_model_gui = self._contacts_gui
        self._show_obj_id = None
        self._enable_show_details = True

        self._update_category_filter()
        self._update_list()
        self.ui.search_edit.setFocus()
        
        self.ui.action_contacts.triggered.connect(self.on_contacts_mode)
        self.ui.action_tasks.triggered.connect(self.on_tasks_mode)
        self.ui.action_contacts.setChecked(True)
        self.ui.action_tasks.setChecked(False)

        self.ui.action_new_item.triggered.connect(self.on_new_item)
        self.ui.action_edit_item.triggered.connect(self.on_edit_item)
        self.ui.action_save_all.triggered.connect(self.on_save_all)
        self.ui.action_revert_changes.triggered.connect(self.on_revert_changed)
        self.ui.search_edit.textChanged.connect(self.on_search_text_changed)
        self.ui.category_filter.currentIndexChanged.connect(self.on_category_changed)
        self.ui.search_result_list.currentItemChanged.connect(self.on_cur_list_item_changed)
        self.ui.search_result_list.itemActivated.connect(self.on_list_item_activated)
        self.ui.html_view.click_link_observers.append(self.on_html_view_click_link)

    @staticmethod
    def _create_data_icons(context: Context):
        return {icon_fpath.stem.lower(): QtGui.QIcon(str(icon_fpath))
                for icon_fpath in context.data_icon_dir.iterdir()}

    def _update_category_filter(self):
        self.ui.category_filter.clear()
        self.ui.category_filter.addItem('')
        for category in self._cur_model_gui.iter_categories():
            icon = self._data_icons.get(category.lower(), None)
            if icon is not None:
                self.ui.category_filter.addItem(icon, category)
            else:
                self.ui.category_filter.addItem(category)

    def on_contacts_mode(self):
        self.ui.action_contacts.setChecked(True)
        self.ui.action_tasks.setChecked(False)
        self._cur_model_gui = self._contacts_gui
        self._update_category_filter()
        self.ui.search_result_list.setCurrentItem(None)
        self._update_list()

    def on_tasks_mode(self):
        self.ui.action_contacts.setChecked(False)
        self.ui.action_tasks.setChecked(True)
        self._cur_model_gui = self._tasks_gui
        self._update_category_filter()
        self.ui.search_result_list.setCurrentItem(None)
        self._update_list()

    def on_new_item(self):
        new_obj_id = self._cur_model_gui.new_item(frame=self)
        if new_obj_id is not None:
            self._update_icons()
            self._update_list(select_obj_id=new_obj_id)
            self._update_html_view(new_obj_id)

    def on_edit_item(self):
        self._edit_show_item()
        
    def on_list_item_activated(self, item):
        self._show_obj_id = item.data(Qt.UserRole)
        self._edit_show_item()

    def _edit_show_item(self):
        obj_id = self._show_obj_id
        if obj_id is None:
            return

        if self._cur_model_gui.edit_item(obj_id, frame=self):
            self._update_icons()
            self._update_list()
            self._update_html_view(obj_id)

    def on_search_text_changed(self, new_text):
        self._update_list()

    def on_category_changed(self, category_index: int):
        self._update_list()

    def on_cur_list_item_changed(self, item, previous_item):
        self.ui.action_edit_item.setEnabled(item is not None)

        if self._enable_show_details:
            obj_id = None if item is None else item.data(Qt.UserRole)
            self._update_html_view(obj_id)

    def on_html_view_click_link(self, href_str):
        obj_id = self._cur_model_gui.get_id_from_href(href_str)
        self._update_html_view(obj_id)

    def on_save_all(self):
        if self._cur_model_gui.save_all():
            self._update_icons()

    def on_revert_changed(self):
        if self._cur_model_gui.revert_change():
            self._update_icons()
            self._update_list(select_obj_id=None)
            self._update_html_view(obj_id=None)

    def _update_icons(self):
        exists_uncommited_changes = self._cur_model_gui.exists_uncommited_changes()
        self.ui.action_save_all.setEnabled(exists_uncommited_changes)
        self.ui.action_revert_changes.setEnabled(exists_uncommited_changes)

    def _update_list(self, select_obj_id=None):
        self._enable_show_details = False
        old_cur_obj_id = self._get_cur_list_obj_id()

        self.ui.search_result_list.clear()
        for obj_id in self._iter_sorted_ids_from_keywords():
            if self._is_id_in_category_filter(obj_id):
                self._add_list_item(obj_id)

        if select_obj_id is None:
            select_obj_id = old_cur_obj_id
        if select_obj_id:
            self._select_item(select_obj_id)

        self._enable_show_details = True

    def _get_cur_list_obj_id(self):
        old_cur_list_item = self.ui.search_result_list.currentItem()
        if old_cur_list_item:
            return old_cur_list_item.data(Qt.UserRole)

    def _iter_sorted_ids_from_keywords(self):
        keywords_str = self.ui.search_edit.text()
        keywords = [x.strip() for x in keywords_str.split() if x.strip() != '']
        yield from self._cur_model_gui.iter_sorted_ids_from_keywords(keywords)

    def _is_id_in_category_filter(self, obj_id) -> bool:
        filter_category = self.ui.category_filter.currentText()
        if filter_category == '':
            return True  # no filter
        else:
            category = self._cur_model_gui.get_object_category(obj_id)
            return category == filter_category

    def _add_list_item(self, obj_id):
        new_item = self._create_new_list_item(obj_id)
        self.ui.search_result_list.addItem(new_item)
        
    def _create_new_list_item(self, obj_id):
        title = self._cur_model_gui.get_object_title(obj_id)
        category = self._cur_model_gui.get_object_category(obj_id)
        new_item = QListWidgetItem(title)
        new_item.setData(Qt.UserRole, obj_id)

        icon = self._data_icons.get(category.lower(), None)
        if icon is not None:
            new_item.setIcon(icon)
        else:
            pass
        return new_item

    def _select_item(self, obj_id):
        list_ctrl = self.ui.search_result_list
        for i in range(list_ctrl.count()):
            item = list_ctrl.item(i)
            if item.data(Qt.UserRole) == obj_id:
                list_ctrl.setCurrentItem(item)
                break

    def _update_html_view(self, obj_id):
        self._show_obj_id = obj_id
        if obj_id:
            html_text = self._cur_model_gui.get_html_text(obj_id)
        else:
            html_text = ''
        self.ui.html_view.setText(html_text)
