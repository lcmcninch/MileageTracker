#!/usr/bin/python
# Original Author: Luke McNinch
# Original Creation Date: 2013/11/13

from PyQt4.QtGui import QApplication, QPixmap, QSplashScreen
from PyQt4.QtCore import Qt
import sys
import os.path
"""
This script imports the minimum modules necessary to display a splash
screen before importing and displaying the downloader application.
"""


def resource_path(relative):
    local = getattr(sys, '_MEIPASS', '.')
    return os.path.join(local, relative)


# Create and display the splash screen
app = QApplication([])
splash_pix = QPixmap(resource_path('icons\splash_loading.png'))
splash = QSplashScreen(splash_pix, Qt.WindowStaysOnTopHint)
splash.setMask(splash_pix.mask())
splash.show()
app.processEvents()

# Import and display the application
from mileage_gui import mileageGui
myapp = mileageGui()
myapp.show()

# Close the splash screen
splash.finish(myapp)
app.exec_()
