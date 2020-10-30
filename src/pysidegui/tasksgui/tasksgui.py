# Copyright (C) 2017  Christian Czepluch
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

from pathlib import Path
from typing import Optional, Iterator, Iterable, Dict

from PySide2 import QtGui
from PySide2.QtWidgets import QMainWindow

from contacts.contactmodel import ContactID
from pysidegui.globalitemid import GlobalItemID, GlobalItemTypes
from pysidegui.modelgui import ModelGui
from pysidegui.tasksgui.taskeditdialog import TaskEditDialog
from context import Context
from tasks.db import DB
from tasks.html_creator import write_htmlstr
from tasks.metamodel import MetaModel
from tasks.taskmodel import TaskModel, KeywordExtractor, Task


class TasksGui(ModelGui):

    def __init__(self, task_model: TaskModel):
        self._task_model = task_model
        keywords = self._task_model.calc_keywords()
        # self.ui.title_edit.init_completer(keywords)  # todo?

    def new_item(self, frame: QMainWindow, data_icons: Dict[str, QtGui.QIcon]) -> Optional[GlobalItemID]:
        new_task = self._task_model.create_new_task()
        dlg = TaskEditDialog(frame, task=new_task, task_model=self._task_model, data_icons=data_icons)
        if dlg.exec() == dlg.Accepted:
            dlg_values = dlg.get_values()  # { attr-name -> new-value }
            new_task_rev = new_task.create_new_revision(**dlg_values)
            self._task_model.add_task_revision(new_task_rev)
            return _convert_task2global_id(new_task_rev.task_serial)

    def edit_item(self, glob_item_id: GlobalItemID, frame: QMainWindow, data_icons: Dict[str, QtGui.QIcon]) -> bool:
        task_serial = _convert_global2task_serial(glob_item_id)
        task = self._task_model.get_task(task_serial)

        dlg = TaskEditDialog(frame, task, task_model=self._task_model, data_icons=data_icons)
        if dlg.exec() != dlg.Accepted:
            return False

        dlg_values = dlg.get_values()  # { attr-name -> new-value }
        if not task.last_revision.have_values_changed(dlg_values):
            return False

        new_task_rev = task.create_new_revision(**dlg_values)
        self._task_model.add_task_revision(new_task_rev)
        return True

    def save_all(self) -> bool:
        return True  # not necessary, cause changes were committed at end of dialog

    def revert_change(self) -> bool:
        raise NotImplemented  # todo: implement

    def get_html_text(self, glob_item_id: GlobalItemID) -> str:
        task_serial = _convert_global2task_serial(glob_item_id)
        task = self._task_model.get_task(task_serial)
        title = task.get_header()
        page = task.last_revision.page
        html_text = write_htmlstr(title, page)
        return html_text

    def exists_uncommitted_changes(self) -> bool:
        return False  # there are not such changes, cause changes were committed at end of dialog

    def get_id_from_href(self, href_str: str) -> GlobalItemID:
        raise NotImplemented  # todo: implement

    def iter_sorted_ids_from_keywords(self, keywords) -> Iterator[GlobalItemID]:
        filtered_tasks = self._iter_filtered_tasks(keywords)
        sorted_tasks = sorted(filtered_tasks, key=lambda x: x.serial, reverse=True)
        for task in sorted_tasks:
            yield _convert_task2global_id(task.serial)

    def _iter_filtered_tasks(self, keywords: Iterable[str]) -> Iterator[Task]:
        for task in self._task_model.tasks:
            if task.last_revision.contains_all_keyword(keywords):
                yield task

    def get_object_title(self, glob_item_id: GlobalItemID) -> str:
        task_serial = _convert_global2task_serial(glob_item_id)
        task = self._task_model.get_task(task_serial)
        return task.get_header()

    def get_object_category(self, glob_item_id: GlobalItemID) -> str:
        task_serial = _convert_global2task_serial(glob_item_id)
        task = self._task_model.get_task(task_serial)
        return task.last_revision.category

    def iter_categories(self) -> Iterator[str]:
        yield from self._task_model.get_sorted_categories()


def _convert_global2task_serial(glob_id: GlobalItemID) -> int:
    assert glob_id.type == GlobalItemTypes.TASK
    return glob_id.serial


def _convert_task2global_id(task_serial: int) -> GlobalItemID:
    return GlobalItemID(GlobalItemTypes.TASK, task_serial)
