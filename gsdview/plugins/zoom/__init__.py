# -*- coding: utf-8 -*-

### Copyright (C) 2008-2010 Antonio Valentino <a_valentino@users.sf.net>

### This file is part of GSDView.

### GSDView is free software; you can redistribute it and/or modify
### it under the terms of the GNU General Public License as published by
### the Free Software Foundation; either version 2 of the License, or
### (at your option) any later version.

### GSDView is distributed in the hope that it will be useful,
### but WITHOUT ANY WARRANTY; without even the implied warranty of
### MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
### GNU General Public License for more details.

### You should have received a copy of the GNU General Public License
### along with GSDView; if not, write to the Free Software
### Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA.


'''Zoom tool.'''

__author__   = 'Antonio Valentino <a_valentino@users.sf.net>'
__date__     = '$Date$'
__revision__ = '$Revision$'

__all__ = ['ZoomTool', 'init', 'close',
           'name','version', 'short_description','description',
           'author', 'author_email', 'copyright', 'license_type',
           'website', 'website_label',
]


from zoom.info import *
from zoom.info import __version__, __requires__


def init(app):
    from PyQt4 import QtCore
    from zoom.core import ZoomTool

    zoomTool = ZoomTool(app)
    app.imagemenu.addSeparator()
    app.imagemenu.addActions(zoomTool.actions.actions())
    app.addToolBar(zoomTool.toolbar)

    zoomTool.actions.setEnabled(False)
    zoomTool.connect(app.mdiarea,
                     QtCore.SIGNAL('subWindowActivated(QMdiSubWindow*)'),
                     lambda w: zoomTool.actions.setEnabled(True))
    zoomTool.connect(app, QtCore.SIGNAL('subWindowClosed()'),
                     lambda: zoomTool.actions.setEnabled(
                                    bool(app.mdiarea.activeSubWindow())))


def close(app):
    saveSettings(app.settings)

def loadSettings(settings):
    pass

def saveSettings(settings):
    pass
