# $Rev$
# $LastChangedDate$
# $URL$
__version__ = '$Id$'.replace('$','')

import os.path
from PyQt4 import QtCore, QtGui, uic
import csv
from datetime import datetime
import pdb

form_path = os.path.join(os.getcwd(),'UIFiles\\ui1.ui')
form, base = uic.loadUiType(form_path)

class TableModel(QtCore.QAbstractTableModel):
    def __init__(self, table = None, headers = None, parent = None):
        QtCore.QAbstractListModel.__init__(self, parent)
        if table is None: table = []
        if headers is None: headers = []
        self._table = table
        self._headers = headers
    
    def rowCount(self, parent):
        return len(self._table)
    
    def columnCount(self, parent):
        if self._table:
            return len(self._table[0])
        else:
            return 0
    
    def data(self, index, role):

        if role == QtCore.Qt.DisplayRole:
            row = index.row()
            col = index.column()
            value = self._table[row][col]
            
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


class mileageGui(base, form):
    def __init__(self, parent=None):
        super(mileageGui,self).__init__(parent)
        
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
        
        self.tableModel = TableModel([],[])
        self.viewTable.setModel(self.tableModel)

    def About(self):
        msg_box = QtGui.QMessageBox()
        msg_box.setIcon(QtGui.QMessageBox.Information)
        msg_box.setWindowTitle('About')
        msg_box.setText(__version__)
        msg_box.exec_()
    
    def Import(self, filename=None):
        if filename:
            fname = filename 
        else:
            fname = str(QtGui.QFileDialog.getOpenFileName(self,
                          'Open file', directory = self._metapath,
                          filter = 'CSV Files (*.csv)'))
        
        if fname:
            with open(fname,'rb') as f:
                reader = csv.reader(f)
                header = reader.next()
                data = [row for row in reader]
            self.tableModel.layoutAboutToBeChanged.emit()
            self.tableModel._table = data
            self.tableModel._headers = header
            self.tableModel.layoutChanged.emit()
            self.viewTable.resizeColumnsToContents()
        
        #Populate the combobox
        dex = self.tableModel._headers.index('Town')
        town_list = list(set([e[dex] for e in self.tableModel._table]))
        town_list.remove('')
        self.editLocation.addItems(sorted(town_list))
    
    def Insert(self):
        print 'Insert'

    
    
if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    myapp = mileageGui()
    myapp.show()

    #odometer = list(zip(*data)[2])
    # pdb.set_trace()
    # odometer = [float(k) for k in list(zip(*data)[2])]
    #try operator.itemgetter
    
    app.exec_()