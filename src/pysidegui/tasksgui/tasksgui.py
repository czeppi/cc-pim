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

from pysidegui.modelgui import ModelGui
from tasks.taskmodel import TaskModel, Task
from pysidegui.tasksgui.taskeditdialog import TaskEditDialog
from pysidegui.tasksgui.context import Context


class TasksGui(ModelGui):

    def __init__(self):
        context = Context()
        self._task_model = TaskModel(context)
        self._task_model.read()

        keywords = self._task_model.calc_keywords()
        #self.ui.title_edit.init_completer(keywords)  # todo

    def new_item(self, frame):
        new_task = self._task_model.create_new_task()
        dlg = TaskEditDialog(self, task=new_task, task_model=self._task_model)
        if dlg.exec() == dlg.Accepted:
            dlg_values = dlg.get_values()  # { attr-name -> new-value }
            new_task_rev = new_task.create_new_revision(**dlg_values)
            self._task_model.add_task_revision(new_task_rev)
            #self._task_model.get_task(new_task_rev.task_id)
            return new_task_rev.task_id

    def edit_item(self, obj_id, frame):
        task_id = obj_id
        task = self._task_model.get_task(task_id)

        dlg = TaskEditDialog(self, task, task_model=self._task_model)
        if dlg.exec() != dlg.Accepted:
            return False

        dlg_values = dlg.get_values()  # { attr-name -> new-value }
        if not task.last_revision.have_values_changed(dlg_values):
            return False

        new_task_rev = task.create_new_revision(**dlg_values)
        self._task_model.add_task_revision(new_task_rev)
        #html_text = task.last_revision.get_html_text()
        #self.ui.html_edit.setText(html_text)
        return True

    def save_all(self):
        #comment, ok = QInputDialog.getText(None, 'Commit', 'please enter a comment')
        #if not ok:
        #    return False

        #self._contact_model.commit(comment, self._contact_repo)
        return True

    def revert_change(self):
        #date_changes, fact_changes = self._contact_repo.aggregate_revisions()
        #self._contact_model = ContactModel(date_changes, fact_changes)
        return True

    def get_html_text(self, obj_id) -> str:
        task_id = obj_id
        task = self._task_model.get_task(task_id)
        html_text = task.last_revision.get_html_text()
        return html_text

    def exists_uncommited_changes(self) -> bool:
        #return self._contact_model.exists_uncommited_changes()
        return False  # todo

    def get_id_from_href(self, href_str: str) -> id:
        contact_id = ContactID.create_from_string(href_str)
        return contact_id

    def iter_sorted_ids_from_keywords(self, keywords):
        filtered_contacts = self._iter_filtered_contacts(keywords)
        sorted_contacts = sorted(filtered_contacts, key=lambda x: x.id)
        for contact in sorted_contacts:
            yield contact.id

    def _iter_filtered_contacts(self, keywords):
        for task in self._task_model.tasks:
            if task.last_revision.contains_all_keyword(keywords):
                yield task

    def get_object_title(self, obj_id) -> str:
        task_id = obj_id
        task = self._task_model.get_task(task_id)
        return task.get_header()