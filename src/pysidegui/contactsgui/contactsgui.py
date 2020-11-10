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

from collections import OrderedDict
from typing import Optional, Iterator, Iterable, Dict

from PySide2.QtGui import QIcon
from PySide2.QtWidgets import QInputDialog, QMainWindow

from contacts.contactmodel import ContactModel, ContactID, ContactType, Address, Person, Company, Contact
from contacts.repository import Repository
from pysidegui.contactsgui.contacteditdialog import ContactEditDialog
from pysidegui.globalitemid import GlobalItemID, GlobalItemTypes
from pysidegui.htmlview import ContactHtmlCreator
from pysidegui.modelgui import ModelGui, ResultItemData


class ContactsGui(ModelGui):

    def __init__(self, contact_model: ContactModel, contact_repo: Repository):
        self._contact_model = contact_model
        self._contact_repo = contact_repo

    def new_item(self, frame: QMainWindow, data_icons: Dict[str, QIcon],
                 css_buf: Optional[str]) -> Optional[GlobalItemID]:
        contact_model = self._contact_model
        type_map = OrderedDict((x.type_name.lower(), x) for x in contact_model.iter_object_classes())
        type_name, ok = QInputDialog.getItem(frame, 'new', 'select a type', list(type_map.keys()), editable=False)
        if ok:
            contact_cls = type_map[type_name]
            new_contact = self._contact_model.create_contact(contact_cls.contact_type)

            dlg = ContactEditDialog(frame, new_contact, contact_model, data_icons=data_icons)
            if dlg.exec() == dlg.Accepted:
                contact_model.add_changes(
                    date_changes=dlg.date_changes,
                    fact_changes=dlg.fact_changes
                )
                return _convert_contact2global_id(new_contact.id)

    def edit_item(self, glob_item_id: GlobalItemID, frame: QMainWindow, data_icons: Dict[str, QIcon],
                  css_buf: Optional[str]) -> bool:
        contact_id = _convert_global2contact_id(glob_item_id)
        contact = self._contact_model.get_contact(contact_id)
        dlg = ContactEditDialog(frame, contact, self._contact_model, data_icons=data_icons)
        if dlg.exec() != dlg.Accepted:
            return False
        if not dlg.check_contact_with_message_box():
            return False

        self._contact_model.add_changes(
            date_changes=dlg.date_changes,
            fact_changes=dlg.fact_changes
        )
        return True

    def save_all(self) -> bool:
        comment, ok = QInputDialog.getText(None, 'Commit', 'please enter a comment')
        if not ok:
            return False

        self._contact_model.commit(comment, self._contact_repo)
        return True

    def revert_change(self) -> bool:
        date_changes, fact_changes = self._contact_repo.aggregate_revisions()
        self._contact_model = ContactModel(date_changes, fact_changes)
        return True

    def get_html_text(self, glob_item_id: GlobalItemID) -> str:
        contact_id = _convert_global2contact_id(glob_item_id)
        contact = self._contact_model.get_contact(contact_id)
        html_text = ContactHtmlCreator(contact, self._contact_model).create_html_text()
        return html_text

    def exists_uncommitted_changes(self) -> bool:
        return self._contact_model.exists_uncommitted_changes()

    def get_id_from_href(self, href_str: str) -> GlobalItemID:
        contact_id = ContactID.create_from_string(href_str)
        return _convert_contact2global_id(contact_id)

    def iter_sorted_filtered_items(self, search_words: Iterable[str],
                                   filter_category: str,
                                   filter_files_state: str) -> Iterator[ResultItemData]:
        yield from sorted(
            self._iter_filtered_items(
                search_words, filter_category, filter_files_state),
            key=lambda x: x.title)

    def _iter_filtered_items(self, search_words: Iterable[str],
                             filter_category: str,
                             filter_files_state: str) -> Iterator[ResultItemData]:
        for contact in self._contact_model.iter_objects():
            if contact.does_meet_the_criteria(search_words, filter_category):
                yield ResultItemData(
                    glob_id=_convert_contact2global_id(contact.id),
                    category=contact.contact_type.name.lower(),
                    title=contact.title,
                )

    @staticmethod
    def iter_categories() -> Iterator[str]:
        yield Person.type_name.lower()
        yield Company.type_name.lower()
        yield Address.type_name.lower()


def _convert_global2contact_id(glob_id: GlobalItemID) -> ContactID:
    type_name = glob_id.type.name
    contact_type = ContactType[type_name]
    return ContactID(contact_type, glob_id.serial)


def _convert_contact2global_id(contact_id: ContactID) -> GlobalItemID:
    type_name = contact_id.contact_type.name
    global_type = GlobalItemTypes[type_name]
    return GlobalItemID(global_type, contact_id.serial)
