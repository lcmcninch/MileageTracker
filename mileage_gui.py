# $Rev$
# $LastChangedDate$
# $URL$
__version__ = '$Id$'.replace('$','')

import os.path
from PyQt4 import QtCore, QtGui, uic
import csv
from datetime import datetime
import pdb
from mileage_class import mileageEntry, mileageList

form_path = os.path.join(os.getcwd(),'UIFiles\\ui1.ui')
form, base = uic.loadUiType(form_path)

class TableModel(QtCore.QAbstractTableModel):
    def __init__(self, data, parent = None):
        QtCore.QAbstractListModel.__init__(self, parent)
        
        self.dataset = data
        self._headers = ['Date', 'Town', 'Odometer', 'Miles', 'Gallons',
                         'MPG' , 'Price', 'Cost']
    
    def rowCount(self, index=QtCore.QModelIndex()):
        return len(self.dataset)
    
    def columnCount(self, index=QtCore.QModelIndex()):
        return len(self._headers)
    
    def data(self, index, role):
        if role == QtCore.Qt.DisplayRole:
            row = index.row()
            field = self._headers[index.column()]
            value = self.dataset[row][field]
            if field.lower() == 'cost' and value:
                value = '${:.2f}'.format(value)
            
            return value

    def headerData(self, section, orientation, role):        
        if role == QtCore.Qt.DisplayRole:            
            if orientation == QtCore.Qt.Horizontal:                
                if section < len(self._headers):
                    return self._headers[section]
                else:
                    return "not implemented"
            else:
                return section + 1

    def flags(self, index):
        if not index.isValid():
            return QtCore.Qt.ItemEnabled
        return QtCore.Qt.ItemFlags(
                            QtCore.QAbstractTableModel.flags(self, index) |
                            QtCore.Qt.ItemIsEditable)

    def insertRow(self, entry, position=None, index=QtCore.QModelIndex()):
        """ Model required method for inserting rows """
        if position is None:
            position = self.rowCount()
        self.beginInsertRows(QtCore.QModelIndex(), position, position)
        self.dataset.append(entry)
        self.endInsertRows()
        self.dataChanged.emit(QtCore.QModelIndex(), QtCore.QModelIndex())
        return True

    def changeDataset(self, dataset):
        """ Function that changes models underlying dataset

        This function is to facilitate changing the dataset for the model
        to be used in cases such as loading a file.

        """
        self.beginResetModel()
        self.dataset = dataset
        self.endResetModel()
        #self.dirty.emit()


class mileageGui(base, form):
    def __init__(self, parent=None):
        super(mileageGui,self).__init__(parent)
        self.setWindowIcon(QtGui.QIcon('icons\gas-pump-icon.png'))
        
        self.setupUi(self)
        #self.button_open.clicked.connect(self.file_dialog)
        
        #Set up application data
        # self._metapath = QtCore.QDir.homePath()
        self._metapath = os.getcwd()
        self.editDate.setDate(datetime.now())
        self.editDate.setCurrentSection(QtGui.QDateTimeEdit.DaySection)
        
        #Signal/slot connections
        self.actionClose.triggered.connect(self.close)
        self.actionAbout.triggered.connect(self.About)
        self.actionImport.triggered.connect(self.Import)
        self.buttonInsert.clicked.connect(self.Insert)
        
        self.tableModel = TableModel([])
        self.viewTable.setModel(self.tableModel)
        self.viewTable.setAlternatingRowColors(True)

    def About(self):
        msg_box = QtGui.QMessageBox()
        msg_box.setIcon(QtGui.QMessageBox.Information)
        msg_box.setWindowTitle('About')
        msg_box.setText(__version__)
        msg_box.exec_()
        print self.viewTable.verticalScrollBar().maximum()
    
    def Import(self, filename=None):
        if filename:
            fname = filename 
        else:
            fname = str(QtGui.QFileDialog.getOpenFileName(self,
                          'Open file', directory = self._metapath,
                          filter = 'CSV Files (*.csv)'))
        
        if fname:
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
                ppg = d[lhead.index('ppg')]
                if ppg:
                    ppg = float(ppg)
                fillup = d[lhead.index('fillup')]
                e = mileageEntry(d[lhead.index('date')],
                                 d[lhead.index('town')],
                                 odometer, gallons, ppg,
                                 fillup, previous)
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

#    def scrollToBottom(self):
#        sb = self.viewTable.verticalScrollBar()
#        max = sb.maximum()
#        print max
#        sb.setValue(max)
#        print sb.value()

    
    
if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    myapp = mileageGui()
    
    myapp.Import('..\FuelRecord.csv')
    
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