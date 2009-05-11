### Copyright (C) 2008-2009 Antonio Valentino <a_valentino@users.sf.net>

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

'''Metadata viewer component for geo-datasets.'''

__author__   = 'Antonio Valentino <a_valentino@users.sf.net>'
__date__     = '$Date$'
__revision__ = '$Revision$'
__requires__ = []       # @TODO: move this to the info file

__all__ = ['MetadataViewer', 'init', 'close']


from info import *

from PyQt4 import QtCore

from core import MetadataViewer


__version__ = info.__version__


def init(mainwin):
    metadataviewer = MetadataViewer(mainwin)
    metadataviewer.setObjectName('metadataViewerPanel') # @TODO: check
    mainwin.addDockWidget(QtCore.Qt.BottomDockWidgetArea, metadataviewer)

    def setItemMetadata(item, metadataviewer=metadataviewer):
        if not item:
            metadataviewer.clear()
            return

        # @TODO: fix
        # @WARNING: this method contains backend specific code
        if item.backend != 'gdalbackend':
            logging.warning('only "gdalbackend" is supported by "overview" '
                            'plugin')
            return

        metadata = item.GetMetadata_List()
        metadataviewer.setMetadata(metadata)

    def onItemClicked(index, mainwin=mainwin):
        #if not mainwin.mdiarea.activeSubWindow():
        item = mainwin.datamodel.itemFromIndex(index)
        setItemMetadata(item)

    mainwin.connect(mainwin.treeview,
                    QtCore.SIGNAL('clicked(const QModelIndex&)'),
                    onItemClicked)

    def onSubWindowChanged(window=None, mainwin=mainwin):
        if not window:
            window = mainwin.mdiarea.activeSubWindow()
        if window:
            try:
                item = window.item
            except AttributeError:
                item = None
        else:
            item = mainwin.currentItem()

        setItemMetadata(item)

    mainwin.connect(mainwin.mdiarea,
                    QtCore.SIGNAL('subWindowActivated(QMdiSubWindow*)'),
                    onSubWindowChanged)

    mainwin.connect(mainwin, QtCore.SIGNAL('subWindowClosed()'),
                    onSubWindowChanged)


def close(mainwin):
    saveSettings(mainwin.settings)

def loadSettings(settings):
    pass

def saveSettings(settings):
    pass