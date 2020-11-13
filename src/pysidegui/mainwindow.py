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
import re
import webbrowser
from datetime import datetime
from typing import Optional, Iterator, List

from PySide2.QtCore import Qt, QPoint
from PySide2.QtWidgets import QListWidgetItem, QProgressDialog, QMenu
from PySide2.QtWidgets import QMainWindow

from contacts.contactmodel import ContactModel
from context import Context
from pysidegui._ui2_.ui_mainwindow import Ui_MainWindow, QResizeEvent, QMoveEvent, QBrush, QColor
from pysidegui.contactsgui.contactsgui import ContactsGui
from pysidegui.globalitemid import GlobalItemID
from pysidegui.modelgui import ResultItemData, ModelGui
from pysidegui.tasksgui.tasksgui import TasksGui
from tasks.caching import TaskCacheManager, TaskCache, TaskFilesState


class MainWindow(QMainWindow):

    def __init__(self, context: Context):
        super().__init__(None)
        self._context = context
        self._config = context.user.read_config()
        self._state = context.user.read_state()
        self._data_icons = context.user.read_icons()
        self._contact_css = context.user.read_contact_css()
        self._task_css = context.user.read_task_css()
        self._cur_css = self._contact_css

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.ui.splitter.setStretchFactor(0, 0)
        self.ui.splitter.setStretchFactor(1, 1)
        self.resize(*self._state.frame_size)
        self.move(*self._state.frame_pos)
        self.ui.splitter.setSizes([self._state.search_width, self._state.frame_size[0] - self._state.search_width])

        contact_repo = context.user.get_contact_repo()
        contact_repo.reload()
        date_changes, fact_changes = contact_repo.aggregate_revisions()
        contact_model = ContactModel(date_changes, fact_changes)

        task_meta_model = context.system.read_task_metamodel()
        self._task_model = context.user.read_task_model(task_meta_model, self._config.tasks_root)
        self._task_model.update_cache_of_active_tasks()
        self._contacts_gui = ContactsGui(contact_model, contact_repo)
        self._tasks_gui = TasksGui(self._task_model)

        self._cur_model_gui: ModelGui = self._contacts_gui
        self._show_obj_id = None
        self._enable_show_details = True

        self._update_category_filter()
        self._update_files_state_filter()
        self._update_list()

        self.ui.action_revert_changes.setVisible(False)  # todo: implement or remove
        self.ui.files_state_filter.hide()
        self.ui.search_edit.setFocus()
        self.ui.search_result_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.ui.search_result_list.customContextMenuRequested.connect(self.on_list_item_context_menu)
        if self._contact_css:
            self.ui.html_view.document().setDefaultStyleSheet(self._contact_css)

        self.ui.action_contacts.triggered.connect(self.on_contacts_mode)
        self.ui.action_tasks.triggered.connect(self.on_tasks_mode)
        self.ui.action_contacts.setChecked(True)
        self.ui.action_tasks.setChecked(False)

        self.ui.action_new_item.triggered.connect(self.on_new_item)
        self.ui.action_edit_item.triggered.connect(self.on_edit_item)
        self.ui.action_save_all.triggered.connect(self.on_save_all)
        self.ui.action_revert_changes.triggered.connect(self.on_revert_changed)
        self.ui.action_update_cache.triggered.connect(self.on_update_cache)
        self.ui.splitter.splitterMoved.connect(self.on_splitter_moved)
        self.ui.search_edit.textChanged.connect(self.on_search_text_changed)
        self.ui.category_filter.currentIndexChanged.connect(self.on_category_changed)
        self.ui.files_state_filter.currentIndexChanged.connect(self.on_files_state_changed)
        self.ui.search_result_list.currentItemChanged.connect(self.on_cur_list_item_changed)
        self.ui.search_result_list.itemActivated.connect(self.on_list_item_activated)
        self.ui.html_view.click_link_observers.append(self.on_html_view_click_link)

    def _update_category_filter(self) -> None:
        self.ui.category_filter.clear()
        self.ui.category_filter.addItem('')
        for category in self._cur_model_gui.iter_categories():
            icon = self._data_icons.get(category.lower(), None)
            if icon is not None:
                self.ui.category_filter.addItem(icon, category)
            else:
                self.ui.category_filter.addItem(category)

    def _update_files_state_filter(self) -> None:
        self.ui.files_state_filter.clear()
        self.ui.files_state_filter.addItem('')
        for i, files_state in enumerate(TaskFilesState):
            if files_state != TaskFilesState.UNKNOWN:
                self.ui.files_state_filter.addItem(files_state.name.lower())
                rgb = files_state.rgb()
                if rgb is not None:
                    color = QColor(*rgb)
                    self.ui.files_state_filter.setItemData(i, color, Qt.ForegroundRole)

    def resizeEvent(self, resize_event: QResizeEvent) -> None:
        new_size = resize_event.size().width(), resize_event.size().height()
        if new_size != self._state.frame_size:
            self._state.frame_size = new_size
            self._context.user.write_state(self._state)

    def moveEvent(self, move_event: QMoveEvent) -> None:
        new_pos = move_event.pos().x(), move_event.pos().y()
        if new_pos != self._state.frame_pos:
            self._state.frame_pos = new_pos
            self._context.user.write_state(self._state)

    def on_splitter_moved(self, new_pos: int, index: int) -> None:
        if new_pos != self._state.search_width:
            self._state.search_width = new_pos
            self._context.user.write_state(self._state)

    def on_contacts_mode(self):
        self.ui.action_contacts.setChecked(True)
        self.ui.action_tasks.setChecked(False)
        self.ui.files_state_filter.hide()
        self._cur_model_gui = self._contacts_gui
        self._update_category_filter()
        self.ui.search_result_list.setCurrentItem(None)
        self._update_list()
        if self._contact_css:
            self.ui.html_view.document().setDefaultStyleSheet(self._contact_css)
        self._cur_css = self._contact_css

    def on_tasks_mode(self):
        self.ui.action_contacts.setChecked(False)
        self.ui.action_tasks.setChecked(True)
        self.ui.files_state_filter.show()
        self._cur_model_gui = self._tasks_gui
        self._update_category_filter()
        self.ui.search_result_list.setCurrentItem(None)
        self._update_list()
        if self._task_css:
            self.ui.html_view.document().setDefaultStyleSheet(self._task_css)
        self._cur_css = self._task_css

    def on_new_item(self):
        new_obj_id = self._cur_model_gui.new_item(frame=self, data_icons=self._data_icons, css_buf=self._cur_css)
        if new_obj_id is not None:
            self._update_toolbar_icons()
            self._update_list(select_obj_id=new_obj_id)
            self._update_html_view(new_obj_id)

    def on_edit_item(self):
        self._edit_show_item()
        
    def on_list_item_activated(self, item):
        self._show_obj_id = item.data(Qt.UserRole)
        self._edit_show_item()

    def _edit_show_item(self) -> None:
        obj_id = self._show_obj_id
        if obj_id is None:
            return

        if self._cur_model_gui.edit_item(obj_id, frame=self, data_icons=self._data_icons, css_buf=self._cur_css):
            self._update_toolbar_icons()
            self._update_list()
            self._update_html_view(obj_id)

    def on_search_text_changed(self, new_text: str):
        self._update_list()

    def on_category_changed(self, category_index: int):
        self._update_list()

    def on_files_state_changed(self, files_state_index: int):
        self._update_list()

    def on_cur_list_item_changed(self, item, previous_item):
        self.ui.action_edit_item.setEnabled(item is not None)

        if self._enable_show_details:
            obj_id = None if item is None else item.data(Qt.UserRole)
            self._update_html_view(obj_id)

    def on_list_item_context_menu(self, point: QPoint):
        cur_item = self.ui.search_result_list.currentItem()
        obj_id = cur_item.data(Qt.UserRole)

        global_pos = self.ui.search_result_list.mapToGlobal(point)
        menu_items = list(self._cur_model_gui.iter_context_menu_items(obj_id))
        if menu_items:
            context_menu = QMenu()
            for menu_item in menu_items:
                context_menu.addAction(menu_item)
            action = context_menu.exec_(global_pos)
            if action is not None:
                self._cur_model_gui.exec_context_menu_action(
                    obj_id, action.text(),
                    file_commander_cmd=self._config.file_commander_cmd)
                self._update_list()

    def on_html_view_click_link(self, href_str: str):
        obj_id = self._cur_model_gui.get_id_from_href(href_str)
        if obj_id is not None:
            self._update_html_view(obj_id)
        else:
            webbrowser.open_new_tab(href_str)

    def on_save_all(self):
        if self._cur_model_gui.save_all():
            self._update_toolbar_icons()

    def on_revert_changed(self):
        if self._cur_model_gui.revert_change():
            self._update_toolbar_icons()
            self._update_list(select_obj_id=None)
            self._update_html_view(obj_id=None)

    def on_update_cache(self):
        t0 = datetime.now()
        cache_mgr = TaskCacheManager(self._config.tasks_root)
        task_resources = cache_mgr.read_resources()

        task_caches: List[TaskCache] = []
        n = len(task_resources)
        dlg = QProgressDialog("updating...", "Abort", 0, n)
        dlg.setWindowTitle("Cache")
        dlg.setWindowModality(Qt.WindowModal)
        for i in range(n):
            task_caches.append(task_resources[i].read())

            dlg.setValue(i)
            if dlg.wasCanceled():
                return

        self._task_model.update_cache(t0, task_caches)
        dlg.setValue(n)
        self._update_list()

    def _update_toolbar_icons(self):
        exists_uncommitted_changes = self._cur_model_gui.exists_uncommitted_changes()
        self.ui.action_save_all.setEnabled(exists_uncommitted_changes)
        self.ui.action_revert_changes.setEnabled(exists_uncommitted_changes)

    def _update_list(self, select_obj_id: Optional[GlobalItemID] = None) -> None:
        self._enable_show_details = False
        old_cur_obj_id = self._get_cur_list_item_obj_id()

        self.ui.search_result_list.clear()
        for result_item in self._iter_filtered_items():
            self._add_list_item(result_item)

        if select_obj_id is None:
            select_obj_id = old_cur_obj_id
        if select_obj_id:
            self._select_item(select_obj_id)

        self._enable_show_details = True

    def _get_cur_list_item_obj_id(self) -> GlobalItemID:
        old_cur_list_item = self.ui.search_result_list.currentItem()
        if old_cur_list_item:
            return old_cur_list_item.data(Qt.UserRole)

    def _iter_filtered_items(self) -> Iterator[ResultItemData]:
        search_text = self.ui.search_edit.text()
        search_words = [x.strip() for x in search_text.split() if x.strip() != '']
        filter_category = self.ui.category_filter.currentText()
        filter_files_state = ''
        if self.ui.files_state_filter.isVisible():
            filter_files_state = self.ui.files_state_filter.currentText()

        yield from self._cur_model_gui.iter_sorted_filtered_items(
            search_words, filter_category, filter_files_state)

    def _add_list_item(self, item_data: ResultItemData) -> None:
        new_item = QListWidgetItem(item_data.title)
        new_item.setData(Qt.UserRole, item_data.glob_id)

        if item_data.rgb is not None:
            color = QColor(*item_data.rgb)
            brush = QBrush(color)
            new_item.setForeground(brush)

        icon = self._data_icons.get(item_data.category.lower(), None)
        if icon is not None:
            new_item.setIcon(icon)

        self.ui.search_result_list.addItem(new_item)

    def _select_item(self, obj_id: GlobalItemID) -> None:
        list_ctrl = self.ui.search_result_list
        for i in range(list_ctrl.count()):
            item = list_ctrl.item(i)
            if item.data(Qt.UserRole) == obj_id:
                list_ctrl.setCurrentItem(item)
                break

    def _update_html_view(self, obj_id: Optional[GlobalItemID]) -> None:
        self._show_obj_id = obj_id
        if obj_id:
            search_rex = self._create_search_rex()
            html_text = self._cur_model_gui.get_html_text(obj_id, search_rex)
        else:
            html_text = ''
        self.ui.html_view.set_text(html_text)

    def _create_search_rex(self) -> Optional[re.Pattern]:
        search_text = self.ui.search_edit.text()
        if search_text:
            search_words = [x.strip() for x in search_text.split() if x.strip() != '']
            return re.compile('|'.join(search_words),
                              flags=re.I)  # todo: should only find matches which begins with search words
