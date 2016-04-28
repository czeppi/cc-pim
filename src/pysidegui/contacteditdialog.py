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

from PySide.QtGui import (QApplication, QComboBox, QDialog, QDialogButtonBox, QGridLayout, QLabel, QLayout,
                          QLineEdit, QSplitter, QTextEdit, QVBoxLayout, QWidget)
from PySide.QtCore import Qt, QObject, QMetaObject, SIGNAL
from modeling.contactmodel import ContactHtmlCreator
from modeling.basetypes import Ref


class ContactEditDialog(QDialog):

    def __init__(self, parent, contact, contacts_model):
        super().__init__(parent, f=Qt.WindowMaximizeButtonHint)

        self._contact_is_new = not contacts_model.contains(contact.type_id, contact.serial)
        if self._contact_is_new:
            self._contact = contact
        else:
            self._contact = contact.copy()
        self._contacts_model = contacts_model
        self._date_changes = {}  # date_serial -> VagureDate
        self._fact_changes = {}  # fact_serial -> Fact

        self.setObjectName('NoteEditDialog')
        self.setWindowModality(Qt.ApplicationModal)
        self.resize(1200, 900)
        self.setModal(True)

        self._init_title()
        self._main_vertical_layout = self._create_main_vertical_layout()
        self._splitter             = self._create_splitter(self._main_vertical_layout)
        self._button_box           = self._create_button_box(self._main_vertical_layout)
        self._left_widget          = self._create_left_widget(self._splitter)
        self._grid_layout          = self._create_grid(self._left_widget)
        self._preview              = self._create_preview(self._splitter)

        self._button_box.accepted.connect(self.accept)
        self._button_box.rejected.connect(self.reject)

    def _init_title(self):
        title = 'New Contact' if self._contact_is_new else 'Edit Contact'
        self.setWindowTitle(title)

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

        attr_label = QLabel(parent)
        attr_label.setObjectName('label{}'.format(row))
        attr_label.setText(attr.name + ':')
        grid_layout.addWidget(attr_label, row, 0, 1, 1)

        if isinstance(attr.value_type, Ref):
            val_widget = self._create_val_combo(row, fact, attr, parent)
        else:
            val_widget = self._create_val_edit(row, fact, attr, parent)
        grid_layout.addWidget(val_widget, row, 1, 1, 1)

    def _create_val_combo(self, row, fact, attr, parent):
        combo = QComboBox(parent)
        combo.setObjectName('val_combo{}'.format(row))

        # completer = QCompleter(word_list, self)
        # completer.setCaseSensitivity(Qt.CaseInsensitive)
        # combo.setCompleter(completer)
        # combo.setEditable(True)

        ref_map = self._create_ref_map(attr)
        combo.addItem('', 0)
        current_data = 0
        for title in sorted(ref_map.keys()):
            contact = ref_map[title]
            if contact.serial == int(fact.value):
                current_data = contact.serial
            combo.addItem(title, contact.serial)
        cur_index = combo.findData(current_data)
        combo.setCurrentIndex(cur_index)
        combo.currentIndexChanged.connect(self.on_combo_index_changed)
        combo.fact = fact
        return combo

    def _create_ref_map(self, attr):
        ref = attr.value_type
        ref_type_id = ref.target_class.type_id
        ref_map = {}  # title -> obj
        for obj in self._contacts_model.iter_objects():
            if obj.type_id == ref_type_id:
                obj_title = obj.title
                if obj_title:
                    ref_map[obj_title] = obj
        return ref_map

    def _create_val_edit(self, row, fact, attr, parent):
        val_edit = QLineEdit(parent)
        val_edit.setObjectName('val_edit{}'.format(row))
        val = self._contacts_model.get_fact_value(fact, attr)
        val_edit.setText(val)
        val_edit.textChanged.connect(self.on_text_changed)
        val_edit.fact = fact
        return val_edit

    def _create_button_box(self, outer_layout):
        button_box = QDialogButtonBox(self)
        button_box.setOrientation(Qt.Horizontal)
        button_box.setStandardButtons(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
        button_box.setObjectName('button_box')
        outer_layout.addWidget(button_box)
        return button_box

    def _create_preview(self, parent):
        preview = QTextEdit(parent)
        preview.setObjectName('preview')
        return preview

    def on_text_changed(self):
        val_edit = self.sender()
        fact = val_edit.fact
        text = val_edit.text()
        if text != fact.value:
            fact.value = text
            self._fact_changes[fact.serial] = fact

        html_creator = ContactHtmlCreator(self._contact, self._contacts_model)
        html_text = html_creator.create_html_text()
        self._preview.setText(html_text)

    def on_combo_index_changed(self):
        val_combo = self.sender()
        fact = val_combo.fact
        cur_index = val_combo.currentIndex()
        cur_serial = val_combo.itemData(cur_index)
        if cur_serial != fact.value:
            fact.value = cur_serial
            self._fact_changes[fact.serial] = fact

        html_creator = ContactHtmlCreator(self._contact, self._contacts_model)
        html_text = html_creator.create_html_text()
        self._preview.setText(html_text)

    @property
    def fact_changes(self):
        return self._fact_changes

    @property
    def date_changes(self):
        return self._date_changes
