# $Rev$
# $LastChangedDate$
# $URL$
__version__ = '$Id$'.replace('$', '')

import os
from PyQt4 import QtCore, QtGui
import csv
from datetime import datetime
from mileage_class import mileageEntry, mileageList
from mileage_model import TableModel, mileageDelegate
from UIFiles.mileage_Ui import Ui_MainWindow as uiform

# These are used in the settings
organization = "McNinch Custom"
application = "FuelMileage"


class mileageGui(uiform, QtGui.QMainWindow):

    dirty = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super(mileageGui, self).__init__(parent)
        self.setWindowIcon(QtGui.QIcon('icons\gas-pump-icon.png'))
        self.setupUi(self)

        # Setup application organization and application name
        app = QtGui.QApplication.instance()
        app.setOrganizationName(organization)
        app.setApplicationName(application)

        # Get settings object
        settings = QtCore.QSettings()
        #Restore window geometry
        self.restoreGeometry(
                settings.value("MainWindow/Geometry").toByteArray())
        self._initHeaderState = settings.value('TableView/HeaderState')

        #Set up application data
        # self._metapath = QtCore.QDir.homePath()
        self._metapath = os.getcwd()
        self._dirty = False
        self._checkSave = True
        self._edits = [self.editOdometer, self.editGallons, self.editPrice]
        self._currentFile = None
        self.editDate.setDate(datetime.now())
        self.editDate.setCurrentSection(QtGui.QDateTimeEdit.DaySection)

        #Set up the table model
        self.tableModel = TableModel()
        self.viewTable.setModel(self.tableModel)
        self.viewTable.setAlternatingRowColors(True)
        dg = mileageDelegate(self)
        self.viewTable.setItemDelegate(dg)

        #Signal/slot connections
        self.actionExit.triggered.connect(self.close)
        self.actionAbout.triggered.connect(self.About)
        self.actionOpen.triggered.connect(self.Open)
        self.actionSave.triggered.connect(self.Save)
        self.actionSave_As.triggered.connect(self.Save_As)
        self.buttonInsert.clicked.connect(self.Insert)
        self.tableModel.dirty.connect(self.setDirty)
        self.dirty.connect(self.setDirty)

    def closeEvent(self, event):
        """
        Implemented to prompt to save if file is changed and save settings
        before closing
        """
        if self._dirty:
            message_box = self.createSaveChangesToCurrent()
            value = message_box.exec_()
            # This is a value of cancel
            if value == message_box.Cancel:
                event.setAccepted(False)
            # This is a yes value
            elif value == message_box.Yes:
                event.setAccepted(self.SaveFile(False))
        if event.isAccepted():
            settings = QtCore.QSettings()
            settings.setValue("MainWindow/Geometry", QtCore.QVariant(
                          self.saveGeometry()))
            settings.setValue('TableView/HeaderState',
                          self.viewTable.horizontalHeader().saveState())

    def showEvent(self, event):
        """ Implemented to setup table view geometry """
        self.viewTable.horizontalHeader().restoreState(
                self._initHeaderState.toByteArray())

    def About(self):
        msg_box = QtGui.QMessageBox()
        msg_box.setIcon(QtGui.QMessageBox.Information)
        msg_box.setWindowTitle('About')
        msg_box.setText(__version__)
        msg_box.exec_()
        print self.viewTable.verticalScrollBar().maximum()

    def Open(self, filename=None):
        """ Opens a new csv file """
        if self._dirty:
            message_box = self.createSaveChangesToCurrent()
            value = message_box.exec_()
            if value == message_box.Yes:
                value = self.SaveFile(False)
            if value == message_box.Cancel:
                return
        #Get the new filename
        if filename:
            fname = os.path.abspath(filename)
        else:
            fname = str(QtGui.QFileDialog.getOpenFileName(self,
                          'Open file', directory=self._metapath,
                          filter='CSV Files (*.csv)'))

        if fname:
            self._metapath = os.path.dirname(fname)
            self._currentFile = fname
            with open(fname, 'rb') as f:
                reader = csv.reader(f)
                header = reader.next()
                data = [row for row in reader]
            lhead = [x.lower() for x in header]
            m = mileageList()
            for d in data:
                previous = None
                gallons = d[lhead.index('gallons')]
                if len(m) and gallons:
                    gallons = float(gallons)
                    previous = m[-1]
                odometer = d[lhead.index('odometer')]
                if odometer:
                    odometer = float(odometer)
                price = d[lhead.index('price')]
                if price:
                    price = float(price.replace('$',''))
                fillup = d[lhead.index('fillup')]
                e = mileageEntry(d[lhead.index('date')],
                                 d[lhead.index('town')],
                                 odometer, gallons, price, fillup, previous)
                m.append(e)
            self.tableModel.changeDataset(m)
            h = self.viewTable.verticalHeader().sectionSizeFromContents(0)
            self.viewTable.verticalHeader().setDefaultSectionSize(h.height())

            #Populate the combobox
            self.editLocation.setInsertPolicy(QtGui.QComboBox.InsertAlphabetically)
            town_list = list(set([e['town'] for e in self.tableModel.dataset]))
            if '' in town_list:
                town_list.remove('')
            self.editLocation.addItems(sorted(town_list))
            self.viewTable.scrollToBottom()

            self._dirty = False
            self.changeWindowTitle()
            self.editDate.setFocus(QtCore.Qt.TabFocusReason)

    def Save(self):
        self.SaveFile(False)

    def Save_As(self):
        self.SaveFile(True)

    def SaveFile(self, checksave=True):
        fname = self._currentFile
        if checksave or not self._currentFile:
            pth = self._currentFile if self._currentFile else self._metapath
            fname = str(QtGui.QFileDialog.getSaveFileName(self,
                          'Save file', directory=pth,
                          filter='CSV Files (*.csv)'))

        if fname:
            self._metapath = os.path.dirname(fname)
            self._currentFile = fname
            try:
                fid = open(fname, 'wb')
            except IOError:
                warningBox('{}\nis locked. Please try again!'.format(fname))
            else:
                with fid:
                    self.tableModel.dataset.write(fid, ftype='csv')
                self._dirty = False
                self.changeWindowTitle()
            return True

        return False

    def createSaveChangesToCurrent(self):
        message = ("Do you want to save the changes to the current"
                   " file?")
        message_box = QtGui.QMessageBox()
        message_box.setText(message)
        message_box.setWindowTitle('Save Changes?')
        message_box.setIcon(QtGui.QMessageBox.Question)
        message_box.addButton(QtGui.QMessageBox.Yes)
        message_box.addButton(QtGui.QMessageBox.No)
        message_box.addButton(QtGui.QMessageBox.Cancel)
        return message_box

    def Insert(self):
        date = str(self.editDate.date().toString('MM/dd/yy'))
        loc = str(self.editLocation.currentText())
        odo = self.editOdometer.text()
        odo = float(odo) if not odo.isEmpty() else None
        gal = float(self.editGallons.text())
        ppg = float(self.editPrice.text())
        fil = self.checkFillup.isChecked()
        entry = mileageEntry(date, loc, odo, gal, ppg, fil,
                             self.tableModel.dataset[-1])
        self.tableModel.insertRow(entry)
        self.viewTable.scrollToBottom()
        for e in self._edits:
            e.clear()
        self.editDate.setFocus(QtCore.Qt.TabFocusReason)

    def setDirty(self):
        """ Slot to set the dirty flag when changes have been made """
        self._dirty = True
        self.changeWindowTitle()

    def changeWindowTitle(self, filename=None):
        """ Simple helper function to change the window title """
        file_path = filename if filename else self._currentFile
        if self._dirty:
            file_path = ''.join(['*', file_path])
        win_title = 'Fuel Mileage - ' + file_path
        self.setWindowTitle(win_title)


def warningBox(message):
    message_box = QtGui.QMessageBox()
    message_box.setText(message)
    message_box.setIcon(QtGui.QMessageBox.Warning)
    message_box.exec_()

if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    myapp = mileageGui()

    myapp.Open('../FuelRecord.csv')

#    with open('..\FuelRecord.csv','rb') as f:
#        reader = csv.reader(f)
#        header = reader.next()
#        lhead = [x.lower() for x in header]
#        #pdb.set_trace()
#        data = [row for row in reader]
#    m = mileageList()
#    for d in data:
#        previous = None
#        gallons = d[lhead.index('gallons')]
#        if len(m) and gallons:
#            gallons = float(gallons)
#            previous = m[-1]
#        odometer = d[lhead.index('odometer')]
#        if odometer:
#            odometer = float(odometer)
#        ppg = d[lhead.index('ppg')]
#        if ppg:
#            ppg = float(ppg)
#        # fillup = True if d[lhead.index('mpg')] else False
#        fillup = d[lhead.index('fillup')]
#        e = mileageEntry(d[lhead.index('date')],
#                         d[lhead.index('town')],
#                         odometer, gallons, ppg,
#                         fillup, previous)
#        m.append(e)
#
#    myapp.viewTable.model().changeDataset(m)
##    myapp.viewTable.resizeRowsToContents()
##    myapp.viewTable.resizeColumnsToContents()

    myapp.show()

    #odometer = list(zip(*data)[2])
    # pdb.set_trace()
    # odometer = [float(k) for k in list(zip(*data)[2])]
    #try operator.itemgetter

    app.exec_()
