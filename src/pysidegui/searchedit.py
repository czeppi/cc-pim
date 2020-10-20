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
from typing import List

from PySide2.QtCore import Qt
from PySide2.QtGui import QFocusEvent, QKeyEvent
from PySide2.QtWidgets import QCompleter, QWidget
from PySide2.QtWidgets import QLineEdit


class SearchEdit(QLineEdit):

    def __init__(self, parent: QWidget):
        QLineEdit.__init__(self, parent)
        self.completer = None

    def init_completer(self, keywords: List[str]) -> None:
        assert self.completer is None

        self.completer = QCompleter(keywords, self)
        self.completer.setWidget(self)
        self.completer.setCompletionMode(QCompleter.PopupCompletion)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.completer.activated().connect(self.on_insert_completion)

    def completer(self) -> QCompleter:
        return self.completer

    def on_insert_completion(self, completion):
        if self.completer.widget() != self:
            return
        prefix = self.completer.completionPrefix()
        extra_text = completion[len(prefix):] + ', '
        self.insert(extra_text)

    def text_under_cursor(self) -> str:
        text = self.text()
        cursor_pos = self.cursorPosition()

        start_index = None
        comma_index1 = text[:cursor_pos].rfind(',')
        if comma_index1 >= 0:
            start_index = comma_index1 + 1

        end_index = None
        comma_index2 = text[cursor_pos:].find(',')
        if comma_index2 >= 0:
            end_index = cursor_pos + comma_index2

        return text[start_index:end_index].strip()

    def focus_in_event(self, event: QFocusEvent) -> None:
        if self.completer:
            self.completer.setWidget(self)
        QLineEdit.focusInEvent(self, event)

    def keyPressEvent(self, key_event: QKeyEvent) -> None:
        if self.completer and self.completer.popup().isVisible():
            # The following keys are forwarded by the completer to the widget
            key = key_event.key()
            if key in (Qt.Key_Enter, Qt.Key_Return, Qt.Key_Escape, Qt.Key_Tab, Qt.Key_Backtab):
                key_event.ignore()
                return  # let the completer do default behavior

        is_ctrl_modifier = (key_event.modifiers() & Qt.ControlModifier) != 0
        is_shift_modifier = (key_event.modifiers() & Qt.ShiftModifier) != 0
        ctrl_or_shift = is_ctrl_modifier or is_shift_modifier

        is_shortcut = is_ctrl_modifier and key_event.key() == Qt.Key_E  # CTRL+E
        if not self.completer or not is_shortcut:  # do not process the shortcut when we have a completer
            QLineEdit.keyPressEvent(self, key_event)

        if not self.completer or ctrl_or_shift and key_event.text() == '':
            return

        eow = "~!@#$%^&*()_+{}|:\"<>?,./;'[]\\-="  # end of word
        has_modifier = (key_event.modifiers() != Qt.NoModifier) and not ctrl_or_shift
        completion_prefix = self.text_under_cursor()

        if not is_shortcut:
            event_text = key_event.text()
            if has_modifier or not event_text or len(completion_prefix) < 1 or event_text[-1] in eow:
                self.completer.popup().hide()
                return

        if completion_prefix != self.completer.completionPrefix():
            self.completer.setCompletionPrefix(completion_prefix)
            self.completer.popup().setCurrentIndex(self.completer.completionModel().index(0, 0))

        cr = self.cursorRect()
        cr.setWidth(self.completer.popup().sizeHintForColumn(0) +
                    self.completer.popup().verticalScrollBar().sizeHint().width())
        self.completer.complete(cr)  # popup it up!
