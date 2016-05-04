#! /usr/bin/env python
#-*- coding: utf-8 -*-

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

from PySide.QtGui import QTextEdit


class HtmlView(QTextEdit):

    def __init__(self, parent):
        super().__init__(parent)
        self.click_link_observers = []

    def mousePressEvent(self, event):
        pos = event.pos()
        href_str = self.anchorAt(pos)
        super().mousePressEvent(event)

        #print('mouse-presse-event: pos: {}, anchor: {}'.format(pos, href_str))
        if href_str:
            for observer in self.click_link_observers:
                observer(href_str)
