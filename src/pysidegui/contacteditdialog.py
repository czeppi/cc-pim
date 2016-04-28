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

from collections import OrderedDict
from PySide.QtGui import (QComboBox, QDialog, QDialogButtonBox, QGridLayout, QInputDialog, QLabel, QLayout,
                          QLineEdit, QPushButton, QSplitter, QTextEdit, QVBoxLayout, QWidget)
from PySide.QtCore import Qt
from modeling.contactmodel import ContactHtmlCreator
from modeling.basetypes import Ref
from modeling.repository import Fact


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

        self.setObjectName('ContactEditDialog')
        self.setWindowModality(Qt.ApplicationModal)
        self.resize(800, 600)
        self.setModal(True)

        self._init_title()
        self._main_vertical_layout = self._create_main_vertical_layout()
        self._splitter             = self._create_splitter(self._main_vertical_layout)
        self._button_box           = self._create_button_box(self._main_vertical_layout)
        self._left_widget          = self._create_left_widget(self._splitter)


        self._grid_layout          = self._create_grid_layout(self._left_widget)
        self._add_fact_button      = self._create_add_fact_button(self._left_widget)
        self._left_layout          = self._create_left_layout(self._grid_layout, self._add_fact_button)
        self._preview              = self._create_preview(self._splitter)

        self._fill_grid()
        self._left_widget.setLayout(self._left_layout)

        self._button_box.accepted.connect(self.accept)
        self._button_box.rejected.connect(self.reject)

    def _init_title(self):
        type_lower_name = self._contact.type_name
        type_name = type_lower_name[0].upper() + type_lower_name[1:]
        prefix = 'New' if self._contact_is_new else 'Edit'
        title = prefix + ' ' + type_name
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

    def _create_grid_layout(self, parent):
        grid_layout = QGridLayout()
        grid_layout.setObjectName('gridLayout')
        return grid_layout

    def _create_add_fact_button(self, parent):
        button = QPushButton('add', parent)
        button.clicked.connect(self.on_add_fact_button_clicked)
        return button

    def _create_left_layout(self, grid_layout, add_fact_button):
        vbox = QVBoxLayout()
        vbox.addLayout(grid_layout)
        vbox.addWidget(add_fact_button)
        vbox.addStretch()
        return vbox

    def _fill_grid(self):
        for attr in self._contact.iter_attributes():
            for fact in self._contact.get_facts(attr.name):
                self._add_row_to_grid(attr, fact)

    def _add_row_to_grid(self, attr, fact):
        parent = self._left_widget
        new_row = self._grid_layout.rowCount()
        attr_label = QLabel(parent)
        attr_label.setObjectName('label{}'.format(new_row))
        attr_label.setText(attr.name + ':')
        self._grid_layout.addWidget(attr_label, new_row, 0, 1, 1)

        if isinstance(attr.value_type, Ref):
            val_widget = self._create_val_combo(attr, fact, parent)
        else:
            val_widget = self._create_val_edit(attr, fact, parent)
        self._grid_layout.addWidget(val_widget, new_row, 1, 1, 1)

    def _create_val_combo(self, attr, fact, parent):
        combo = QComboBox(parent)
        #combo.setObjectName('val_combo{}'.format(row))

        # completer = QCompleter(word_list, self)
        # completer.setCaseSensitivity(Qt.CaseInsensitive)
        # combo.setCompleter(completer)
        # combo.setEditable(True)

        ref_map = self._create_ref_map(attr)
        combo.addItem('', 0)
        current_data = 0
        for title in sorted(ref_map.keys()):
            contact = ref_map[title]
            if fact is not None and contact.serial == int(fact.value):
                current_data = contact.serial
            combo.addItem(title, contact.serial)
        cur_index = combo.findData(current_data)
        combo.setCurrentIndex(cur_index)
        combo.currentIndexChanged.connect(self.on_combo_index_changed)
        combo.fact = fact
        combo.attr = attr
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

    def _create_val_edit(self, attr, fact, parent):
        val_edit = QLineEdit(parent)
        #val_edit.setObjectName('val_edit{}'.format(row))
        val = '' if fact is None else self._contacts_model.get_fact_value(fact, attr)
        val_edit.setText(val)
        val_edit.textChanged.connect(self.on_text_changed)
        val_edit.fact = fact
        val_edit.attr = attr
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
        text = val_edit.text()
        fact = val_edit.fact
        attr = val_edit.attr
        if fact is None:
            fact_serial = self._contacts_model.create_fact_serial()
            fact = Fact(fact_serial,
                        predicate_serial=attr.predicate_serial,
                        subject_serial=self._contact.serial,
                        value=None)
            val_edit.fact = fact
        if text != fact.value:
            fact.value = text
            self._fact_changes[fact.serial] = fact

        html_creator = ContactHtmlCreator(self._contact, self._contacts_model)
        html_text = html_creator.create_html_text()
        self._preview.setText(html_text)

    def on_combo_index_changed(self):
        val_combo = self.sender()
        cur_index = val_combo.currentIndex()
        cur_serial = val_combo.itemData(cur_index)

        fact = val_combo.fact
        attr = val_combo.attr
        if fact is None:
            fact_serial = self._contacts_model.create_fact_serial()
            fact = Fact(fact_serial,
                        predicate_serial=attr.predicate_serial,
                        subject_serial=self._contact.serial,
                        value=None)
            val_combo.fact = fact
        if cur_serial != fact.value:
            fact.value = cur_serial
            self._fact_changes[fact.serial] = fact

        html_creator = ContactHtmlCreator(self._contact, self._contacts_model)
        html_text = html_creator.create_html_text()
        self._preview.setText(html_text)

    def on_add_fact_button_clicked(self):
        print('on_add_fact_button_clicked')
        attr_map = OrderedDict((x.name, x) for x in self._contact.iter_attributes())
        attr_name, ok = QInputDialog.getItem(self, 'add fact', 'select an attribute', list(attr_map.keys()), editable=False)
        if ok:
            attr = attr_map[attr_name]
            self._add_row_to_grid(attr, fact=None)

    @property
    def fact_changes(self):
        return self._fact_changes

    @property
    def date_changes(self):
        return self._date_changes
