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
import os
import re
import copy
from pathlib import Path
from typing import Optional, Iterator, Iterable, Dict, List as TList, Any

from PySide2.QtGui import QIcon
from PySide2.QtWidgets import QMainWindow

from pysidegui.globalitemid import GlobalItemID, GlobalItemTypes
from pysidegui.modelgui import ModelGui, ResultItemData
from pysidegui.tasksgui.taskeditdialog import TaskEditDialog
from tasks.caching import TaskFilesState, TaskCacheManager
from tasks.html_creator import write_htmlstr, LinkSolver
from tasks.page import Header, NormalText, Paragraph, List, ListItem, Link, Page
from tasks.taskmodel import TaskModel, Task


class TasksGui(ModelGui):
    _REX = re.compile(r"(?P<type>[a-zA-Z]+)(?P<serial>[0-9]+)")

    def __init__(self, task_model: TaskModel):
        self._task_model = task_model
        # keywords = self._task_model.calc_keywords()
        # self.ui.title_edit.init_completer(keywords)  # todo?

    def new_item(self, frame: QMainWindow, data_icons: Dict[str, QIcon],
                 css_buf: Optional[str]) -> Optional[GlobalItemID]:
        new_task = self._task_model.create_new_task()
        dlg = TaskEditDialog(frame, task=new_task, task_model=self._task_model, data_icons=data_icons, css_buf=css_buf)
        if dlg.exec() == dlg.Accepted:
            dlg_values = dlg.get_values()  # { attr-name -> new-value }
            new_task_rev = new_task.create_new_revision(**dlg_values)
            self._task_model.add_task_revision(new_task_rev)
            return _convert_task2global_id(new_task_rev.task_serial)

    def edit_item(self, glob_item_id: GlobalItemID, frame: QMainWindow, data_icons: Dict[str, QIcon],
                  css_buf: Optional[str]) -> bool:
        task_serial = _convert_global2task_serial(glob_item_id)
        task = self._task_model.get_task(task_serial)

        dlg = TaskEditDialog(frame, task, task_model=self._task_model, data_icons=data_icons, css_buf=css_buf)
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
        raise NotImplemented()

    def get_html_text(self, glob_item_id: GlobalItemID) -> str:
        task_serial = _convert_global2task_serial(glob_item_id)
        task = self._task_model.get_task(task_serial)
        title = task.get_header()
        page = copy.deepcopy(task.last_revision.page)
        self._extend_page_with_task_cache(page=page, task=task)
        link_solver = LinkSolver(self._task_model)
        html_text = write_htmlstr(title, page, link_solver=link_solver)
        return html_text

    def _extend_page_with_task_cache(self, page: Page, task: Task) -> None:
        task_cache = task.cache
        if task_cache:
            if task_cache.readme:
                page.block_elements.append(Header(level=2, inline_elements=[NormalText('readme:')]))
                page.block_elements.append(Paragraph([NormalText(task_cache.readme)], preformatted=True))
            if task_cache.file_names:
                page.block_elements.append(Header(level=2, inline_elements=[NormalText('files:')]))
                file_tree = FilebufSplitter(task_cache.file_names).split()
                new_list = List()
                task_path = task.get_path(self._task_model.tasks_root)
                for name in sorted(file_tree.keys()):
                    new_link = Link(text=name, uri=str(task_path / name))
                    new_item = ListItem(inline_elements=[new_link])
                    self._build_file_list_recursive(new_item, file_tree[name], task_path / name)
                    new_list.items.append(new_item)

                page.block_elements.append(new_list)

    def _build_file_list_recursive(self, list_item: ListItem, file_subtree: Dict[str, Any], dpath: Path):
        for name in sorted(file_subtree.keys()):
            new_link = Link(text=name, uri=str(dpath / name))
            new_sub_item = ListItem(inline_elements=[new_link])
            list_item.sub_items.append(new_sub_item)
            self._build_file_list_recursive(new_sub_item, file_subtree[name], dpath / name)

    def exists_uncommitted_changes(self) -> bool:
        return False  # there are not such changes, cause changes were committed at end of dialog

    @classmethod
    def get_id_from_href(cls, href_str: str) -> Optional[GlobalItemID]:
        match = cls._REX.match(href_str)
        if match:
            type_name = match.group('type').upper()
            serial = int(match.group('serial'))

            global_type = GlobalItemTypes[type_name]
            return GlobalItemID(global_type, serial)

    def iter_sorted_filtered_items(self, search_words: Iterable[str],
                                   filter_category: str,
                                   filter_files_state: str) -> Iterator[ResultItemData]:
        yield from sorted(
            self._iter_filtered_items(
                search_words, filter_category, filter_files_state),
            key=lambda x: x.title, reverse=True)

    def _iter_filtered_items(self, search_words: Iterable[str],
                             filter_category: str,
                             filter_files_state: str) -> Iterator[ResultItemData]:
        for task in self._task_model.tasks:
            if task.does_meet_the_criteria(search_words, filter_category, filter_files_state):
                yield ResultItemData(
                    glob_id=_convert_task2global_id(task.serial),
                    category=task.last_revision.category,
                    title=task.get_header(),
                    rgb=task.get_rgb(),
                )

    def iter_categories(self) -> Iterator[str]:
        yield from self._task_model.get_sorted_categories()

    def iter_context_menu_items(self, glob_item_id: GlobalItemID) -> Iterator[str]:
        task_serial = _convert_global2task_serial(glob_item_id)
        task = self._task_model.get_task(task_serial)
        if task.cache:
            files_state = task.cache.files_state
            if files_state in [TaskFilesState.ACTIVE, TaskFilesState.PASSIVE]:
                yield 'open-in-explorer'

            if files_state == TaskFilesState.ACTIVE:
                yield 'zip'
            elif files_state == TaskFilesState.PASSIVE:
                yield 'unzip'
        else:
            yield 'create-dir'

    def exec_context_menu_action(self, glob_item_id: GlobalItemID,
                                 action_name: str, file_commander_cmd: str) -> None:
        print(glob_item_id, action_name)

        tasks_root = self._task_model.tasks_root
        task_serial = _convert_global2task_serial(glob_item_id)
        task = self._task_model.get_task(task_serial)

        if action_name == 'open-in-explorer':
            path = task.get_path(tasks_root)
            cmd = file_commander_cmd.format(path=path)
            os.system(cmd)
        elif action_name == 'create-dir':
            task.create_dir(tasks_root)
            self._update_files_state(task)
        elif action_name == 'zip':
            task.zip_dir(tasks_root)
            self._update_files_state(task)
        elif action_name == 'unzip':
            task.unzip_file(tasks_root)
            self._update_files_state(task)

    def _update_files_state(self, task: Task) -> None:
        cache_mgr = TaskCacheManager(self._task_model.tasks_root)
        cache_mgr.update_state_files_in_db(task.serial,
                                           task.cache.files_state,
                                           db=self._task_model.db)


class FilebufSplitter:

    def __init__(self, file_buf: str):
        self._file_buf = file_buf

    def split(self) -> Dict[str, Any]:
        file_tree: Dict[str, Any] = {}
        path_items: TList[Dict[str, Any]] = [file_tree]
        for line in self._file_buf.split('\n'):
            indent_len = self._calc_indent_len(line)
            assert indent_len % 2 == 0
            level =  indent_len // 2
            assert len(path_items) > level
            del path_items[level + 1:]
            name = line[indent_len:]
            assert name != ''
            new_item = {}
            path_items[level][name] = new_item
            path_items.append(new_item)
        return file_tree

    @staticmethod
    def _calc_indent_len(line) -> int:
        return len(line) - len(line.lstrip())


def _convert_global2task_serial(glob_id: GlobalItemID) -> int:
    assert glob_id.type == GlobalItemTypes.TASK
    return glob_id.serial


def _convert_task2global_id(task_serial: int) -> GlobalItemID:
    return GlobalItemID(GlobalItemTypes.TASK, task_serial)
