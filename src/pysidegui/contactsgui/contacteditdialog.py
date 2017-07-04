# Copyright (C) 2016  Christian Czepluch
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
# Programm erhalten haben. Wenn nicht, siehe <http://www.gnu.org/licenses/>.

import difflib
from collections import OrderedDict

from PySide.QtCore import Qt
from PySide.QtGui import (QCheckBox, QComboBox, QDialog, QDialogButtonBox, QGridLayout, QInputDialog, QLabel, QLayout,
                          QLineEdit, QMessageBox, QPushButton, QVBoxLayout)

from contacts.basetypes import Ref, Fact, VagueDate
from pysidegui.contactsgui.vaguedatedialog import VagueDateDialog


class ContactEditDialog(QDialog):

    def __init__(self, parent, contact, contacts_model):
        super().__init__(parent, f=Qt.WindowMaximizeButtonHint)

        self._contact_is_new = not contacts_model.contains(contact.id)
        if self._contact_is_new:
            self._contact = contact
        else:
            self._contact = contact.copy()
        self._contacts_model = contacts_model
        self._date_changes = {}  # date_serial -> VagureDate
        self._fact_changes = {}  # fact_serial -> Fact

        self.setWindowModality(Qt.ApplicationModal)
        self.resize(1200, 600)
        self.setModal(True)
        self._init_title()

        self._date_combos = []
        self._main_vertical_layout = self._create_main_vertical_layout()
        self._grid_layout          = self._create_grid_layout(self)
        self._add_fact_button      = self._create_add_fact_button(self)
        self._button_box           = self._create_button_box()

        if self._contact_is_new:
            self._fill_grid_new()
        else:
            self._fill_grid_edit()
        #self._left_widget.setLayout(self._left_layout)
        self._fill_main_layout()

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
        return layout

    def _create_grid_layout(self, parent):
        grid_layout = QGridLayout()
        return grid_layout

    def _create_add_fact_button(self, parent):
        button = QPushButton('add', parent)
        button.clicked.connect(self.on_add_fact_button_clicked)
        return button

    def _fill_main_layout(self):
        self._main_vertical_layout.addLayout(self._grid_layout)
        self._main_vertical_layout.addWidget(self._add_fact_button)
        self._main_vertical_layout.addStretch()
        self._main_vertical_layout.addWidget(self._button_box)

    def _fill_grid_edit(self):
        for attr in self._contact.iter_attributes():
            for fact in self._contact.get_facts(attr.name):
                self._add_row_to_grid(attr, fact)

    def _fill_grid_new(self):
        for attr in self._contact.iter_attributes():
            self._add_row_to_grid(attr, fact=None)

    def _add_row_to_grid(self, attr, fact):
        parent = self
        new_row = self._grid_layout.rowCount()
        attr_label = QLabel(parent)
        attr_label.setText(attr.name + ':')
        self._grid_layout.addWidget(attr_label, new_row, 0, 1, 1)

        row_widgets = RowWidgets(attr, fact, parent)

        if isinstance(attr.value_type, Ref):
            val_widget = self._create_val_combo(row_widgets)
        else:
            val_widget = self._create_val_edit(row_widgets)
        row_widgets.val_widget = val_widget
        self._grid_layout.addWidget(val_widget, new_row, 1, 1, 1)

        note_edit = self._create_note_edit(row_widgets)
        row_widgets.note_edit = note_edit
        self._grid_layout.addWidget(note_edit, new_row, 2, 1, 1)

        valid_checkbox = self._create_valid_checkbox(row_widgets)
        row_widgets.valid_checkbox = valid_checkbox
        self._grid_layout.addWidget(valid_checkbox, new_row, 3, 1, 1)

        from_combo = self._create_from_combo(row_widgets)
        row_widgets.from_combo = from_combo
        self._date_combos.append(from_combo)
        self._grid_layout.addWidget(from_combo, new_row, 4, 1, 1)

        from_button = self._create_from_button(row_widgets)
        row_widgets.from_button = from_button
        self._grid_layout.addWidget(from_button, new_row, 5, 1, 1)

        minus_label = QLabel(parent)
        minus_label.setText('-')
        self._grid_layout.addWidget(minus_label, new_row, 6, 1, 1)

        until_combo = self._create_until_combo(row_widgets)
        row_widgets.until_combo = until_combo
        self._date_combos.append(until_combo)
        self._grid_layout.addWidget(until_combo, new_row, 7, 1, 1)

        until_button = self._create_until_button(row_widgets)
        row_widgets.from_button = until_button
        self._grid_layout.addWidget(until_button, new_row, 8, 1, 1)

        remove_button = self._create_remove_button(row_widgets)
        row_widgets.remove_button = remove_button
        self._grid_layout.addWidget(remove_button, new_row, 9, 1, 1)

    def _create_val_combo(self, row):
        combo = QComboBox(row.parent)

        # completer = QCompleter(word_list, self)
        # completer.setCaseSensitivity(Qt.CaseInsensitive)
        # combo.setCompleter(completer)
        # combo.setEditable(True)

        ref_map = self._create_ref_map(row.attr)
        combo.addItem('', 0)
        current_data = 0
        for title in sorted(ref_map.keys()):
            contact = ref_map[title]
            if row.fact is not None and contact.serial == int(row.fact.value):
                current_data = contact.serial
            combo.addItem(title, contact.serial)
        cur_index = combo.findData(current_data)
        combo.setCurrentIndex(cur_index)
        combo.currentIndexChanged.connect(self.on_val_combo_index_changed)
        combo.row = row
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

    def _create_val_edit(self, row):
        val_edit = QLineEdit(row.parent)
        val = '' if row.fact is None else self._contacts_model.get_fact_value(row.fact)
        val_edit.setText(val)
        val_edit.textChanged.connect(self.on_text_changed)
        val_edit.row = row
        return val_edit

    def _create_note_edit(self, row):
        note_edit = QLineEdit(row.parent)
        text = '' if row.fact is None else row.fact.note
        note_edit.setText(text)
        note_edit.textChanged.connect(self.on_note_changed)
        note_edit.row = row
        return note_edit

    def _create_valid_checkbox(self, row):
        valid_checkbox = QCheckBox(row.parent)
        is_checked = True if row.fact is None else row.fact.is_valid
        valid_checkbox.setChecked(is_checked)
        valid_checkbox.stateChanged.connect(self.on_valid_changed)
        valid_checkbox.row = row
        return valid_checkbox

    def _create_from_combo(self, row):
        cur_serial = 0
        if row.fact is not None: # and row.fact.date_begin_serial is not None:
            cur_serial = row.fact.date_begin_serial
        return self._create_from_until_combo(row, cur_serial, self.on_from_combo_index_changed)

    def _create_until_combo(self, row):
        cur_serial = 0
        if row.fact is not None: # and row.fact.date_end_serial is not None:
            cur_serial = row.fact.date_end_serial
        return self._create_from_until_combo(row, cur_serial, self.on_until_combo_index_changed)

    def _create_from_until_combo(self, row, cur_serial, on_func):
        combo = QComboBox(row.parent)
        combo.setMinimumWidth(100)

        combo.addItem('', 0)
        sorted_date_serials = sorted(x.serial for x in self._contacts_model.iter_dates())
        for date_serial in sorted_date_serials:
            date = self._contacts_model.get_date(date_serial)
            item_text = self._create_vague_date_combo_text(date)
            combo.addItem(item_text, date.serial)

        cur_index = combo.findData(cur_serial)
        combo.setCurrentIndex(cur_index)
        combo.currentIndexChanged.connect(on_func)
        combo.row = row
        return combo

    def _create_from_button(self, row):
        return self._create_from_until_button(row, self.on_from_button_clicked)

    def _create_until_button(self, row):
        return self._create_from_until_button(row, self.on_until_button_clicked)

    def _create_from_until_button(self, row, on_func):
        button = QPushButton('*', row.parent)
        button.setFixedWidth(20)
        button.clicked.connect(on_func)
        button.row = row
        return button

    def _create_remove_button(self, row):
        remove_button = QPushButton('x', row.parent)
        remove_button.setFixedWidth(40)
        remove_button.clicked.connect(self.on_remove_button_clicked)
        remove_button.row = row
        return remove_button

    def _create_button_box(self):
        button_box = QDialogButtonBox(self)
        button_box.setOrientation(Qt.Horizontal)
        button_box.setStandardButtons(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
        return button_box

    def on_text_changed(self):
        val_edit = self.sender()
        text = val_edit.text()
        fact = self._get_or_create_fact(val_edit)
        if text != fact.value:
            fact.value = text
            self._fact_changes[fact.serial] = fact

    def _get_or_create_fact(self, widget):
        row = widget.row
        if row.fact is None:
            fact_serial = self._contacts_model.create_fact_serial()
            row.fact = Fact(fact_serial,
                            predicate_serial=row.attr.predicate_serial,
                            subject_serial=self._contact.serial,
                            value=None)
        return row.fact

    def on_val_combo_index_changed(self):
        val_combo = self.sender()
        cur_index = val_combo.currentIndex()
        cur_serial = val_combo.itemData(cur_index)
        fact = self._get_or_create_fact(val_combo)
        if cur_serial != fact.value:
            fact.value = cur_serial
            self._fact_changes[fact.serial] = fact

    def on_note_changed(self):
        note_edit = self.sender()
        text = note_edit.text()
        fact = self._get_or_create_fact(note_edit)
        if text != fact.note:
            fact.note = text
            self._fact_changes[fact.serial] = fact

    def on_valid_changed(self):
        valid_checkbox = self.sender()
        is_checked = valid_checkbox.isChecked()
        fact = self._get_or_create_fact(valid_checkbox)
        if is_checked != fact.is_valid:
            fact.is_valid = is_checked
            self._fact_changes[fact.serial] = fact

    def on_from_combo_index_changed(self):
        from_combo = self.sender()
        cur_index = from_combo.currentIndex()
        date_serial = from_combo.itemData(cur_index)
        fact = self._get_or_create_fact(from_combo)
        if date_serial != fact.date_begin_serial:
            fact.date_begin_serial = date_serial
            self._fact_changes[fact.serial] = fact

    def on_from_button_clicked(self):
        from_button = self.sender()
        row = from_button.row
        cur_index = row.from_combo.currentIndex()
        date_serial = row.from_combo.itemData(cur_index)
        vague_date = self._input_vague_date(date_serial)
        if vague_date is None:
            return
        self._date_changes[vague_date.serial] = vague_date

        if date_serial is None or date_serial == 0:
            self._add_date_to_all_date_combos(vague_date)
        else:
            self._update_all_date_combos(vague_date)
        cur_index = row.from_combo.findData(vague_date.serial)
        row.from_combo.setCurrentIndex(cur_index)

        fact = self._get_or_create_fact(from_button)
        if vague_date.serial != fact.date_begin_serial:
            fact.date_begin_serial = vague_date.serial
            self._fact_changes[fact.serial] = fact

    def _input_vague_date(self, date_serial):
        if date_serial is None or date_serial == 0:
            date = None
        elif date_serial in self._date_changes:
            date = self._date_changes[date_serial]
        else:
            date = self._contacts_model.get_date(date_serial)
        dlg = VagueDateDialog(self, date)
        if dlg.exec() == dlg.Accepted:
            try:
                if date_serial is None or date_serial == 0:
                    date_serial = self._contacts_model.create_date_serial()
                return VagueDate(dlg.text, serial=date_serial)
            except ValueError as err:
                msgBox = QMessageBox()
                msgBox.setText(str(err))
                msgBox.exec_()

    def _add_date_to_all_date_combos(self, new_date):
        item_text = self._create_vague_date_combo_text(new_date)
        for date_combo in self._date_combos:
            date_combo.addItem(item_text, userData=new_date.serial)

    def _update_all_date_combos(self, changed_date):
        item_text = self._create_vague_date_combo_text(changed_date)
        for date_combo in self._date_combos:
            cur_index = date_combo.findData(changed_date.serial)
            date_combo.setItemText(cur_index, item_text)

    def _create_vague_date_combo_text(self, vague_date):
        return '#{}: {}'.format(vague_date.serial, vague_date)

    def on_until_combo_index_changed(self):
        until_combo = self.sender()
        cur_index = until_combo.currentIndex()
        date_serial = until_combo.itemData(cur_index)
        fact = self._get_or_create_fact(until_combo)
        if date_serial != fact.date_end_serial:
            fact.date_end_serial = date_serial
            self._fact_changes[fact.serial] = fact

    def on_until_button_clicked(self):
        until_button = self.sender()
        row = until_button.row
        cur_index = row.until_combo.currentIndex()
        date_serial = row.until_combo.itemData(cur_index)
        vague_date = self._input_vague_date(date_serial)
        if vague_date is None:
            return
        self._date_changes[vague_date.serial] = vague_date

        if date_serial is None or date_serial == 0:
            self._add_date_to_all_date_combos(vague_date)
        else:
            self._update_all_date_combos(vague_date)
        cur_index = row.from_combo.findData(vague_date.serial)
        row.until_combo.setCurrentIndex(cur_index)

        fact = self._get_or_create_fact(until_button)
        if vague_date.serial != fact.date_end_serial:
            fact.date_end_serial = vague_date.serial
            self._fact_changes[fact.serial] = fact

    def on_remove_button_clicked(self):
        remove_button = self.sender()

    def on_add_fact_button_clicked(self):
        attr_map = OrderedDict((x.name, x) for x in self._contact.iter_attributes())
        attr_name, ok = QInputDialog.getItem(self, 'add fact', 'select an attribute', list(attr_map.keys()), editable=False)
        if ok:
            attr = attr_map[attr_name]
            self._add_row_to_grid(attr, fact=None)

    def check_contact_with_message_box(self):
        other_titles = list(self._iter_all_other_titles())
        if self._contact.title in  other_titles:
            msg_box = QMessageBox()
            msg = 'Title already exists!'
            msg_box.setText(msg)
            msg_box.exec_()
            return False

        similar_titles = difflib.get_close_matches(self._contact.title, other_titles, n=10, cutoff=0.6)
        if len(similar_titles) == 0:
            return True

        msg_box = QMessageBox()
        msg = 'Similar titles:\n\n' + '\n'.join(similar_titles)
        msg_box.setText(msg)
        msg_box.setInformativeText("Continue?")
        msg_box.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        msg_box.setDefaultButton(QMessageBox.Ok)
        ret = msg_box.exec_()
        if ret == QMessageBox.Ok:
            return True
        elif ret == QMessageBox.Cancel:
            return False
        else:
            raise Exception(str(ret))

    def _iter_all_other_titles(self):
        for contact in self._contacts_model.iter_objects():
            if contact.id != self._contact.id:
                yield contact.title

    @property
    def fact_changes(self):
        return self._fact_changes

    @property
    def date_changes(self):
        return self._date_changes


class RowWidgets:

    def __init__(self, attr, fact, parent):
        self.attr = attr
        self.fact = fact
        self.parent = parent
        self.val_widget = None
        self.note_edit = None
        self.valid_checkbox = None
        self.from_combo = None
        self.from_button = None
        self.until_combo = None
        self.until_button = None
        self.remove_button = None

    # def distribute_fact(self, fact):
    #     self.fact = fact
    #     if self.val_widget is not None:
    #         self.val_widget.fact = fact
    #     if self.note_edit is not None:
    #         self.note_edit.fact = fact
    #     if self.valid_checkbox is not None:
    #         self.valid_checkbox.fact = fact


