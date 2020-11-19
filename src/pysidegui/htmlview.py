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

from pathlib import Path
from typing import Tuple, Optional
from zipfile import ZipFile

from PySide2.QtCore import QEvent, QBuffer, QIODevice, QSize, Qt
from PySide2.QtGui import QHelpEvent, QImage, QPixmap
from PySide2.QtWidgets import QTextEdit, QToolTip


class HtmlView(QTextEdit):

    def __init__(self, parent):
        super().__init__(parent)
        self.zoomIn(range=1)
        self.click_link_observers = []
        self.setMouseTracking(True)
        self._tooltip_caches = {}  # path -> buf

    def event(self, event: QEvent):
        if event.type() == QEvent.ToolTip:
            help_event: QHelpEvent = event
            anchor = self.anchorAt(help_event.pos())
            if anchor:
                tooltip = self._get_tooltip(anchor)
                # html = "<img src='G:/app-data/cc-pim/icons/finn.ico'>Hallo</img>"
                QToolTip.showText(help_event.globalPos(), tooltip)
            else:
                QToolTip.hideText()
                event.ignore()
            return True

        return super().event(event)

    def _get_tooltip(self, anchor: str) -> str:
        if anchor not in self._tooltip_caches:
            self._tooltip_caches[anchor] = self._create_tooltip(anchor)
        return self._tooltip_caches[anchor]

    def _create_tooltip(self, anchor: str) -> str:
        path = Path(anchor)
        suffix = path.suffix
        if suffix in ('.txt', '.py', '.html', '.xml'):
            data = self._read_file(path)
            if data:
                file_buf = data.decode('utf-8')
                if suffix == '.html':
                    return file_buf
                else:
                    return f'<pre>{file_buf}</pre>'
        elif suffix in ('.png', '.jpg'):
            image = self._read_image(path)
            if image:
                buffer = QBuffer()
                buffer.open(QIODevice.WriteOnly)
                pixmap = QPixmap.fromImage(image)
                pixmap.save(buffer, "PNG")
                data = bytes(buffer.data().toBase64()).decode()
                return f'<img src="data:image/png;base64,{data}">'

        return f'<p>{anchor}</p>'

    def _read_image(self, path: Path) -> Optional[QImage]:
        data = self._read_file(path)
        if data:
            image = QImage()
            image.loadFromData(data, path.suffix[1:])
            max_size = QSize(600, 400)
            image_size = image.size()
            if image_size.width() > max_size.width() or image_size.height() > max_size.height():
                image = image.scaled(max_size, Qt.AspectRatioMode.KeepAspectRatio)
            return image

    def _read_file(self, path: Path) -> Optional[bytes]:
        try:
            if path.exists():
                return path.open('rb').read()
            else:
                zip_fpath, zipped_filename = self._split_zip_path(path)
                if zip_fpath:
                    with ZipFile(zip_fpath, 'r') as zip_file:
                        return zip_file.read(zipped_filename)
        except OSError:
            pass
        except PermissionError:
            pass

    @staticmethod
    def _split_zip_path(path: Path) -> Tuple[Optional[Path], Optional[str]]:
        p = path
        while p:
            if p.suffix == '.zip':
                n = len(p.parts)
                return p, '/'.join(path.parts[n:])
            p = p.parent
        return None, None

    def mousePressEvent(self, event):
        pos = event.pos()
        href_str = self.anchorAt(pos)
        super().mousePressEvent(event)

        # print('mouse-presse-event: pos: {}, anchor: {}'.format(pos, href_str))
        if href_str:
            for observer in self.click_link_observers:
                observer(href_str)

    def set_text(self, text: str) -> None:
        self._tooltip_caches.clear()
        super().setText(text)
