# $Rev$
# $LastChangedDate$
# $URL$
__version__ = '$Id$'.replace('$', '')

import os
from PyQt4 import QtCore, QtGui
import csv
from datetime import datetime
from mileage_class import mileageEntry, mileageList
from UIFiles.mileage_Ui import Ui_MainWindow as uiform


class TableModel(QtCore.QAbstractTableModel):

    dirty = QtCore.pyqtSignal()

    def __init__(self, data=None, parent=None):
        QtCore.QAbstractListModel.__init__(self, parent)

        self.dataset = mileageList() if data is None else data
        self._special = ['cost', 'price', 'mpg']
        self._formats = ['${:.2f}', '${:.3f}', '{:.2f}']

    def rowCount(self, index=QtCore.QModelIndex()):
        return len(self.dataset)

    def columnCount(self, index=QtCore.QModelIndex()):
        return len(self.dataset.displayFields)

    def data(self, index, role):
        field = self.dataset.displayFields[index.column()]
        if role in (QtCore.Qt.DisplayRole, QtCore.Qt.EditRole):
            row = index.row()
            value = self.dataset[row][field]
            #Format special fields
            if value:
                try:
                    dex = self._special.index(field.lower())
                except:
                    pass
                else:
                    value = self._formats[dex].format(value)
            return QtCore.QVariant(value)
        elif role == QtCore.Qt.FontRole and field.lower() == 'mpg':
            font = QtGui.QFont()
            font.setBold(True)
            return font

    def setData(self, index, value, role):
        row = index.row()
        field = self.dataset.displayFields[index.column()]
        if field and index.isValid():
            try:
                self.dataset[row][field] = value.toPyObject()
            except AttributeError:
                return False
            else:
                self.dataChanged.emit(index, index)
                self.dirty.emit()
        return True

    def headerData(self, section, orientation, role):
        if role == QtCore.Qt.DisplayRole:
            if orientation == QtCore.Qt.Horizontal:
                if section < len(self.dataset.displayFields):
                    return self.dataset.displayFields[section]
                else:
                    return "not implemented"
            else:
                return section + 1
        elif (role == QtCore.Qt.FontRole and
                section < len(self.dataset.displayFields) and
                self.dataset.displayFields[section].lower() == 'mpg'):
            font = QtGui.QFont()
            font.setBold(True)
            return font

    def flags(self, index):
        field = self.dataset.displayFields[index.column()]
        if not index.isValid():
            return QtCore.Qt.ItemEnabled
        elif field in self.dataset.editableFields:
            return QtCore.Qt.ItemFlags(
                            QtCore.QAbstractTableModel.flags(self, index) |
                            QtCore.Qt.ItemIsEditable)
        return QtCore.Qt.ItemFlags(
                            QtCore.QAbstractTableModel.flags(self, index))

    def insertRow(self, entry, position=None, index=QtCore.QModelIndex()):
        """ Model required method for inserting rows """
        if position is None:
            position = self.rowCount()
        self.beginInsertRows(QtCore.QModelIndex(), position, position)
        self.dataset.append(entry)
        self.endInsertRows()
        self.dataChanged.emit(QtCore.QModelIndex(), QtCore.QModelIndex())
        self.dirty.emit()
        return True

    def changeDataset(self, dataset):
        """ Function that changes models underlying dataset

        This function is to facilitate changing the dataset for the model
        to be used in cases such as loading a file.

        """
        self.beginResetModel()
        self.dataset = dataset
        self.endResetModel()
        self.dirty.emit()
        #self.dirty.emit()


class mileageDelegate(QtGui.QStyledItemDelegate):

    def __init__(self, parent=None):
        super(mileageDelegate, self).__init__(parent)

    def createEditor(self, parent, option, index):
        field = index.model().dataset.fieldobjs[index.column()]
        if field.editor == field.DateEditor:
            de = QtGui.QDateEdit(parent)
            return de
        elif field.editor == field.DoubleSpinBoxEditor:
            spinbox = QtGui.QDoubleSpinBox(parent)
            spinbox.setDecimals(3)
            return spinbox
        else:
            return QtGui.QStyledItemDelegate.createEditor(self, parent, option, index)


class mileageGui(uiform, QtGui.QMainWindow):

    dirty = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super(mileageGui, self).__init__(parent)
        self.setWindowIcon(QtGui.QIcon('icons\gas-pump-icon.png'))

        self.setupUi(self)
        self._dirty = False
        self._checkSave = True
        #self.button_open.clicked.connect(self.file_dialog)

        #Set up application data
        # self._metapath = QtCore.QDir.homePath()
        self._metapath = os.getcwd()
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
        if self._dirty:
            message_box = self.createSaveChangesToCurrent()
            value = message_box.exec_()
            # This is a value of cancel
            if value == message_box.Cancel:
                event.setAccepted(False)
            # This is a yes value
            elif value == message_box.Yes:
                event.setAccepted(self.SaveFile(False))

    def About(self):
        msg_box = QtGui.QMessageBox()
        msg_box.setIcon(QtGui.QMessageBox.Information)
        msg_box.setWindowTitle('About')
        msg_box.setText(__version__)
        msg_box.exec_()
        print self.viewTable.verticalScrollBar().maximum()

    def Open(self, filename=None):
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
                    price = float(price)
                fillup = d[lhead.index('fillup')]
                e = mileageEntry(d[lhead.index('date')],
                                 d[lhead.index('town')],
                                 odometer, gallons, price, fillup, previous)
                m.append(e)
            self.tableModel.changeDataset(m)
            h = self.viewTable.verticalHeader().sectionSizeFromContents(0)
            self.viewTable.resizeColumnsToContents()
            self.viewTable.verticalHeader().setDefaultSectionSize(h.height())

            #Populate the combobox
            town_list = list(set([e['town'] for e in self.tableModel.dataset]))
            if '' in town_list:
                town_list.remove('')
            self.editLocation.addItems(sorted(town_list))
            self.viewTable.scrollToBottom()

            self._dirty = False
            self.changeWindowTitle()

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
        odo = float(self.editOdometer.text())
        gal = float(self.editGallons.text())
        ppg = float(self.editPrice.text())
        fil = self.checkFillup.isChecked()
        entry = mileageEntry(date, loc, odo, gal, ppg, fil,
                             self.tableModel.dataset[-1])
        self.tableModel.insertRow(entry)
        self.viewTable.scrollToBottom()
        for e in self._edits:
            e.clear()

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

    myapp.Open('..\FuelRecord.csv')

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
