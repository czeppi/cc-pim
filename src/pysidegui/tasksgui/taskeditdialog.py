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
from typing import Iterator, Dict

from PySide2.QtCore import Qt
from PySide2.QtWidgets import QDialog, QApplication, QWidget

from pysidegui._ui2_.ui_taskeditdialog import Ui_TaskEditDialog
from tasks.html_creator import write_htmlstr
from tasks.markup_reader import read_markup
from tasks.taskmodel import Task, TaskModel


class TaskEditDialog(QDialog):

    def __init__(self, parent: QWidget, task: Task, task_model: TaskModel):
        super().__init__(parent, f=Qt.WindowMaximizeButtonHint)
        self.ui = Ui_TaskEditDialog()
        self.ui.setupUi(self)
        
        self._task = task
        self._task_model = task_model
        self._init_title()
        self._init_splitter()
        self._init_id_edit()
        self._init_cat_combo()
        self._init_title_text()
        self._init_text_edit()
        self._init_preview()
        
        self._preview_updater = FastPreviewUpdater(self)
        self.showMaximized()
        
    def _init_title(self) -> None:
        title = "New Task" if self._task.is_empty() else "Edit Task"
        self.setWindowTitle(
            QApplication.translate(
                "TaskEditDialog", title, None, -1))
                
    def _init_splitter(self) -> None:
        self.ui.splitter.setStretchFactor(0, 2)
        self.ui.splitter.setStretchFactor(1, 3)
    
    def _init_id_edit(self) -> None:
        task = self._task
        self.ui.id_edit.setText(str(task.id))
        self.ui.id_edit.setReadOnly(True)
    
    def _init_cat_combo(self) -> None:
        task = self._task
        sorted_categories = self._task_model.get_sorted_categories()
        self.ui.cat_combo.addItems(sorted_categories)
        
        cat_str = task.last_revision.category
        self.ui.cat_combo.setEditText(cat_str)
        
    def _init_title_text(self) -> None:
        task = self._task
        self.ui.title_edit.setText(task.last_revision.title)
        
        keywords = self._task_model.calc_keywords()
        self.ui.title_edit.init_completer(keywords)
    
    def _init_text_edit(self) -> None:
        task = self._task

        self.ui.body_edit.setFontFamily('Courier')
        self.ui.body_edit.setFontPointSize(12)
        self.ui.body_edit.setAcceptRichText(False)
        self.ui.body_edit.setText(task.last_revision.body)
    
    def _init_preview(self) -> None:
        task = self._task
        # self.ui.preview.setText(task.last_revision.get_html_text())
        html_text = self._get_html_text()
        # html_text = '\n'.join(self._create_dummy_html_text())
        # print(html_text)
        # self.ui.preview.setFontPointSize(20);
        # self.ui.preview.setStyleSheet(
        #    'title: { text-align: center }')
        #    #'font: 12px')
        self.ui.preview.setStyleSheet(
            '* {'
            '    color:  # 222;'
            '    font-size: 10px;'
            '    font-weight: normal;'
            '    margin: 0;'
            '    padding: 0;'
            '}'
            'h1 {'
            '   color:  # 555;'
            '   font-size: 12px;'
            '   text-align: center;'
            '}'
        )
        self.ui.preview.setText(html_text)
        self.ui.preview.setReadOnly(False)

    @staticmethod
    def _create_dummy_html_text() -> Iterator[str]:
        yield '<html>'
        yield '<ul><li>aaa</li><li>bbb</li></ul>'
        yield '<p>aaa</p>'
        yield '<table border="1">'
        yield '<tr><td>A1</td><td>B1</td></tr>'
        yield '<tr><td>A2</td><td>B2</td></tr>'
        yield '</table>'
        yield '</html>'

    def _update_preview(self) -> None:
        # task = self._task
        # values = task.last_revision.get_values()
        # values.update(self.get_values())
        # tmp_task_rev = TaskRevision(**values)
        # html_text = tmp_task_rev.get_html_text()
        html_text = self._get_html_text()
        self.ui.preview.setText(html_text)

    def _get_html_text(self) -> str:
        title = self.ui.title_edit.text()
        body = self.ui.body_edit.toPlainText()
        # category = self.ui.cat_combo.currentText()

        markup_str = f'# {title}\n\n{body}'
        page = read_markup(markup_str)
        html_text = write_htmlstr(page)
        print(html_text)
        return html_text

    def get_values(self) -> Dict[str, str]:
        return {
            'title':    self.ui.title_edit.text(),
            'body':     self.ui.body_edit.toPlainText(),
            'category': self.ui.cat_combo.currentText(),
        }
        

class FastPreviewUpdater:

    def __init__(self, dialog: QDialog):
        self._dialog = dialog
        self._dialog.ui.title_edit.textChanged.connect(self.on_text_changed)
        self._dialog.ui.body_edit.textChanged.connect(self.on_text_changed)
        
    def on_text_changed(self):
        self._dialog._update_preview()


class LazyPreviewUpdater:

    def __init__(self, dialog: QDialog):
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

    def _get_row(self) -> int:
        cursor = self._dialog.ui.body_edit.textCursor()
        block = cursor.block()
        return block.firstLineNumber()
