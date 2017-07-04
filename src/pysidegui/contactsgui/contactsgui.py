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
# Programm erhalten haben. Wenn nicht, siehe <http://www.gnu.org/licenses/>.

from collections import OrderedDict
from PySide.QtGui import QInputDialog
from pysidegui.modelgui import ModelGui
from pysidegui.contactsgui.contacteditdialog import ContactEditDialog
from contacts.repository import Repository
from contacts.contactmodel import ContactModel, ContactID
from pysidegui.htmlview import ContactHtmlCreator


class ContactsGui(ModelGui):

    def __init__(self, context):
        self._contact_repo = Repository(context.contacts_db_path)
        self._contact_repo.reload()
        date_changes, fact_changes = self._contact_repo.aggregate_revisions()
        self._contact_model = ContactModel(date_changes, fact_changes)

    def new_object(self, frame):
        contact_model = self._contact_model
        type_map = OrderedDict((x.type_name, x) for x in contact_model.iter_object_classes())
        type_name, ok = QInputDialog.getItem(frame, 'new', 'select a type', list(type_map.keys()), editable=False)
        if ok:
            contact_cls = type_map[type_name]
            new_contact = self._contact_model.create_contact(contact_cls.type_id)

            dlg = ContactEditDialog(frame, new_contact, contact_model)
            if dlg.exec() == dlg.Accepted:
                contact_model.add_changes(
                    date_changes=dlg.date_changes,
                    fact_changes=dlg.fact_changes
                )
                return new_contact.id

    def edit_object(self, obj_id, frame):
        contact_id = obj_id
        contact = self._contact_model.get(contact_id)
        dlg = ContactEditDialog(frame, contact, self._contact_model)
        if dlg.exec() != dlg.Accepted:
            return False
        if not dlg.check_contact_with_message_box():
            return False

        self._contact_model.add_changes(
            date_changes=dlg.date_changes,
            fact_changes=dlg.fact_changes
        )
        return True

    def save_all(self):
        comment, ok = QInputDialog.getText(None, 'Commit', 'please enter a comment')
        if not ok:
            return False

        self._contact_model.commit(comment, self._contact_repo)
        return True

    def revert_change(self):
        date_changes, fact_changes = self._contact_repo.aggregate_revisions()
        self._contact_model = ContactModel(date_changes, fact_changes)
        return True

    def get_html_text(self, obj_id) -> str:
        contact_id = obj_id
        contact = self._contact_model.get(contact_id)
        html_text = ContactHtmlCreator(contact, self._contact_model).create_html_text()
        return html_text

    def exists_uncommited_changes(self) -> bool:
        return self._contact_model.exists_uncommited_changes()

    def get_id_from_href(self, href_str: str) -> id:
        contact_id = ContactID.create_from_string(href_str)
        return contact_id

    def iter_sorted_ids_from_keywords(self, keywords):
        filtered_contacts = self._iter_filtered_contacts(keywords)
        sorted_contacts = sorted(filtered_contacts, key=lambda x: x.id)
        for contact in sorted_contacts:
            yield contact.id

    def _iter_filtered_contacts(self, keywords):
        for contact in self._contact_model.iter_objects():
            if contact.contains_all_keywords(keywords):
                yield contact

    def get_object_title(self, obj_id) -> str:
        contact = self._contact_model.get(obj_id)
        return contact.title
