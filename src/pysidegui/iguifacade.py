
class IGuiFacade:

    def new_object(self, frame):
        raise Exception('net yet implemented.')

    def edit_object(self, obj_id, frame):
        raise Exception('net yet implemented.')

    def save_all(self):
        raise Exception('net yet implemented.')

    def revert_change(self):
        raise Exception('net yet implemented.')

    def get_html_text(self, obj_id) -> str:
        raise Exception('net yet implemented.')

    def exists_uncommited_changes(self) -> bool:
        raise Exception('net yet implemented.')

    def get_id_from_href(self, href_str: str) -> id:
        raise Exception('net yet implemented.')

    def iter_sorted_ids_from_keywords(self, keywords):
        raise Exception('net yet implemented.')

    def _iter_filtered_contacts(self, keywords):
        raise Exception('net yet implemented.')

    def get_object_title(self, obj_id) -> str:
        raise Exception('net yet implemented.')
