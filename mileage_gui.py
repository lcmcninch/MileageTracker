import sys
import os
from PyQt4 import QtCore, QtGui, uic
import csv
import pdb

form_path = os.path.join(os.getcwd(),'UIFiles\\ui1.ui')
form, base = uic.loadUiType(form_path)

class TableModel(QtCore.QAbstractTableModel):
    def __init__(self, table = [], headers = [], parent = None):
        QtCore.QAbstractListModel.__init__(self, parent)
        self._table = table
        self._headers = headers
    
    def rowCount(self, parent):
        return len(self._table)
    
    def columnCount(self, parent):
        return len(self._table[0])
    
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
        #super ensures __init__'s of the parents are run
        super(mileageGui,self).__init__(parent)
        
        self.setupUi(self)
        #self.button_open.clicked.connect(self.file_dialog)
        # QtCore.QObject.connect(self.ui.button_open,QtCore.SIGNAL("clicked()"), self.file_dialog)
        
        #Connect the close button
        self.actionClose.triggered.connect(self.close)
        
        

if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    myapp = mileageGui()
    myapp.show()
    
    with open('FuelRecord.csv','rb') as f:
        reader = csv.reader(f)
        header = reader.next()
        #pdb.set_trace()
        data = [row for row in reader]

    model = TableModel(data, header)
    myapp.tableView.setModel(model)
    myapp.tableView.resizeRowsToContents()
    myapp.tableView.resizeColumnsToContents()
    
    #odometer = list(zip(*data)[2])
    # pdb.set_trace()
    # odometer = [float(k) for k in list(zip(*data)[2])]
    #try operator.itemgetter
    
    app.exec_()