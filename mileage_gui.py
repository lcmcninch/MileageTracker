#! /usr/bin/python
import sys
import os
from PyQt4 import QtCore, QtGui
import csv
from datetime import datetime
from mileage_class import mileageEntry, mileageList
from mileage_model import TableModel, mileageDelegate
from mileage_database import MileageDatabase
from UIFiles.mileage_Ui import Ui_MainWindow as uiform

# These are used in the settings
organization = "McNinch Custom"
application = "FuelMileage"
version = '0.2'


def resource_path(relative):
    local = getattr(sys, '_MEIPASS', '.')
    return os.path.join(local, relative)


ffilter = 'Mileage Tracker File (*.mtf);;CSV Files (*.csv)' + \
          ';;All Files (*)'


class mileageGui(uiform, QtGui.QMainWindow):

    dirty = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super(mileageGui, self).__init__(parent)
        self.setWindowIcon(QtGui.QIcon(resource_path(r'icons\gas-station-multi-size.ico')))
        self.setupUi(self)

        # Setup application organization and application name
        app = QtGui.QApplication.instance()
        app.setOrganizationName(organization)
        app.setApplicationName(application)

        # Setup the undo stack
        self.undoStack = QtGui.QUndoStack(self)
        self.undoStack.cleanChanged.connect(self.undoCleanSlot)

        # Get settings object
        settings = QtCore.QSettings()

        # Recent files list
        stringlist = settings.value("recentfiles").toPyObject()
        self.recentFileList = list(stringlist) if stringlist else []
        self.createRecentFileMenu()

        # Restore window geometry
        self.restoreGeometry(
            settings.value("MainWindow/Geometry").toByteArray())
        self._initHeaderState = settings.value('TableView/HeaderState')

        # Restore other options and settings
        defaults = {'currentfile': None}
        options = settings.value("options").toPyObject()
        if options:
            for k, v in options.iteritems():
                if str(k) in defaults:
                    defaults[str(k)] = v
        self.options = defaults
        currentfile = self.options['currentfile']
        if currentfile and not os.path.exists(currentfile):
            self.options['currentfile'] = None

        # Set up application data
        self._metapath = os.getcwd()
        self._dirty = False
        self._checkSave = True
        self._edits = [self.editOdometer, self.editGallons, self.editPrice]
        self.editDate.setDate(datetime.now())
        self.editDate.setCurrentSection(QtGui.QDateTimeEdit.DaySection)

        # Set up the table model
        self.tableModel = TableModel(self.undoStack)
        self.viewTable.setModel(self.tableModel)
        self.tableModel.newActiveCell.connect(self.viewTable.selectCell)
        self.viewTable.setAlternatingRowColors(True)
        dg = mileageDelegate(self)
        self.viewTable.setItemDelegate(dg)

        # Signal/slot connections
        self.actionExit.triggered.connect(self.close)
        self.actionAbout.triggered.connect(self.About)
        self.actionNew.triggered.connect(self.New)
        self.actionOpen.triggered.connect(self.Open)
        self.actionSave.triggered.connect(self.Save)
        self.actionSave_As.triggered.connect(self.Save_As)
        self.actionUndo.triggered.connect(self.undoStack.undo)
        self.actionRedo.triggered.connect(self.undoStack.redo)
        self.checkFresh.toggled.connect(self.freshChecked)
        self.buttonInsert.clicked.connect(self.Insert)
        self.tableModel.dirty.connect(self.setDirty)
        self.dirty.connect(self.setDirty)

        # Set up a file reader dictionary
        self._file_readers = {'.csv': self.readcsv,
                              '.mtf': self.readmtf}

        QtCore.QTimer.singleShot(0, self.startup)

    def startup(self):
        """ Open a new or existing file to start with """
        if self.options['currentfile']:
            self.Open(self.options['currentfile'])
        else:
            self.New()

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
            settings.setValue("options", QtCore.QVariant(self.options))
            settings.setValue("recentfiles", QtCore.QVariant(self.recentFileList))

    def showEvent(self, event):
        """ Implemented to setup table view geometry """
        self.viewTable.horizontalHeader().restoreState(
            self._initHeaderState.toByteArray())

    def About(self):
        msg_box = QtGui.QMessageBox()
        msg_box.setIcon(QtGui.QMessageBox.Information)
        msg_box.setWindowTitle('About')
        msg = 'Mileage Tracker v{}'.format(version)
        msg_box.setText(msg)
        msg_box.exec_()

    def New(self):
        """ Create a new file """
        # Check to save current file
        if self._dirty:
            message_box = self.createSaveChangesToCurrent()
            value = message_box.exec_()
            if value == message_box.Yes:
                value = self.SaveFile(False)
            if value == message_box.Cancel:
                return

        # Make changes
        self.options['currentfile'] = None
        self.tableModel.changeDataset(mileageList())
        self._dirty = False
        self.changeWindowTitle()
        self.checkFresh.setChecked(True)
        self.editDate.setFocus(QtCore.Qt.TabFocusReason)

    def Open(self, filename=None):
        """ Opens a new csv file """
        if self._dirty:
            message_box = self.createSaveChangesToCurrent()
            value = message_box.exec_()
            if value == message_box.Yes:
                value = self.SaveFile(False)
            if value == message_box.Cancel:
                return
        # Get the new filename
        if filename:
            fname = os.path.abspath(str(filename))
        else:
            fname = QtGui.QFileDialog.getOpenFileName(self,
                                                      'Open file',
                                                      directory=self._metapath,
                                                      filter=ffilter)

        if fname:
            fname = str(QtCore.QDir.toNativeSeparators(fname))
            self.options['currentfile'] = fname
            self._metapath = os.path.dirname(fname)
            ext = os.path.splitext(fname)[1]

            # Read the file
            dataset = self._file_readers[ext](fname)
            self.tableModel.changeDataset(dataset)

            # h = self.viewTable.verticalHeader().sectionSizeFromContents(0)
            # self.viewTable.verticalHeader().setDefaultSectionSize(h.height())
            h = self.viewTable.sizeHintForRow(0)
            self.viewTable.verticalHeader().setDefaultSectionSize(h)

            # Populate the combobox
            self.editLocation.setInsertPolicy(QtGui.QComboBox.InsertAlphabetically)
            town_list = list(set([e['town'] for e in dataset]))
            if '' in town_list:
                town_list.remove('')
            self.editLocation.addItems(sorted(town_list))
            self.viewTable.scrollToBottom()

            self._dirty = False
            self.changeWindowTitle()
            self.undoStack.clear()
            self.editDate.setFocus(QtCore.Qt.TabFocusReason)
            self.checkFresh.setChecked(False)
            self.addToRecentFileList(fname)

    def readcsv(self, fname):
        """Read a csv file"""
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
                price = float(price.replace('$', ''))
            fillup = d[lhead.index('fillup')]
            if 'compareprice' in lhead:
                compareprice = d[lhead.index('compareprice')]
            else:
                compareprice = None
            e = mileageEntry(d[lhead.index('date')],
                             d[lhead.index('town')], odometer,
                             gallons, price, fillup, previous, compareprice)
            m.append(e)
        return m

    def readmtf(self, fname):
        """Read an mtf database file"""
        newdb = MileageDatabase(fname)
        m = mileageList()
        for k in range(1, len(newdb)+1):
            previous = m[-1] if newdb.linkback(k) else None
            gallons = newdb.gallons(k)
            if gallons:
                gallons = float(gallons)
            odometer = newdb.odometer(k)
            if odometer:
                odometer = float(odometer)
            price = newdb.price(k)
            fillup = newdb.fillup(k)
            compareprice = newdb.compareprice(k)
            e = mileageEntry(newdb.date(k), newdb.town(k), odometer,
                             gallons, price, fillup, previous, compareprice)
            m.append(e)
        return m

    def Save(self):
        self.SaveFile(False)

    def Save_As(self):
        self.SaveFile(True)

    def SaveFile(self, checksave=True):
        fname = self.options['currentfile']
        if checksave or not fname:
            pth = self._metapath
            fname = str(QtGui.QFileDialog.getSaveFileName(self,
                        'Save file', directory=pth, filter=ffilter))

        if fname:
            fname = str(QtCore.QDir.toNativeSeparators(fname))
            self._metapath = os.path.dirname(fname)
            self.options['currentfile'] = fname
            if self.isSQLite(fname):
                return self.writesql(fname)
            else:
                return self.writecsv(fname)

        return False

    def writecsv(self, fname):
        try:
            fid = open(fname, 'wb')
        except IOError:
            warningBox('{}\nis locked. Please try again!'.format(fname))
            return False
        else:
            with fid:
                self.tableModel.dataset.write(fid, ftype='csv')
            self.undoStack.setClean()
            self._dirty = False
            self.changeWindowTitle()
            self.addToRecentFileList(fname)
            return True

    def writesql(self, fname):
        if os.path.exists(fname):
            os.remove(fname)
        newdb = MileageDatabase(fname)
        self.tableModel.dataset.write(newdb, 'mtf')
        self.undoStack.setClean()
        self._dirty = False
        self.changeWindowTitle()
        self.addToRecentFileList(fname)
        return True

    def isSQLite(self, fname):
        if os.path.splitext(fname)[1] in ['.db', '.mtf']:
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
        command = self.insertCmd(self)
        self.undoStack.push(command)

    def freshChecked(self, state):
        """ Make sure Start Fresh can be checked """
        if not state and not len(self.tableModel.dataset):
            self.checkFresh.setChecked(True)
        if self.checkFresh.isChecked():
            self.checkFillup.setChecked(True)
            self.checkFillup.setEnabled(False)
        else:
            self.checkFillup.setEnabled(True)

    def undoCleanSlot(self, value):
        self._dirty = not value
        self.changeWindowTitle()

    def setDirty(self):
        """ Slot to set the dirty flag when changes have been made """
        self._dirty = True
        self.changeWindowTitle()

    def changeWindowTitle(self, filename=None):
        """ Simple helper function to change the window title """
        file_path = filename if filename else self.options['currentfile']
        if not file_path:
            file_path = 'Untitled'
        if self._dirty:
            file_path = ''.join(['*', file_path])
        win_title = 'Fuel Mileage - ' + file_path
        self.setWindowTitle(win_title)

    def createRecentFileMenu(self):
        """ Create the Recent File Menu """
        menu = QtGui.QMenu()
        sm = QtCore.QSignalMapper(self)
        sm.mapped[QtCore.QString].connect(self.Open)
        for rfile in self.recentFileList[:]:
            if os.path.exists(rfile):
                a = QtGui.QAction(rfile, self)
                sm.setMapping(a, str(rfile))
                a.triggered.connect(sm.map)
                menu.addAction(a)
            else:
                self.recentFileList.remove(rfile)
        self.actionRecent_Files.setMenu(menu)

    def addToRecentFileList(self, rfile):
        """ Add file to the recent file list menu also refresh the menu """
        if rfile in self.recentFileList:
            self.recentFileList.remove(rfile)
        if len(self.recentFileList) > 9:
            self.recentFileList.pop(-1)
        self.recentFileList.insert(0, rfile)
        self.createRecentFileMenu()

    #               #
    # Undo Commands #
    #               #

    class insertCmd(QtGui.QUndoCommand):
        def __init__(self, parent):
            QtGui.QUndoCommand.__init__(self)
            self.parent = parent
            odo = parent.editOdometer.text()
            gal = parent.editGallons.text()
            pri = parent.editPrice.text()
            kwargs = {'date': str(parent.editDate.date().toString('MM/dd/yyyy')),
                      'location': str(parent.editLocation.currentText()),
                      'odometer': (float(odo) if not odo.isEmpty() else None),
                      'gallons': float(gal) if not gal.isEmpty() else None,
                      'price': float(pri) if not pri.isEmpty() else None,
                      'fillup': parent.checkFillup.isChecked()}
            self.kwargs = kwargs
            self.startFresh = parent.checkFresh.isChecked()

        def redo(self):
            if (self.parent.checkFresh.isChecked() or
                    len(self.parent.tableModel.dataset) == 0):
                previous = None
            else:
                previous = self.parent.tableModel.dataset[-1]
            self.entry = mileageEntry(previous=previous, **self.kwargs)
            self.parent.tableModel.insertRow(self.entry)
            self.parent.viewTable.scrollToBottom()
            for e in self.parent._edits:
                e.clear()
            self.parent.editDate.setFocus(QtCore.Qt.TabFocusReason)
            self.parent.checkFresh.setChecked(False)

        def undo(self):
            index = self.parent.tableModel.dataset.index(self.entry)
            self.parent.tableModel.removeRows(index)
            self.parent.checkFresh.setChecked(self.startFresh)


def warningBox(message):
    message_box = QtGui.QMessageBox()
    message_box.setText(message)
    message_box.setIcon(QtGui.QMessageBox.Warning)
    message_box.exec_()


if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    myapp = mileageGui()
    myapp.show()
    app.exec_()
