#! /usr/bin/env python3

# Copyright (C) 2016  Christian Czepluch
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

from PySide.QtGui import (QApplication, QDialog, QDialogButtonBox, QGridLayout, QLabel, QLayout, QLineEdit, QSplitter,
                          QTextEdit, QVBoxLayout, QWidget)
from PySide.QtCore import Qt, QObject, QMetaObject, SIGNAL
from modeling.contactmodel import ContactHtmlCreator
from modeling.basetypes import Ref


class ContactEditDialog(QDialog):

    def __init__(self, parent, contact, contacts_model):
        super().__init__(parent, f=Qt.WindowMaximizeButtonHint)

        self._contact = contact
        self._contacts_model = contacts_model
        self._date_changes = {}  # date_serial -> VagureDate
        self._fact_changes = {}  # fact_serial -> Fact

        # self.ui = Ui_NoteEditDialog()
        # self.ui.setupUi(self)
        self.setObjectName('NoteEditDialog')
        self.setWindowModality(Qt.ApplicationModal)
        self.resize(1200, 900)
        self.setModal(True)

        self._val_edit_list = []

        self._init_title()
        self._main_vertical_layout = self._create_main_vertical_layout()
        self._splitter             = self._create_splitter(self._main_vertical_layout)
        self._button_box           = self._create_button_box(self._main_vertical_layout)
        self._left_widget          = self._create_left_widget(self._splitter)
        self._grid_layout          = self._create_grid(self._left_widget)

        # self._init_id_edit()
        # self._init_cat_combo()
        # self._init_title_text()
        # self._init_text_edit()
        self._preview = self._create_preview(self._splitter)

        # self._preview_updater = FastPreviewUpdater(self)

        QObject.connect(self._button_box, SIGNAL('accepted()'), self.accept)
        QObject.connect(self._button_box, SIGNAL('rejected()'), self.reject)
        QMetaObject.connectSlotsByName(self)

        #self.showMaximized()

    def _init_title(self):
        #title = "New Contact" if self._note.is_empty() else "Edit Contact"
        title = 'Edit Contact'
        self.setWindowTitle(
            QApplication.translate(
                'ContactEditDialog', title, None, QApplication.UnicodeUTF8))

    def _create_main_vertical_layout(self):
        layout = QVBoxLayout(self)
        layout.setSizeConstraint(QLayout.SetDefaultConstraint)
        layout.setObjectName('main_vertical_layout')
        return layout

    def _create_splitter(self, outer_layout):
        splitter = QSplitter(self)
        splitter.setOrientation(Qt.Horizontal)
        splitter.setObjectName('splitter')
        outer_layout.addWidget(splitter)
        return splitter

    def _create_left_widget(self, parent):
        left_widget = QWidget(parent)
        left_widget.setObjectName("left widget")
        return left_widget

    def _create_grid(self, parent):
        grid_layout = QGridLayout(parent)
        grid_layout.setObjectName('gridLayout')
        row = 0
        for attr in self._contact.iter_attributes():
            for fact in self._contact.get_facts(attr.name):
                self._add_row_to_grid(row, fact, attr, grid_layout, parent)
                row += 1
        return grid_layout

    def _add_row_to_grid(self, row, fact, attr, grid_layout, parent):
        val = self._contacts_model.get_fact_value(fact, attr)

        attr_label = QLabel(parent)
        attr_label.setObjectName('label{}'.format(row))
        attr_label.setText(attr.name + ':')
        grid_layout.addWidget(attr_label, row, 0, 1, 1)

        val_edit = QLineEdit(parent)
        val_edit.setObjectName('val_edit{}'.format(row))
        val_edit.setText(val)
        val_edit.textChanged.connect(self.on_text_changed)
        val_edit.fact = fact
        val_edit.attr = attr

        grid_layout.addWidget(val_edit, row, 1, 1, 1)
        self._val_edit_list.append((fact, attr, val_edit))

    def _create_button_box(self, outer_layout):
        button_box = QDialogButtonBox(self)
        button_box.setOrientation(Qt.Horizontal)
        button_box.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)
        button_box.setObjectName('button_box')
        outer_layout.addWidget(button_box)
        return button_box

    def _create_preview(self, parent):
        preview = QTextEdit(parent)
        preview.setObjectName('preview')
        return preview

    def on_text_changed(self):
        sender = self.sender()
        fact = sender.fact
        attr = sender.attr

        contact = self._contact.copy()
        for fact, attr, val_edit in self._val_edit_list:
            if not isinstance(attr.value_type, Ref):
                text = val_edit.text()
                fact = contact.get_fact(fact.serial)
                if text != fact.value:
                    fact.value = text
                    self._fact_changes[fact.serial] = fact

        html_creator = ContactHtmlCreator(contact, self._contacts_model)
        html_text = html_creator.create_html_text()

        self._preview.setText(html_text)

    @property
    def fact_changes(self):
        return self._fact_changes

    @property
    def date_changes(self):
        return self._date_changes
