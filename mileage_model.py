# $Rev$
# $LastChangedDate$
# $URL$
__version__ = '$Id$'.replace('$', '')

from PyQt4 import QtCore, QtGui
from mileage_class import mileageList


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
