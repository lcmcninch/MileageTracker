#!/usr/bin/python
# Original Author: Luke McNinch
# Original Creation Date: 2013/11/13

import sys
from PyQt4.QtGui import QApplication, QPixmap, QSplashScreen
from PyQt4.QtCore import Qt


"""
This script imports the minimum modules necessary to display a splash
screen before importing and displaying the downloader application.
"""

app = QApplication(sys.argv)

# Create and display the splash screen
splash_pix = QPixmap('icons\splash_loading.png')
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
