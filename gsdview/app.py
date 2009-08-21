#!/usr/bin/env python

# -*- coding: UTF8 -*-

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

'''GUI front-end for the Geospatial Data Abstracton Library (GDAL).'''

__author__   = 'Antonio Valentino <a_valentino@users.sf.net>'
__date__     = '$Date$'
__revision__ = '$Revision$'


import os
import sys
import logging

from PyQt4 import QtCore, QtGui

from gsdview import info
from gsdview import utils
from gsdview import exectools
from gsdview import qt4support
from gsdview import graphicsview
from gsdview import pluginmanager

#from gsdview appsite import USERCONFIGDIR, SYSPLUGINSDIR  # @TODO: fix
from gsdview.widgets import AboutDialog, PreferencesDialog
from gsdview.exectools.qt4tools import Qt4ToolController
from gsdview.exectools.qt4tools import Qt4DialogLoggingHandler

#~ from gsdview import resources

# @TODO: move elsewhere (site.py ??)
# @NOTE: this should happen before any os.chdir
GSDVIEWROOT = os.path.dirname(os.path.abspath(__file__))
# @TODO: import from appsite
USERCONFIGDIR = os.path.expanduser(os.path.join('~', '.gsdview'))
SYSPLUGINSDIR = os.path.join(GSDVIEWROOT, 'plugins')

from mainwin import ItemModelMainWindow


class GSDView(ItemModelMainWindow): # MdiMainWindow #QtGui.QMainWindow):
    # @TODO:
    #   * plugin architecture (incomplete)
    #   * cache browser, cache cleanup
    #   * open internal product
    #   * stop button
    #   * disable actions when the external tool is running
    #   * stretching tool
    #   * /usr/share/doc/python-qt4-doc/examples/mainwindows/recentfiles.py

    '''Main window class for GSDView application.

    :attributes:

    - filedialog
    - aboutdialog
    - preferencedsdialog
    - progressbar
    - settings_submenu
    - settings
    - logger
    - cachedir
    - fileActions
    - settingsActions
    - helpActions

    - pluginmanager
    - backends

    - controller
    - montior

    - mdiarea           (inherited from MdiMainWindow)
    - datamodel         (inherited from ItemModelMainWindow)
    - treeview          (inherited from ItemModelMainWindow)

    '''

    def __init__(self, parent=None):
        logger = logging.getLogger('gsdview')

        logger.debug('Main window base classes initialization ...')
        QtGui.qApp.setWindowIcon(QtGui.QIcon(':/GSDView.png'))

        super(GSDView, self).__init__(parent)
        title = self.tr('GSDView Open Source Edition v. %1').arg(info.version)
        self.setWindowTitle(title)
        self.setObjectName('gsdview-mainwin')

        # GraphicsViewMonitor
        logger.debug('Setting up "monitor" component ...')
        self.monitor = graphicsview.GraphicsViewMonitor()

        # Dialogs
        logger.debug('Setting up file dialog ...')
        self.filedialog = QtGui.QFileDialog(self)
        self.filedialog.setFileMode(QtGui.QFileDialog.ExistingFile)
        self.filedialog.setViewMode(QtGui.QFileDialog.Detail)

        logger.debug('Setting up the about dialog ...')
        self.aboutdialog = AboutDialog(self)
        logger.debug('Setting up the preferences dialog ...')
        self.preferencesdialog = PreferencesDialog(self)
        self.connect(self.preferencesdialog, QtCore.SIGNAL('apply()'),
                     self.applySettings)

        # Progressbar
        logger.debug('Setting up the progress bar ...')
        self.progressbar = QtGui.QProgressBar(self)
        self.progressbar.setTextVisible(True)
        self.statusBar().addPermanentWidget(self.progressbar)
        self.progressbar.hide()

        logger.debug('Miscellanea setup ...')
        self.cachedir = None

        # Plugin Manager
        #self.plugins = {}
        self.backends = []
        self.pluginmanager = pluginmanager.PluginManager(self, SYSPLUGINSDIR)
        self.preferencesdialog.addPage(
                pluginmanager.PluginManagerGui(self.pluginmanager, self),
                QtGui.QIcon(':/plugin.svg'),
                label='Plugins')

        # Settings
        if not os.path.isdir(USERCONFIGDIR):
            os.makedirs(USERCONFIGDIR)

        # @TODO: fix filename
        logger.debug('Read application settings ...')
        #self.settings = QtCore.QSettings('gsdview-soft', 'gsdview', self)
        #self.settings = QtCore.QSettings(QtCore.QSettings.IniFormat,
        #                                 QtCore.QSettings.UserScope,
        #                                 'gsdview', 'gsdview', self)
        cfgfile = os.path.join(USERCONFIGDIR, 'gsdview.ini')
        self.settings = QtCore.QSettings(cfgfile,
                                         QtCore.QSettings.IniFormat,
                                         self)

        # Setup the log system and the external tools controller
        logger.debug('Complete logging setup...')
        # @TODO: logevel could be set from command line
        self.logger = self.setupLogging()

        logger.debug('Setting up external tol controller ...')
        self.controller = self.setupController(self.logger, self.statusBar(),
                                               self.progressbar)

        # Actions
        logger.debug('Setting up actions ...')
        self.setupActions()

        # File menu end toolbar
        self._addMenuFromActions(self.fileActions, self.tr('&File'))
        self._addToolBarFromActions(self.fileActions, self.tr('File toolbar'))

        # Setup plugins
        logger.debug(self.tr('Setup plugins ...'))
        self.setupPlugins()

        # Settings menu end toolbar
        logger.debug(self.tr('Settings menu setup ...'))
        menu = self._addMenuFromActions(self.settingsActions,
                                        self.tr('&Settings'))
        self._addToolBarFromActions(self.settingsActions,
                                    self.tr('Settings toolbar'))
        self.settings_submenu = QtGui.QMenu(self.tr('&View'))
        menu.addSeparator()
        menu.addMenu(self.settings_submenu)
        self.connect(self.settings_submenu, QtCore.SIGNAL('aboutToShow()'),
                     self.updateSettingsMenu)

        logger.debug(self.tr('Window menu setup ...'))
        self.menuBar().addMenu(self.windowmenu)

        # Help menu end toolbar
        logger.debug('Help menu setup ...')
        self._addMenuFromActions(self.helpActions, self.tr('&Help'))
        self._addToolBarFromActions(self.helpActions, self.tr('Help toolbar'))

        # @NOTE: the window state setup must happen after the plugins loading
        logger.info('Load settings ...')
        self.loadSettings() # @TODO: pass settings
        # @TODO: force the log level set from command line
        #self.logger.setLevel(level)

        self.statusBar().showMessage('Ready')

    ### Model/View utils ######################################################
    def currentGraphicsView(self):
        window = self.mdiarea.activeSubWindow()
        if window:
            widget = window.widget()
            if isinstance(widget, QtGui.QGraphicsView):
                return widget
        return None

    def itemContextMenu(self, pos):
        modelindex = self.treeview.indexAt(pos)
        if not modelindex.isValid():
            return
        # @TODO: check
        # @NOTE: set the current index so that action calback can retrieve
        #        the cottect item
        self.treeview.setCurrentIndex(modelindex)
        item = self.datamodel.itemFromIndex(modelindex)
        backend = self.pluginmanager.plugins[item.backend]
        menu = backend.itemContextMenu(item)
        if menu:
            menu.exec_(self.treeview.mapToGlobal(pos))

    ### Event handlers ########################################################
    def closeEvent(self, event):
        self.controller.stop_tool()
        # @TODO: whait for finished (??)
        # @TODO: save opened datasets (??)
        self.saveSettings()
        self.pluginmanager.save_settings(self.settings)
        self.closeAll()
        self.pluginmanager.reset()
        event.accept()

    def changeEvent(self, event):
        try:
            if event.oldState() == QtCore.Qt.WindowNoState:
                # save window size and position
                self.settings.beginGroup('mainwindow')
                self.settings.setValue('position', QtCore.QVariant(self.pos()))
                self.settings.setValue('size', QtCore.QVariant(self.size()))
                self.settings.endGroup()
                event.accept()
        except AttributeError:
            pass

    ### Setup helpers #########################################################
    def _setupFileActions(self):
        # @TODO: add a "close all" (items) action
        actionsgroup = QtGui.QActionGroup(self)

        # Open
        action = QtGui.QAction(QtGui.QIcon(':/open.svg'),
                               self.tr('&Open'), actionsgroup)
        action.setObjectName('open')
        action.setShortcut(self.tr('Ctrl+O'))
        action.setToolTip(self.tr('Open an existing file'))
        action.setStatusTip(self.tr('Open an existing file'))
        self.connect(action, QtCore.SIGNAL('triggered()'), self.openFile)
        actionsgroup.addAction(action)

        # Close
        action = QtGui.QAction(QtGui.QIcon(':/close.svg'),
                               self.tr('&Close'), actionsgroup)
        action.setObjectName('close')
        action.setShortcut(self.tr('Ctrl+W'))
        action.setToolTip(self.tr('Close the current file'))
        action.setStatusTip(self.tr('Close the current file'))
        self.connect(action, QtCore.SIGNAL('triggered()'), self.closeFile)
        actionsgroup.addAction(action)

        # Separator
        QtGui.QAction(actionsgroup).setSeparator(True)
        #action.setObjectName('separator')

        # Exit
        action = QtGui.QAction(QtGui.QIcon(':/quit.svg'),
                               self.tr('&Exit'), actionsgroup)
        action.setObjectName('exit')
        action.setShortcut(self.tr('Ctrl+X'))
        action.setToolTip(self.tr('Exit the program'))
        action.setStatusTip(self.tr('Exit the program'))
        self.connect(action, QtCore.SIGNAL('triggered()'), self.close)
        actionsgroup.addAction(action)

        return actionsgroup

    def _setupSettingsActions(self):
        actionsgroup = QtGui.QActionGroup(self)

        # Preferences
        action = QtGui.QAction(QtGui.QIcon(':/preferences.svg'),
                               self.tr('&Preferences'), actionsgroup)
        action.setObjectName('preferences')
        action.setToolTip(self.tr('Open the program preferences dialog'))
        action.setStatusTip(self.tr('Open the program preferences dialog'))
        self.connect(action, QtCore.SIGNAL('triggered()'),
                     self.showPreferencesDialog)
        actionsgroup.addAction(action)

        return actionsgroup

    def _setupHelpActions(self):
        actionsgroup = QtGui.QActionGroup(self)

        # About
        action = QtGui.QAction(QtGui.QIcon(':/about.svg'),
                               self.tr('&About'), actionsgroup)
        action.setObjectName('about')
        action.setToolTip(self.tr('Show program information'))
        action.setStatusTip(self.tr('Show program information'))
        self.connect(action, QtCore.SIGNAL('triggered()'),
                     self.aboutdialog.exec_)
        actionsgroup.addAction(action)

        # AboutQt
        action = QtGui.QAction(QtGui.QIcon(':/qt-logo.png'),
                               self.tr('About &Qt'), actionsgroup)
        action.setObjectName('aboutQt')
        action.setToolTip(self.tr('Show information about Qt'))
        action.setStatusTip(self.tr('Show information about Qt'))
        self.connect(action, QtCore.SIGNAL('triggered()'),
                     lambda: QtGui.QMessageBox.aboutQt(self))
        actionsgroup.addAction(action)

        return actionsgroup

    def setupActions(self):
        self.fileActions = self._setupFileActions()
        self.settingsActions = self._setupSettingsActions()
        self.helpActions = self._setupHelpActions()
        # @TODO: tree view actions: expand/collapse all, expand/collapse subtree

    def _addMenuFromActions(self, actions, name):
        menu = qt4support.actionGroupToMenu(actions, name, self)
        self.menuBar().addMenu(menu)
        return menu

    def _addToolBarFromActions(self, actions, name):
        toolbar = qt4support.actionGroupToToolbar(actions, name)
        self.addToolBar(toolbar)
        return toolbar

    def setupPlugins(self):
        # load backends
        module = __import__('gsdview.gdalbackend', fromlist=['gsdview'])
        self.pluginmanager.load_module(module, 'gdalbackend')

        # load settings
        self.pluginmanager.load_settings(self.settings)

        # save initial state
        self.pluginmanager.save_settings(self.settings)

    def setupLogging(self):
        logger = logging.getLogger('gsdview')    # 'gsdview' # @TODO: fix

        # move this to launch.py
        fmt = ('%(levelname)s: %(asctime)s %(filename)s line %(lineno)d in '
               '%(funcName)s: %(message)s')
        formatter = logging.Formatter(fmt)
        logfile = os.path.join(USERCONFIGDIR, 'gsdview.log')
        handler = logging.FileHandler(logfile, 'w')
        handler.setLevel(logging.DEBUG)
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        formatter = logging.Formatter('%(message)s')
        handler = Qt4DialogLoggingHandler(parent=self, dialog=None)
        handler.setLevel(logging.WARNING)
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        # set log level
        # @WARNING: duplicate loadSettings
        level = self.settings.value('preferences/loglevel',
                                    QtCore.QVariant('INFO'))
        level = level.toString()
        levelno = logging.getLevelName(str(level))
        if isinstance(levelno, int):
            logger.setLevel(levelno)
            logger.info('"%s" loglevel set' % level)
        else:
            logging.debug('invalid log level: "%s"' % level)

        return logger

    def setupController(self, logger, statusbar, progressbar):
        # @TODO: move to plugin (??)
        #~ handler = GdalOutputHandler(None, statusbar, progressbar)
        #~ tool = GdalAddOverviewDescriptor(stdout_handler=handler)

        # @TODO: rewrite and remove this workaround
        tool = exectools.GenericToolDescriptor('echo')  # dummy tool
        controller = Qt4ToolController(logger, parent=self)
        controller.tool = tool
        controller.connect(controller, QtCore.SIGNAL('finished()'),
                           self.processingDone)

        return controller

    ### Settings ##############################################################
    def _restoreWindowState(self, settings=None):
        if settings is None:
            settings = self.settings

        settings.beginGroup('mainwindow')
        try:
            position = settings.value('position')
            if not position.isNull():
                self.move(position.toPoint())
            size = settings.value('size')
            if not size.isNull():
                self.resize(size.toSize())
            else:
                # default size
                self.resize(800, 600)

            try:
                winstate = settings.value('winstate',
                                QtCore.QVariant(QtCore.Qt.WindowNoState))
                winstate, ok = winstate.toInt()
                if winstate != QtCore.Qt.WindowNoState:
                    winstate = qt4support.intToWinState[winstate]
                    self.setWindowState(winstate)
            except KeyError:
                logging.debug('unable to restore the window state',
                              exc_info=True)

            # State of toolbars ad docks
            state = settings.value('state')
            if not state.isNull():
                self.restoreState(state.toByteArray())
        finally:
            settings.endGroup()

    def _restoreFileDialogState(self, settings=None):
        if settings is None:
            settings = self.settings

        settings.beginGroup('filedialog')
        try:
            # state
            state = settings.value('state')
            if not state.isNull():
                try:
                    # QFileDialog.restoreState is new in Qt 4.3
                    self.filedialog.restoreState(state.toByteArray())
                except AttributeError:
                    logging.debug('unable to save the file dialog state')

            # workdir
            default = utils.default_workdir()
            workdir = settings.value('workdir', QtCore.QVariant(default))
            workdir = str(workdir.toString())
            workdir = os.path.expanduser(os.path.expandvars(workdir))
            self.filedialog.setDirectory(workdir)

            # history
            #history = settings.value('history')
            #if not history.isNull():
            #    self.filedialog.setHistory(history.toStringList())

            # sidebar urls
            try:
                # QFileDialog.setSidebarUrls is new in Qt 4.3
                sidebarurls = settings.value('sidebarurls')
                if not sidebarurls.isNull():
                    sidebarurls = sidebarurls.toStringList()
                    sidebarurls = [QtCore.QUrl(item) for item in sidebarurls]
                    self.filedialog.setSidebarUrls(sidebarurls)
            except AttributeError:
                logging.debug('unable to restore sidebar URLs of the file '
                              'dialog')
        finally:
            settings.endGroup()

    def loadSettings(self, settings=None):
        # @TODO: split app saveSettings frlm plugins one
        if settings is None:
            settings = self.settings

        # general
        self._restoreWindowState(settings)
        self._restoreFileDialogState(settings)

        settings.beginGroup('preferences')
        try:
            # log level
            level = settings.value('loglevel', QtCore.QVariant('INFO'))
            level = level.toString()
            levelno = logging.getLevelName(str(level))
            if isinstance(levelno, int):
                self.logger.setLevel(levelno)
                self.logger.debug('"%s" loglevel set' % level)
            else:
                logging.debug('invalid log level: "%s"' % level)

            default = os.path.join(USERCONFIGDIR, 'cache')
            cachedir = settings.value('cachedir', QtCore.QVariant(default))
            cachedir = str(cachedir.toString())
            self.cachedir = os.path.expanduser(os.path.expandvars(cachedir))
        finally:
            settings.endGroup()

        # cache
        # @TODO

        # plugins
        for plugin in self.pluginmanager.plugins.values():
            plugin.loadSettings(settings)

    def _saveWindowState(self, settings=None):
        if settings is None:
            settings = self.settings

        settings.beginGroup('mainwindow')
        try:
            # @TODO: check
            # @NOTE: workaround for silencing Qt warning
            winstate = int(self.windowState())
            settings.setValue('winstate', QtCore.QVariant(winstate))
            #settings.setValue('winstate', QtCore.QVariant(self.windowState()))

            if self.windowState() == QtCore.Qt.WindowNoState:
                settings.setValue('position', QtCore.QVariant(self.pos()))
                settings.setValue('size', QtCore.QVariant(self.size()))

            settings.setValue('state', QtCore.QVariant(self.saveState()))
        finally:
            settings.endGroup()

    def _saveFileDialogState(self, settings=None):
        if settings is None:
            settings = self.settings

        settings.beginGroup('filedialog')
        try:
            # state
            try:
                # QFileDialog.saveState is new in Qt 4.3
                state = self.filedialog.saveState()
                settings.setValue('state', QtCore.QVariant(state))
            except AttributeError:
                logging.debug('unable to save the file dialog state')

            # workdir
            # @NOTE: uncomment to preserve the session value
            #workdir = self.filedialog.directory()
            #workdir = settings.setValue('workdir', QtCore.QVariant(workdir))

            # history
            #settings.setValue('history',
            #                  QtCore.QVariant(self.filedialog.history()))

            # sidebar urls
            try:
                # QFileDialog.sidebarUrls is new in Qt 4.3
                sidebarurls = self.filedialog.sidebarUrls()
                if sidebarurls:
                    qsidebarurls = QtCore.QStringList()
                    for item in sidebarurls:
                        qsidebarurls.append(QtCore.QString(item.toString()))
                    settings.setValue('sidebarurls',
                                      QtCore.QVariant(qsidebarurls))
            except AttributeError:
                logging.debug('unable to save sidebar URLs of the file dialog')
        finally:
            settings.endGroup()

    def saveSettings(self, settings=None):
        if settings is None:
            settings = self.settings

        # general
        self._saveWindowState(settings)
        self._saveFileDialogState(settings)

        settings.beginGroup('preferences')
        try:
            level = QtCore.QVariant(logging.getLevelName(self.logger.level))
            settings.setValue('loglevel', QtCore.QVariant(level))

            # only changed via preferences
            #settings.setValue('cachedir', QtCore.QVariant(self.cachedir))
        finally:
            settings.endGroup()

        # @NOTE: cache preferences are only modified via preferences dialog

        for plugin in self.pluginmanager.plugins.values():
            #logging.debug('save %s plugin preferences' % plugin.name)
            plugin.saveSettings(settings)

    def updateSettingsMenu(self):
        self.settings_submenu.clear()
        menu = self.createPopupMenu()

        for action in menu.actions():
            if self.tr('toolbar') in action.text():
                self.settings_submenu.addAction(action)
        self.settings_submenu.addSeparator()
        for action in menu.actions():
            if self.tr('toolbar') not in action.text():
                self.settings_submenu.addAction(action)

    def applySettings(self):
        self.preferencesdialog.save(self.settings)
        self.loadSettings()

    def showPreferencesDialog(self):
        # @TODO: complete
        self.saveSettings()
        self.preferencesdialog.load(self.settings)
        if self.preferencesdialog.exec_():
            self.applySettings()

    ### File actions ##########################################################
    def openFile(self):
        # @TODO: allow multiple file selection
        if self.filedialog.exec_():
            filename = str(self.filedialog.selectedFiles()[0])
            if filename:
                for backendname in self.backends:
                    backend = self.pluginmanager.plugins[backendname]
                    try:
                        item = backend.openFile(filename)
                        if item:
                            self.datamodel.appendRow(item)
                            self.treeview.expand(item.index())
                            self.logger.debug('File "%s" opened with backend '
                                              '"%s"' % (filename, backendname))
                        else:
                            self.logger.info('file %s" already open' % filename)
                        break
                    except RuntimeError:
                        #self.logger.exception('exception caught')
                        self.logger.debug('Backend "%s" failed to open file '
                                          '"%s"' % (backendname, filename))
                else:
                    self.logger.error('Unable to open file "%s"' % filename)

    def closeFile(self):
        # @TODO: extend for multiple datasets
        #~ self.emit(QtCore.SIGNAL('closeGdalDataset()'))

        item = self.currentItem()
        if item:
            # find the toplevel item
            while item.parent():
                item = item.parent()

            try:
                #~ backend = self.pluginmanager.plugins[item.backend]
                #~ backend.closeFile(item)
                item.close()
            except AttributeError:
                self.datamodel.invisibleRootItem().removeRow(item.row())

        self.statusBar().showMessage('Ready.')

    def closeAll(self):
        root = self.datamodel.invisibleRootItem()
        while root.hasChildren():
            item = root.child(0)
            try:
                #~ backend = self.pluginmanager.plugins[item.backend]
                #~ backend.closeFile(item)
                item.close()
            except AttributeError:
                root.removeRow(item.row())

    ### Auxiliary methods ####################################################
    def updateProgressBar(self, fract):
        self.progressbar.show()
        self.progressbar.setValue(int(100.*fract))

    def processingDone(self):
        self.controller.reset_controller()
        try:
            if self.controller.subprocess.exitCode() != 0: # timeout 30000 ms
                msg = ('An error occurred during the quicklook generation.\n'
                       'Now close the dataset.')
                QtGui.QMessageBox.warning(self, '', msg)
                self.closeFile()   # @TODO: check
                return
        finally:
            self.progressbar.hide()
            self.statusBar().showMessage('Ready.')


if __name__ == '__main__':
    from gsdview.launch import main
    main()