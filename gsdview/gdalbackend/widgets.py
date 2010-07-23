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


'''Widgets and dialogs for GSDView.'''

__author__   = '$Author$'
__date__     = '$Date$'
__revision__ = '$Revision$'

import os
import logging

import numpy
from osgeo import gdal
from PyQt4 import QtCore, QtGui

from gsdview import qt4support
from gsdview.widgets import get_filedialog, FileEntryWidget

from gsdview.gdalbackend import gdalsupport


GDALInfoWidgetBase = qt4support.getuiform('gdalinfo', __name__)
class GDALInfoWidget(QtGui.QWidget, GDALInfoWidgetBase):

    def __init__(self, parent=None, flags=QtCore.Qt.Widget, **kwargs):
        super(GDALInfoWidget, self).__init__(parent, flags, **kwargs)
        self.setupUi(self)

        # Context menu actions
        qt4support.setViewContextActions(self.gdalDriversTableWidget)

        # @TODO: check for available info in gdal 1.5 and above
        try:
            self.gdalReleaseNameValue.setText(gdal.VersionInfo('RELEASE_NAME'))
            self.gdalReleaseDateValue.setText(gdal.VersionInfo('RELEASE_DATE'))
        except AttributeError:
            self.gdalVersionGroupBox.hide()

        self.updateCacheInfo()
        self.setGdalDriversTab()

    def setGdalDriversTab(self):
        self.gdalDriversNumValue.setText(str(gdal.GetDriverCount()))

        tablewidget = self.gdalDriversTableWidget
        tablewidget.verticalHeader().hide()

        hheader = tablewidget.horizontalHeader()
        #hheader.resizeSections(QtGui.QHeaderView.ResizeToContents)
        fontinfo = QtGui.QFontInfo(tablewidget.font())
        hheader.setDefaultSectionSize(10*fontinfo.pixelSize())

        sortingenabled = tablewidget.isSortingEnabled()
        tablewidget.setSortingEnabled(False)
        tablewidget.setRowCount(gdal.GetDriverCount())

        for row in range(gdal.GetDriverCount()):
            driver = gdal.GetDriver(row)
            # @TODO: check for available ingo in gdal 1.5 and above
            tablewidget.setItem(row, 0, QtGui.QTableWidgetItem(driver.ShortName))
            tablewidget.setItem(row, 1, QtGui.QTableWidgetItem(driver.LongName))
            tablewidget.setItem(row, 2, QtGui.QTableWidgetItem(driver.GetDescription()))
            tablewidget.setItem(row, 3, QtGui.QTableWidgetItem(str(driver.HelpTopic)))

            metadata = driver.GetMetadata()
            if metadata:
                tablewidget.setItem(row, 4, QtGui.QTableWidgetItem(str(metadata.pop(gdal.DMD_EXTENSION, ''))))
                tablewidget.setItem(row, 5, QtGui.QTableWidgetItem(str(metadata.pop(gdal.DMD_MIMETYPE, ''))))
                tablewidget.setItem(row, 6, QtGui.QTableWidgetItem(str(metadata.pop(gdal.DMD_CREATIONDATATYPES, ''))))

                data = metadata.pop(gdal.DMD_CREATIONOPTIONLIST, '')
                # @TODO: parse xml
                tableitem = QtGui.QTableWidgetItem(data)
                tableitem.setToolTip(data)
                tablewidget.setItem(row, 7, tableitem)

                metadata.pop(gdal.DMD_HELPTOPIC, '')
                metadata.pop(gdal.DMD_LONGNAME, '')

                metadatalist = ['%s=%s' % (k, v) for k, v in metadata.items()]
                tableitem = QtGui.QTableWidgetItem(', '.join(metadatalist))
                tableitem.setToolTip('\n'.join(metadatalist))
                tablewidget.setItem(row, 8, tableitem)

        tablewidget.setSortingEnabled(sortingenabled)
        tablewidget.sortItems(0, QtCore.Qt.AscendingOrder)

    def updateCacheInfo(self):
        self.gdalCacheMaxValue.setText('%.3f MB' % (gdal.GetCacheMax()/1024.**2))
        self.gdalCacheUsedValue.setText('%.3f MB' % (gdal.GetCacheUsed()/1024.**2))

    def showEvent(self, event):
        self.updateCacheInfo()
        QtGui.QWidget.showEvent(self, event)


GDALPreferencesPageBase = qt4support.getuiform('gdalpage', __name__)
class GDALPreferencesPage(QtGui.QWidget, GDALPreferencesPageBase):

    def __init__(self, parent=None, flags=QtCore.Qt.Widget, **kwargs):
        super(GDALPreferencesPage, self).__init__(parent, flags, **kwargs)
        self.setupUi(self)

        self.infoButton.setIcon(qt4support.geticon('info.svg', 'gsdview'))

        # Avoid promoted widgets
        DirectoryOnly = QtGui.QFileDialog.DirectoryOnly
        self.gdalDataDirEntryWidget = FileEntryWidget(mode=DirectoryOnly)
        self.optionsGridLayout.addWidget(self.gdalDataDirEntryWidget, 1, 1)
        self.gdalDataDirEntryWidget.setEnabled(False)
        self.connect(self.gdalDataCheckBox,
                     QtCore.SIGNAL('toggled(bool)'),
                     self.gdalDataDirEntryWidget,
                     QtCore.SLOT('setEnabled(bool)'))

        self.gdalDriverPathEntryWidget = FileEntryWidget(mode=DirectoryOnly)
        self.optionsGridLayout.addWidget(self.gdalDriverPathEntryWidget, 3, 1)
        self.gdalDriverPathEntryWidget.setEnabled(False)
        self.connect(self.gdalDriverPathCheckBox,
                     QtCore.SIGNAL('toggled(bool)'),
                     self.gdalDriverPathEntryWidget,
                     QtCore.SLOT('setEnabled(bool)'))

        self.ogrDriverPathEntryWidget = FileEntryWidget(mode=DirectoryOnly)
        self.optionsGridLayout.addWidget(self.ogrDriverPathEntryWidget, 4, 1)
        self.ogrDriverPathEntryWidget.setEnabled(False)
        self.connect(self.ogrDriverPathCheckBox,
                     QtCore.SIGNAL('toggled(bool)'),
                     self.ogrDriverPathEntryWidget,
                     QtCore.SLOT('setEnabled(bool)'))

        # info button
        self.connect(self.infoButton, QtCore.SIGNAL('clicked()'), self.showinfo)

        # Context menu actions
        qt4support.setViewContextActions(self.extraOptTableWidget)

        # standard options
        cachesize = gdal.GetCacheMax()
        self.cacheSpinBox.setValue(cachesize/1024**2)
        dialog = get_filedialog(self)
        for name in ('gdalDataDir', 'gdalDriverPath', 'ogrDriverPath'):
            widget = getattr(self, name + 'EntryWidget')
            widget.dialog = dialog
            widget.mode = QtGui.QFileDialog.Directory

        # extra options
        self._extraoptions = {}
        stdoptions = set(('GDAL_DATA', 'GDAL_SKIP', 'GDAL_DRIVER_PATH',
                          'OGR_DRIVER_PATH', 'GDAL_CACHEMAX', ''))

        extraoptions = gdalsupport.GDAL_CONFIG_OPTIONS.splitlines()
        extraoptions = [opt for opt in extraoptions if opt not in stdoptions]
        self.extraOptTableWidget.setRowCount(len(extraoptions))

        for row, key in enumerate(extraoptions):
            item = QtGui.QTableWidgetItem(key)
            item.setFlags(item.flags() ^ QtCore.Qt.ItemIsEditable)
            self.extraOptTableWidget.setItem(row, 0, item)
            value = gdal.GetConfigOption(key, '')
            item = QtGui.QTableWidgetItem(value)
            self.extraOptTableWidget.setItem(row, 1, item)
            if value:
                self._extraoptions[key] = value

        hheader = self.extraOptTableWidget.horizontalHeader()
        hheader.resizeSections(QtGui.QHeaderView.ResizeToContents)

    def showinfo(self):
        dialog = QtGui.QDialog(self)
        dialog.setWindowTitle(self.tr('GDAL info'))
        layout = QtGui.QVBoxLayout()
        layout.addWidget(GDALInfoWidget())

        buttonbox = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Close)
        dialog.connect(buttonbox, QtCore.SIGNAL('accepted()'),
                       dialog, QtCore.SLOT('accept()'))
        dialog.connect(buttonbox, QtCore.SIGNAL('rejected()'),
                       dialog, QtCore.SLOT('reject()'))
        layout.addWidget(buttonbox)

        dialog.setLayout(layout)
        buttonbox.setFocus()
        dialog.exec_()

    def load(self, settings):
        settings.beginGroup('gdal')
        try:

            # cache size
            cachesize = settings.value('GDAL_CACHEMAX')
            if not cachesize.isNull():
                cachesize, ok = cachesize.toULongLong()
                if ok:
                    self.cacheCheckBox.setChecked(True)
                    self.cacheSpinBox.setValue(cachesize/1024**2)
            else:
                # show the current value and disable the control
                cachesize = gdal.GetCacheMax()
                self.cacheSpinBox.setValue(cachesize/1024**2)
                self.cacheCheckBox.setChecked(False)

            # GDAL data dir
            datadir = settings.value('GDAL_DATA').toString()
            if datadir:
                self.gdalDataCheckBox.setChecked(True)
                self.gdalDataDirEntryWidget.setText(datadir)
            else:
                # show the current value and disable the control
                datadir = gdal.GetConfigOption('GDAL_DATA', '')
                self.gdalDataDirEntryWidget.setText(datadir)
                self.gdalDataCheckBox.setChecked(False)

            # GDAL_SKIP
            gdalskip = settings.value('GDAL_SKIP').toString()
            if gdalskip:
                self.skipCheckBox.setChecked(True)
                self.skipLineEdit.setText(gdalskip)
            else:
                # show the current value and disable the control
                gdalskip = gdal.GetConfigOption('GDAL_SKIP', '')
                self.skipLineEdit.setText(gdalskip)
                self.skipCheckBox.setChecked(False)

            # GDAL driver path
            gdaldriverpath = settings.value('GDAL_DRIVER_PATH').toString()
            if gdaldriverpath:
                self.gdalDriverPathCheckBox.setChecked(True)
                self.gdalDriverPathEntryWidget.setText(gdaldriverpath)
            else:
                # show the current value and disable the control
                gdaldriverpath = gdal.GetConfigOption('GDAL_DRIVER_PATH', '')
                self.gdalDriverPathEntryWidget.setText(gdaldriverpath)
                self.gdalDriverPathCheckBox.setChecked(False)

            # OGR driver path
            ogrdriverpath = settings.value('OGR_DRIVER_PATH').toString()
            if ogrdriverpath:
                self.ogrDriverPathCheckBox.setChecked(True)
                self.ogrDriverPathEntryWidget.setText(ogrdriverpath)
            else:
                # show the current value and disable the control
                ogrdriverpath = gdal.GetConfigOption('OGR_DRIVER_PATH', '')
                self.ogrDriverPathEntryWidget.setText(ogrdriverpath)
                self.ogrDriverPathCheckBox.setChecked(False)

            # @TODO: complete
            #~ gdal.GetConfigOption('CPL_DEBUG', 'OFF')
            #~ gdal.GetConfigOption('GDAL_PAM_ENABLED', "NULL")

            # extra options
            # @TODO

        finally:
            settings.endGroup()

    def save(self, settings):
        settings.beginGroup('gdal')
        try:

            # cache
            if self.cacheCheckBox.isChecked():
                value = self.cacheSpinBox.value() * 1024**2
                settings.setValue('GDAL_CACHEMAX', QtCore.QVariant(value))
            else:
                settings.remove('GDAL_CACHEMAX')

            # GDAL data dir
            if self.gdalDataCheckBox.isChecked():
                value = self.gdalDataDirEntryWidget.text()
                settings.setValue('GDAL_DATA', QtCore.QVariant(value))
            else:
                settings.remove('GDAL_DATA')

            # GDAL_SKIP
            if self.skipCheckBox.isChecked():
                value = self.skipLineEdit.text()
                settings.setValue('GDAL_SKIP', QtCore.QVariant(value))
            else:
                settings.remove('GDAL_SKIP')

            # GDAL driver path
            if self.gdalDriverPathCheckBox.isChecked():
                value = self.gdalDriverPathEntryWidget.text()
                settings.setValue('GDAL_DRIVER_PATH', QtCore.QVariant(value))
            else:
                settings.remove('GDAL_DRIVER_PATH')

            # OGR driver path
            if self.ogrDriverPathCheckBox.isChecked():
                value = self.ogrDriverPathEntryWidget.text()
                settings.setValue('OGR_DRIVER_PATH', QtCore.QVariant(value))
            else:
                settings.remove('OGR_DRIVER_PATH')

            # @TODO: complete
            #~ gdal.GetConfigOption('CPL_DEBUG', 'OFF')
            #~ gdal.GetConfigOption('GDAL_PAM_ENABLED', "NULL")

            # extra options
            # @TODO
        finally:
            settings.endGroup()


class MajorObjectInfoDialog(QtGui.QDialog):
    def __init__(self, gdalobj, parent=None, flags=QtCore.Qt.Widget, **kwargs):
        super(MajorObjectInfoDialog, self).__init__(parent, flags, **kwargs)
        if hasattr(self, 'setupUi'):
            self.setupUi(self)

        self._obj = gdalobj

        if hasattr(self, 'domainComboBox'):
            self.connect(self.domainComboBox,
                         QtCore.SIGNAL('activated(const QString&)'),
                         self.updateMetadata)

        # Contect menu
        qt4support.setViewContextActions(self.metadataTableWidget)

        # Init tabs
        self.updateMetadata()

    def _checkgdalobj(self):
        if not self._obj:
            raise ValueError('no GDAL object attached (self._obj is None).')

    @staticmethod
    def _setMetadata(tablewidget, metadatalist):
        qt4support.clearTable(tablewidget)
        if not metadatalist:
            return

        tablewidget.setRowCount(len(metadatalist))
        sortingenabled = tablewidget.isSortingEnabled()
        tablewidget.setSortingEnabled(False)

        for row, data in enumerate(metadatalist):
            name, value = data.split('=', 1)
            tablewidget.setItem(row, 0, QtGui.QTableWidgetItem(name))
            tablewidget.setItem(row, 1, QtGui.QTableWidgetItem(value))

        # Fix table header behaviour
        tablewidget.setSortingEnabled(sortingenabled)

    def resetMetadata(self, domain=''):
        self.metadataNumValue.setText('0')
        qt4support.clearTable(self.metadataTableWidget)

    def setMetadata(self, metadatalist):
        self.metadataNumValue.setText(str(len(metadatalist)))
        self._setMetadata(self.metadataTableWidget, metadatalist)

    def updateMetadata(self, domain=''):
        if self._obj is not None:
            domain = str(domain)    # it could be a QString
            metadatalist = self._obj.GetMetadata_List(domain)

        if metadatalist:
            self.setMetadata(metadatalist)
        else:
            self.resetMetadata()

    def reset(self):
        self.resetMetadata()

    def update(self):
        if self._obj is not None:
            self.updateMetadata()
        else:
            self.reset()


def _setupImageStructureInfo(widget, metadata):
    widget.compressionValue.setText(metadata.get('COMPRESSION', ''))
    widget.nbitsValue.setText(metadata.get('NBITS', ''))
    widget.interleaveValue.setText(metadata.get('INTERLEAVE', ''))
    widget.pixelTypeValue.setText(metadata.get('PIXELTYPE', ''))


HistogramConfigDialogBase = qt4support.getuiform('histoconfig', __name__)
class HistogramConfigDialog(QtGui.QDialog, HistogramConfigDialogBase):
    def __init__(self, parent=None, flags=QtCore.Qt.Widget, **kwargs):
        super(HistogramConfigDialog, self).__init__(parent, flags, **kwargs)
        self.setupUi(self)

        # Make it not resizable
        w = self.maximumSize().width()
        h = self.size().height()
        self.setMaximumSize(w, h)

        # Colors
        self._default_palette = self.minSpinBox.palette()
        self._error_palette = QtGui.QPalette(self._default_palette)

        color = QtGui.QColor(QtCore.Qt.red)
        self._error_palette.setColor(QtGui.QPalette.Text, color)
        color.setAlpha(50)
        self._error_palette.setColor(QtGui.QPalette.Base, color)

        self.connect(self.minSpinBox, QtCore.SIGNAL('editingFinished()'),
                     self.validate)
        self.connect(self.maxSpinBox, QtCore.SIGNAL('editingFinished()'),
                     self.validate)

    def validate(self):
        if self.minSpinBox.value() >= self.maxSpinBox.value():
            self.minSpinBox.lineEdit().setPalette(self._error_palette)
            self.maxSpinBox.lineEdit().setPalette(self._error_palette)
            return False
        self.minSpinBox.lineEdit().setPalette(self._default_palette)
        self.maxSpinBox.lineEdit().setPalette(self._default_palette)
        return True

    def setLimits(self, dtype):
        vmin = -2**15 - 0.5
        vmax = 2**16 - 0.5
        if dtype in (numpy.uint8, numpy.uint16, numpy.uint32, numpy.uint64):
            # Unsigned
            vmin = -0.5
            if dtype == numpy.uint8:
                vmax = 255.5
            else:
                vmax = 2**16 - 0.5
        elif dtype == numpy.int8:
            vmin = -128.5
            vmax = 127.5
        elif dtype == numpy.int16:
            vmax = 2**15 + 0.5

        self.minSpinBox.setMinimum(vmin)
        self.minSpinBox.setMaximum(vmax)
        self.maxSpinBox.setMinimum(vmin)
        self.maxSpinBox.setMaximum(vmax)


BandInfoDialogBase = qt4support.getuiform('banddialog', __name__)
class BandInfoDialog(MajorObjectInfoDialog, BandInfoDialogBase):

    def __init__(self, band=None, parent=None, flags=QtCore.Qt.Widget,
                 **kwargs):
        super(BandInfoDialog, self).__init__(band, parent, flags, **kwargs)

        self.connect(self.computeStatsButton, QtCore.SIGNAL('clicked()'),
                     self.computeStats)
        self.connect(self.computeHistogramButton, QtCore.SIGNAL('clicked()'),
                     self.computeHistogram)
        self.connect(self.approxStatsCheckBox, QtCore.SIGNAL('toggled(bool)'),
                     lambda chk: self.computeStatsButton.setEnabled(True))
        self.connect(self.customHistogramCheckBox,
                     QtCore.SIGNAL('toggled(bool)'),
                     lambda chk: self.computeHistogramButton.setEnabled(True))

        # Set tab icons
        geticon = qt4support.geticon
        self.tabWidget.setTabIcon(0, geticon('info.svg', 'gsdview'))
        self.tabWidget.setTabIcon(1, geticon('metadata.svg', __name__))
        self.tabWidget.setTabIcon(2, geticon('statistics.svg', __name__))
        self.tabWidget.setTabIcon(3, geticon('color.svg', __name__))

        # Context menu actions
        qt4support.setViewContextActions(self.histogramTableWidget)
        qt4support.setViewContextActions(self.colorTableWidget)

        if not hasattr(gdal.Band, 'GetDefaultHistogram'):
            self.histogramGroupBox.hide()
            self.statisticsVerticalLayout.addStretch()

        # @TODO: remove.
        # Tempoorary disable the button for custom histogram configuration
        self.customHistogramCheckBox.setEnabled(False)

        # Tabs
        if band:
            self.update()

    @property
    def band(self):
        return self._obj

    def setBand(self, band):
        self._obj = band
        if band is not None:
            # @TODO: check type
            self.update()
        else:
            self.reset()

    def reset(self):
        super(BandInfoDialog, self).reset()

        self.resetInfoTab()
        self.resetStatistics()
        self.resetHistogram()
        self.resetColorTable()

    def update(self):
        super(BandInfoDialog, self).update()

        self.updateInfoTab()
        self.updateStatistics()
        self.updateHistogram()
        self.updateColorTable()

    def resetImageStructure(self):
        _setupImageStructureInfo(self, {})

    def setImageStructure(self, metadata):
        if metadata is None:
            self.resetImageStructure()

        _setupImageStructureInfo(self, metadata)

    def updateImageStructure(self):
        if self.band is not None:
            metadata = self.band.GetMetadata('IMAGE_STRUCTURE')
        else:
            metadata = {}

        self.setImageStructure(metadata)

    def resetInfoTab(self):
        # Info
        self.descriptionValue.setText('')
        self.bandNumberValue.setText('')
        self.colorInterpretationValue.setText('')
        self.overviewCountValue.setText('0')
        self.hasArbitraryOverviewsValue.setText('')

        # @TODO: checksum
        #~ band.Checksum                   ??

        # Data
        self.xSizeValue.setText('0')
        self.ySizeValue.setText('0')
        self.blockSizeValue.setText('0')
        self.noDataValue.setText('')

        self.dataTypeValue.setText('')
        self.unitTypeValue.setText('')
        self.offsetValue.setText('0')
        self.scaleValue.setText('1')

        self.resetImageStructure()

    def updateInfoTab(self):
        if self.band is None:
            self.resetInfoTab()
            return

        band = self.band

        # Color interpretaion
        colorint = band.GetRasterColorInterpretation()
        colorint = gdal.GetColorInterpretationName(colorint)

        # Info
        self.descriptionValue.setText(band.GetDescription().strip())
        bandno = band.GetBand()
        self.bandNumberValue.setText(str(bandno))
        self.colorInterpretationValue.setText(colorint)
        self.overviewCountValue.setText(str(band.GetOverviewCount()))

        # @COMPATIBILITY: HasArbitraryOverviews requires GDAL >= 1.7
        if hasattr(gdal.Band, 'HasArbitraryOverviews'):
            hasArbitaryOvr = band.HasArbitraryOverviews()
            self.hasArbitraryOverviewsValue.setText(str(hasArbitaryOvr))
        else:
            self.hasArbitraryOverviewsValue.setText('')

        # @TODO: checksum
        #~ band.Checksum                   ??

        # Data
        self.xSizeValue.setText(str(band.XSize))
        self.ySizeValue.setText(str(band.YSize))
        self.blockSizeValue.setText(str(band.GetBlockSize()))
        self.noDataValue.setText(str(band.GetNoDataValue()))

        self.dataTypeValue.setText(gdal.GetDataTypeName(band.DataType))

        # @COMPATIBILITY: GetUnitType requires GDAL >= 1.7
        if hasattr(gdal.Band, 'GetUnitType'):
            unitType = band.GetUnitType()
            self.unitTypeValue.setText(str(unitType))
        else:
            self.unitTypeValue.setText('')
        self.offsetValue.setText(str(band.GetOffset()))
        self.scaleValue.setText(str(band.GetScale()))

        self.updateImageStructure()

    def resetStatistics(self):
        '''Reset statistics.'''

        value = self.tr('Not computed')
        self.minimumValue.setText(value)
        self.maximumValue.setText(value)
        self.meanValue.setText(value)
        self.stdValue.setText(value)

    def setStatistics(self, vmin, vmax, mean, stddev):
        self.minimumValue.setText(str(vmin))
        self.maximumValue.setText(str(vmax))
        self.meanValue.setText(str(mean))
        self.stdValue.setText(str(stddev))

    @qt4support.overrideCursor
    def updateStatistics(self):
        if self.band is None:
            self.resetStatistics()
            return

        # @NOTE: the band.GetStatistics method called with the second argument
        #        set to False (no image rescanning) has been fixed in
        #        r19666_ (1.6 branch) and r19665_ (1.7 branch)
        #        see `ticket #3572` on `GDAL Trac`_.
        #
        # .. _r19666: http://trac.osgeo.org/gdal/changeset/19666
        # .. _r19665: http://trac.osgeo.org/gdal/changeset/19665
        # .. _`ticket #3572`: http://trac.osgeo.org/gdal/ticket/3572
        # .. _`GDAL Trac`: http://trac.osgeo.org/gdal

        if gdalsupport.hasFastStats(self.band):
            vmin, vmax, mean, stddev = self.band.GetStatistics(True, True)
            self.setStatistics(vmin, vmax, mean, stddev)
            self.computeStatsButton.setEnabled(False)
        else:
            self.resetStatistics()

    def resetHistogram(self):
        tablewidget = self.histogramTableWidget
        self.numberOfClassesValue.setText('0')
        qt4support.clearTable(tablewidget)

    def setHistogram(self, vmin, vmax, nbuckets, hist):
        self.numberOfClassesValue.setText(str(nbuckets))

        w = (vmax - vmin) / nbuckets

        tablewidget = self.histogramTableWidget
        tablewidget.setRowCount(nbuckets)

        for row in range(nbuckets):
            start = vmin + row * w
            stop = start + w
            tablewidget.setItem(row, 0,
                                QtGui.QTableWidgetItem(str(start)))
            tablewidget.setItem(row, 1,
                                QtGui.QTableWidgetItem(str(stop)))
            tablewidget.setItem(row, 2,
                                QtGui.QTableWidgetItem(str(hist[row])))

        # @TODO: plotting

    def updateHistogram(self):
        if self.band is None:
            self.resetHistogram()

        if gdal.DataTypeIsComplex(self.band.DataType):
            self.computeHistogramButton.setEnabled(False)
            return
        else:
            self.computeHistogramButton.setEnabled(True)

        if gdal.VersionInfo() < '1700':
            # @TODO: check
            if self.computeHistogramButton.isEnabled() == False:
                # Histogram already computed
                hist = self.band.GetDefaultHistogram()
            else:
                hist = None
        else:
            # @WARNING: causes a crash in GDAL < 1.7.0 (r18405)
            # @SEEALSO: http://trac.osgeo.org/gdal/ticket/3304
            hist = self.band.GetDefaultHistogram(force=False)

        if hist:
            self.setHistogram(*hist)
            self.computeHistogramButton.setEnabled(False)
        else:
            self.resetHistogram()

    @staticmethod
    def _rgb2qcolor(red, green, blue, alpha=255):
        qcolor = QtGui.QColor()
        qcolor.setRgb(red, green, blue, alpha)
        return qcolor

    @staticmethod
    def _gray2qcolor(gray):
        qcolor = QtGui.QColor()
        qcolor.setRgb(gray, gray, gray)
        return qcolor

    @staticmethod
    def _cmyk2qcolor(cyan, magenta, yellow, black=255):
        qcolor = QtGui.QColor()
        qcolor.setCmyk(cyan, magenta, yellow, black)
        return qcolor

    @staticmethod
    def _hsv2qcolor(hue, lightness, saturation, a=0):
        qcolor = QtGui.QColor()
        qcolor.setHsv(hue, lightness, saturation, a)
        return qcolor

    def resetColorTable(self):
        self.ctInterpretationValue.setText('')
        self.colorsNumberValue.setText('')
        qt4support.clearTable(self.colorTableWidget)

    def setColorTable(self, colortable):
        if colortable is None:
            self.resetColorTable()
            return

        ncolors = colortable.GetCount()
        colorint = colortable.GetPaletteInterpretation()

        label = gdalsupport.colorinterpretations[colorint]['label']
        self.ctInterpretationValue.setText(label)
        self.colorsNumberValue.setText(str(ncolors))

        mapping = gdalsupport.colorinterpretations[colorint]['inverse']
        labels = [mapping[k] for k in sorted(mapping.keys())]
        labels.append('Color')

        tablewidget = self.colorTableWidget

        tablewidget.setRowCount(ncolors)
        tablewidget.setColumnCount(len(labels))

        tablewidget.setHorizontalHeaderLabels(labels)
        tablewidget.setVerticalHeaderLabels([str(i) for i in range(ncolors)])

        colors = gdalsupport.colortable2numpy(colortable)

        if colorint == gdal.GPI_RGB:
            func = BandInfoDialog._rgb2qcolor
        elif colorint == gdal.GPI_Gray:
            func = BandInfoDialog._gray2qcolor
        elif colorint == gdal.GPI_CMYK:
            func = BandInfoDialog._cmyk2qcolor
        elif colorint == gdal.GPI_HLS:
            func = BandInfoDialog._hsv2qcolor
        else:
            raise ValueError('invalid color intepretatin: "%s"' % colorint)

        brush = QtGui.QBrush()
        brush.setStyle(QtCore.Qt.SolidPattern)

        for row, color in enumerate(colors):
            for chan, value in enumerate(color):
                tablewidget.setItem(row, chan,
                                    QtGui.QTableWidgetItem(str(value)))
            qcolor = func(*color)
            brush.setColor(qcolor)
            item = QtGui.QTableWidgetItem()
            item.setBackground(brush)
            tablewidget.setItem(row, chan+1, item)

        hheader = tablewidget.horizontalHeader()
        hheader.resizeSections(QtGui.QHeaderView.ResizeToContents)

    def updateColorTable(self):
        if self.band is None:
            self.resetColorTable()
        else:
            colortable = self.band.GetRasterColorTable()

            if colortable is None:
                # Disable the color table tab
                self.tabWidget.setTabEnabled(3, False)
            else:
                self.tabWidget.setTabEnabled(3, True)
                self.setColorTable(colortable)

    @qt4support.overrideCursor # @TODO: remove
    def computeStats(self):
        self._checkgdalobj()
        #if None not in gdalsupport.GetCachedStatistics(self.band):
        #    return
        self.emit(QtCore.SIGNAL('computeStats(PyQt_PyObject)'), self.band)

        #~ logging.info('start statistics computation')

        #~ band = self.band
        #~ approx = self.approxStatsCheckBox.isChecked()
        #~ band.ComputeStatistics(approx)#, callback=None, callback_data=None)

        #~ # @COMPATIBILITY: workaround fo flagging statistics as computed
        #~ # @SEALSO: ticket #3572 on GDAL Trac
        #~ stats = band.GetStatistics(True, True)
        #~ for name, value in zip(gdalsupport.GDAL_STATS_KEYS, stats):
            #~ band.SetMetadataItem(name, str(value))

        #~ # @TODO: check
        #~ #if self.domainComboBox.currentText() == '':
        #~ #    self.updateMetadata()
        #~ logging.debug('statistics computation completed')
        #~ self.updateStatistics()

    @qt4support.overrideCursor # @TODO: remove
    def computeHistogram(self):
        self._checkgdalobj()
        self.emit(QtCore.SIGNAL('computeHistogram(PyQt_PyObject)'), self.band)
        #self.emit(QtCore.SIGNAL(
        #                'computeHistogram(PyQt_PyObject, int, int, int)'),
        #                band, hmin, nmax, nbuckets)

        #~ band = self.band
        #~ approx = self.approxStatsCheckBox.isChecked()
        #~ if self.customHistogramCheckBox.isChecked():
            #~ dialog = HistogramConfigDialog(self)

            #~ # @COMPATIBILITY: bug in GDAL 1.6.x line
            #~ # @WARNING: causes a crash in GDAL < 1.6.4 (r18405)
            #~ # @SEEALSO: http://trac.osgeo.org/gdal/ticket/3304
            #~ if gdal.VersionInfo() < '1640':
                #~ dialog.approxCheckBox.setChecked(True)
                #~ dialog.approxCheckBox.setEnabled(False)

            #~ from osgeo.gdal_array import GDALTypeCodeToNumericTypeCode
            #~ try:
                #~ dtype = GDALTypeCodeToNumericTypeCode(band.DataType)
            #~ except KeyError:
                #~ pass
            #~ else:
                #~ dialog.setLimits(dtype)

            #~ tablewidget = self.histogramTableWidget
            #~ if tablewidget.rowCount() > 0:
                #~ item = tablewidget.item(0, 0)
                #~ vmin = float(item.text())
                #~ item = tablewidget.item(tablewidget.rowCount() - 1 , 1)
                #~ vmax = float(item.text())

                #~ dialog.minSpinBox.setValue(vmin)
                #~ dialog.maxSpinBox.setValue(vmax)
                #~ dialog.nBucketsSpinBox.setValue(tablewidget.rowCount())

            #~ done = False
            #~ while not done:
                #~ ret = dialog.exec_()
                #~ if ret == QtGui.QDialog.Rejected:
                    #~ return
                #~ if dialog.validate() is False:
                    #~ msg = self.tr('The histogram minimum have been set to a '
                                  #~ 'value that is greater or equal of the '
                                  #~ 'histogram maximum.\n'
                                  #~ 'Please fix it.')
                    #~ QtGui.QMessageBox.warning(self, self.tr('WARNING!'), msg)
                #~ else:
                    #~ done = True

            #~ vmin = dialog.minSpinBox.value()
            #~ vmax = dialog.maxSpinBox.value()
            #~ nbuckets = dialog.nBucketsSpinBox.value()
            #~ include_out_of_range = dialog.outOfRangeCheckBox.isChecked()
            #~ approx = dialog.approxCheckBox.isChecked()

            #~ # @TODO: use callback for progress reporting
            #~ hist = qt4support.callExpensiveFunc(
                                #~ band.GetHistogram,
                                #~ vmin, vmax, nbuckets,
                                #~ include_out_of_range, approx)
                                #~ #callback=None, callback_data=None)

        #~ else:
            #~ # @TODO: use callback for progress reporting
            #~ hist = qt4support.callExpensiveFunc(band.GetDefaultHistogram)
                                                #~ #callback=None,
                                                #~ #callback_data=None)
            #~ vmin, vmax, nbuckets, hist = hist

        #~ self.computeHistogramButton.setEnabled(False)
        #~ self.setHistogram(vmin, vmax, nbuckets, hist)
        #~ self.updateStatistics() # @TODO: check


DatasetInfoDialogBase = qt4support.getuiform('datasetdialog', __name__)
class DatasetInfoDialog(MajorObjectInfoDialog, DatasetInfoDialogBase):

    def __init__(self, dataset=None, parent=None, flags=QtCore.Qt.Widget,
                 **kwargs):
        super(DatasetInfoDialog, self).__init__(dataset, parent, flags,
                                                **kwargs)

        # Set icons
        geticon = qt4support.geticon
        self.tabWidget.setTabIcon(0, geticon('info.svg', 'gsdview'))
        self.tabWidget.setTabIcon(1, geticon('metadata.svg', __name__))
        self.tabWidget.setTabIcon(2, geticon('gcp.svg', __name__))
        self.tabWidget.setTabIcon(3, geticon('driver.svg', __name__))
        self.tabWidget.setTabIcon(4, geticon('multiple-documents.svg',
                                  __name__))

        # Context menu actions
        qt4support.setViewContextActions(self.gcpsTableWidget)
        qt4support.setViewContextActions(self.driverMetadataTableWidget)
        qt4support.setViewContextActions(self.fileListWidget)

        if not hasattr(gdal.Dataset, 'GetFileList'):
            self.tabWidget.setTabEnabled(4, False)
            #self.tabWidget.removeTab(4)

        # Setup Tabs
        if dataset:
            self.update()

    @property
    def dataset(self):
        return self._obj

    def setDataset(self, dataset):
        self._obj = dataset
        if dataset is not None:
            # @TODO: check type
            self.update()
        else:
            self.reset()

    def reset(self):
        super(DatasetInfoDialog, self).reset()

        self.resetInfoTab()
        self.resetDriverTab()
        self.resetGCPs()
        self.resetFilesTab()

    def update(self):
        super(DatasetInfoDialog, self).update()

        self.updateInfoTab()
        self.updateDriverTab()
        self.updateGCPs()
        self.updateFilesTab()

    def resetImageStructure(self):
        _setupImageStructureInfo(self, {})

    def setImageStructure(self, metadata):
        if metadata is None:
            self.resetImageStructure()

        _setupImageStructureInfo(self, metadata)

    def updateImageStructure(self):
        if self.dataset is not None:
            metadata = self.dataset.GetMetadata('IMAGE_STRUCTURE')
        else:
            metadata = {}

        self.setImageStructure(metadata)

    def resetInfoTab(self):
        self.descriptionValue.setText('')
        self.rasterCountValue.setText('0')
        self.xSizeValue.setText('0')
        self.ySizeValue.setText('0')

        self.projectionValue.setText('')
        self.projectionRefValue.setText('')

        self.resetImageStructure()

        self.xOffsetValue.setText('0')
        self.yOffsetValue.setText('0')
        self.a11Value.setText('1')
        self.a12Value.setText('0')
        self.a21Value.setText('0')
        self.a22Value.setText('1')

    def updateInfoTab(self):
        if self.dataset is None:
            self.resetInfoTab()
            return

        dataset = self.dataset
        description = os.path.basename(dataset.GetDescription())
        self.descriptionValue.setText(description)
        self.descriptionValue.setCursorPosition(0)
        self.rasterCountValue.setText(str(dataset.RasterCount))
        self.xSizeValue.setText(str(dataset.RasterXSize))
        self.ySizeValue.setText(str(dataset.RasterYSize))

        self.projectionValue.setText(dataset.GetProjection())
        self.projectionRefValue.setText(dataset.GetProjectionRef())

        self.updateImageStructure()

        xoffset, a11, a12, yoffset, a21, a22 = dataset.GetGeoTransform()
        self.xOffsetValue.setText(str(xoffset))
        self.yOffsetValue.setText(str(yoffset))
        self.a11Value.setText(str(a11))
        self.a12Value.setText(str(a12))
        self.a21Value.setText(str(a21))
        self.a22Value.setText(str(a22))

    def resetDriverTab(self):
        self.driverShortNameValue.setText('')
        self.driverLongNameValue.setText('')
        self.driverDescriptionValue.setText('')
        self.driverHelpTopicValue.setText('')
        self.driverMetadataNumValue.setText('0')
        qt4support.clearTable(self.driverMetadataTableWidget)

    def setDriverTab(self, driver):
        self.resetDriverTab()

        self.driverShortNameValue.setText(driver.ShortName)
        self.driverLongNameValue.setText(driver.LongName)
        self.driverDescriptionValue.setText(driver.GetDescription())

        if driver.HelpTopic:
            link = '''<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0//EN" "http://www.w3.org/TR/REC-html40/strict.dtd">
<html><head><meta name="qrichtext" content="1" /><style type="text/css">
p, li { white-space: pre-wrap; }
</style></head><body style=" font-family:'DejaVu Sans'; font-size:10pt; font-weight:400; font-style:normal;">
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><a href="http://www.gdal.org/%s"><span style=" text-decoration: underline; color:#0000ff;">%s</span></a></p></body></html>''' % (driver.HelpTopic, driver.HelpTopic)
        else:
            link = str(driver.HelpTopic)

        self.driverHelpTopicValue.setText(link)

        metadatalist = driver.GetMetadata_List()
        if metadatalist:
            self.driverMetadataNumValue.setText(str(len(metadatalist)))
            self._setMetadata(self.driverMetadataTableWidget, metadatalist)

    def updateDriverTab(self):
        if self.dataset is None:
            self.resetDriverTab()
            return

        driver = self.dataset.GetDriver()
        self.setDriverTab(driver)

    def resetGCPs(self):
        tablewidget = self.gcpsTableWidget
        qt4support.clearTable(tablewidget)
        self.gcpsNumValue.setText('')
        self.gcpsProjectionValue.setText('')

    def setGCPs(self, gcplist, projection):
        self.resetGCPs()

        tablewidget = self.gcpsTableWidget

        self.gcpsProjectionValue.setText(projection)
        self.gcpsNumValue.setText(str(len(gcplist)))

        tablewidget.setRowCount(len(gcplist))
        tablewidget.setVerticalHeaderLabels([str(gcp.Id) for gcp in gcplist])
        sortingenabled = tablewidget.isSortingEnabled()
        tablewidget.setSortingEnabled(False)

        Item = QtGui.QTableWidgetItem
        for row, gcp in enumerate(gcplist):
            tablewidget.setItem(row, 0, Item(str(gcp.GCPPixel)))
            tablewidget.setItem(row, 1, Item(str(gcp.GCPLine)))
            tablewidget.setItem(row, 2, Item(str(gcp.GCPX)))
            tablewidget.setItem(row, 3, Item(str(gcp.GCPY)))
            tablewidget.setItem(row, 4, Item(str(gcp.GCPZ)))
            tablewidget.setItem(row, 5, Item(gcp.Info))
            #~ item.setToolTip(1, gcp.Info)

        # Fix table header behaviour
        tablewidget.setSortingEnabled(sortingenabled)

    def updateGCPs(self):
        if self.dataset is None:
            self.resetGCPs()
        else:
            # It seems there is a bug in GDAL that causes incorrect GCPs
            # handling when a subdatast is opened (a dataset is aready open)
            # @TODO: check and, if the case, file a ticket on
            #        http://www.gdal.org

            #self.setGCPs(dataset.GetGCPs(), dataset.GetGCPProjection())
            try:
                gcplist = self.dataset.GetGCPs()
            except SystemError:
                logging.debug('unable to read GCPs from dataset %s' %
                                    self.dataset.GetDescription())
                                    #, exc_info=True)
            else:
                if not gcplist:
                    # Disable the GCPs tab
                    self.tabWidget.setTabEnabled(2, False)
                else:
                    self.tabWidget.setTabEnabled(2, True)
                    self.setGCPs(gcplist, self.dataset.GetGCPProjection())

    def resetFilesTab(self):
        #qt4support.clearTable(self.fileListWidget) # @TODO: check
        self.fileListWidget.clear()

    def setFiles(self, files):
        self.tabWidget.setTabEnabled(4, True)

        for filename in files:
            self.fileListWidget.addItem(filename)

    def updateFilesTab(self):
        if self.dataset is not None:
            self.tabWidget.setTabEnabled(4, True)
            self.setFiles(self.dataset.GetFileList())
        else:
            self.resetFilesTab()
            self.tabWidget.setTabEnabled(4, False)

#~ class SubDatasetInfoDialog(DatasetInfoDialog):

    #~ def __init__(self, subdataset, parent=None, flags=QtCore.Qt.Widget):
        #~ assert dataset, 'a valid GDAL dataset expected'
        #~ DatasetInfoDialog.__init__(self, subdataset, parent, flags)
