# -*- coding: utf-8 -*-

# -----------------------------------------------------------------------------
# Copyright (c) 2010, Enthought Inc
# All rights reserved.
#
# This software is provided without warranty under the terms of the BSD
# license.
#
#
# Author: Enthought Inc
# Description: Qt API selector. Can be used to switch between pyQt and PySide
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# NOTE: Code modified to make PyQt4 the default Qt wrapper.
# -----------------------------------------------------------------------------

import os


def prepare_pyqt4():
    # Set PySide compatible APIs.
    import sip

    sip.setapi('QDate', 2)
    sip.setapi('QDateTime', 2)
    sip.setapi('QString', 2)
    sip.setapi('QTextStream', 2)
    sip.setapi('QTime', 2)
    sip.setapi('QUrl', 2)
    sip.setapi('QVariant', 2)

qt_api = os.environ.get('QT_API')

if qt_api is None:
    try:
        import PyQt5
        qt_api = 'pyqt5'
    except ImportError:
        raise
        try:
            prepare_pyqt4()
            import PyQt4
            qt_api = 'pyqt4'
        except ImportError:
            try:
                import PySide
                qt_api = 'pyside'
            except ImportError:
                raise ImportError('Cannot import PyQt4 or PySide')

elif qt_api == 'pyqt4':
    prepare_pyqt4()

elif qt_api != 'pyside':
    raise RuntimeError('Invalid Qt API %r, valid values are: '
                       '"pyqt5", "pyqt4" or "pyside"' % qt_api)
