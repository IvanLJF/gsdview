from PyQt4.QtCore import *

from PyQt4.QtCore import pyqtProperty as Property
from PyQt4.QtCore import pyqtSignal as Signal
from PyQt4.QtCore import pyqtSlot as Slot
#from PyQt4.Qt import QCoreApplication
#from PyQt4.Qt import Qt

__version__ = QT_VERSION_STR
__version_info__ = tuple(map(int, QT_VERSION_STR.split('.')))
