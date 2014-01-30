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

        # Setup the undo stack
        self.undoStack = QtGui.QUndoStack(self)

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
        self.tableModel = TableModel(self.undoStack)
        self.viewTable.setModel(self.tableModel)
        self.tableModel.newActiveCell.connect(self.viewTable.selectCell)
        self.viewTable.setAlternatingRowColors(True)
        dg = mileageDelegate(self)
        self.viewTable.setItemDelegate(dg)

        #Signal/slot connections
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

        #Set the window title
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

    def showEvent(self, event):
        """ Implemented to setup table view geometry """
        self.viewTable.horizontalHeader().restoreState(
                self._initHeaderState.toByteArray())

    def About(self):
        msg_box = QtGui.QMessageBox()
        msg_box.setIcon(QtGui.QMessageBox.Information)
        msg_box.setWindowTitle('About')
        msg_box.setText('Mileage Tracker')
        msg_box.exec_()
        print self.viewTable.verticalScrollBar().maximum()

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
        self._currentFile = None
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
                    price = float(price.replace('$', ''))
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
            self.checkFresh.setChecked(False)

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

    def setDirty(self):
        """ Slot to set the dirty flag when changes have been made """
        self._dirty = True
        self.changeWindowTitle()

    def changeWindowTitle(self, filename=None):
        """ Simple helper function to change the window title """
        file_path = filename if filename else self._currentFile
        if not file_path:
            file_path = 'Untitled'
        if self._dirty:
            file_path = ''.join(['*', file_path])
        win_title = 'Fuel Mileage - ' + file_path
        self.setWindowTitle(win_title)

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
            kwargs = {'date': str(parent.editDate.date().toString('MM/dd/yy')),
                      'location': str(parent.editLocation.currentText()),
                      'odometer': (float(odo) if not odo.isEmpty() else None),
                      'gallons': float(gal) if not gal.isEmpty() else None,
                      'price': float(pri) if not pri.isEmpty() else None,
                      'fillup': parent.checkFillup.isChecked()}
            self.kwargs = kwargs

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

        def undo(self):
            index = self.parent.tableModel.dataset.index(self.entry)
            self.parent.tableModel.removeRows(index)


def warningBox(message):
    message_box = QtGui.QMessageBox()
    message_box.setText(message)
    message_box.setIcon(QtGui.QMessageBox.Warning)
    message_box.exec_()

if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    myapp = mileageGui()

    myapp.Open('../GolfFuelRecord.csv')

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
