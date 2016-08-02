from PyQt4 import QtCore, QtGui
from mileage_class import mileageList

model_idx = QtCore.QModelIndex


class TableModel(QtCore.QAbstractTableModel):

    dirty = QtCore.pyqtSignal()
    newActiveCell = QtCore.pyqtSignal(QtCore.QModelIndex)

    def __init__(self, undoStack, data=None, parent=None):
        QtCore.QAbstractListModel.__init__(self, parent)

        self.dataset = mileageList() if data is None else data
        self._special = ['cost', 'price', 'mpg', 'odometer']
        self._formats = ['${:.2f}', '${:.3f}', '{:.2f}', '{:,}']
        self.undoStack = undoStack

    def rowCount(self, index=model_idx()):
        return len(self.dataset)

    def columnCount(self, index=model_idx()):
        return len(self.dataset.displayFields)

    def data(self, index, role):
        fieldname = self.dataset.displayFields[index.column()]
        field = self.dataset.getFieldByName(fieldname)
        if role in (QtCore.Qt.DisplayRole, QtCore.Qt.EditRole):
            row = index.row()
            value = self.dataset[row][field]
            #Format special fields
            if value:
                try:
                    dex = self._special.index(fieldname.lower())
                except:
                    pass
                else:
                    value = self._formats[dex].format(value)
            return QtCore.QVariant(value)
        elif role == QtCore.Qt.FontRole and fieldname.lower() == 'mpg':
            font = QtGui.QFont()
            font.setBold(True)
            return font

    def setData(self, index, value, role):
        row = index.row()
        fieldname = self.dataset.displayFields[index.column()]
        field = self.dataset.getFieldByName(fieldname)
        oldvalue = self.dataset[row][field]
        if field.editor == field.DateEditEditor:
            newvalue = str(value.toPyObject().toString('MM/dd/yyyy'))
        else:
            newvalue = str(value.toString())
        if not newvalue:
            newvalue = None
        if field and index.isValid() and oldvalue != newvalue:

            command = self.setDataCmd(index, newvalue, oldvalue, self)
            self.undoStack.push(command)
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

    def insertRow(self, entry, position=None, index=model_idx()):
        """ Model required method for inserting rows """
        if position is None:
            position = self.rowCount()
        self.beginInsertRows(QtCore.QModelIndex(), position, position)
        self.dataset.append(entry)
        self.endInsertRows()
        self.dataChanged.emit(model_idx(), model_idx())
        self.dirty.emit()
        return True

    def removeRows(self, position, rows=0, index=model_idx()):
        """ Model required function for removing rows """
        self.beginRemoveRows(model_idx(), position, position + rows)
        self.dataset.removeEntry(position)
        self.endRemoveRows()
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

    #               #
    # Undo Commands #
    #               #

    class setDataCmd(QtGui.QUndoCommand):
        def __init__(self, index, newvalue, oldvalue, model):
            QtGui.QUndoCommand.__init__(self)
            self.index = index
            self.row = index.row()
            self.field = model.dataset.displayFields[index.column()]
            self.newvalue = newvalue
            self.oldvalue = oldvalue
            self.model = model
            self.success = False

        def redo(self):
            model = self.model
            row = self.row
            field = self.field
            try:
                model.dataset[row][field] = self.newvalue
            except AttributeError:
                #This is meant to handle the case when an invalid field is changed
                #The Attribute Error would be raised by the mileageEntry class
                #May not be necessary because those fields shouldn't be editable anyway
                self.success = False
            else:
                model.dataChanged.emit(self.index, self.index)
                model.dirty.emit()
                self.success = True
                model.newActiveCell.emit(self.index)

        def undo(self):
            if self.success:
                model = self.model
                row = self.row
                field = self.field
                model.dataset[row][field] = self.oldvalue
                self.success = False
                model.dataChanged.emit(self.index, self.index)
                model.dirty.emit()
                model.newActiveCell.emit(self.index)


class mileageDelegate(QtGui.QStyledItemDelegate):
    """A delegate that allows for checkbox cells and different editor types

    Most work is based on the example given in the following StackOverflow
    answer: http://stackoverflow.com/a/17788371
    """

    def __init__(self, parent=None):
        super(mileageDelegate, self).__init__(parent)

    def paint(self, painter, option, index):
        """Re-implemented to paint checkboxes when necessary"""
        field = index.model().dataset.fieldobjs[index.column()]
        if field.editor == field.CheckBoxEditor:
            checked = index.data().toBool()
            check_box_style_option = QtGui.QStyleOptionButton()
            #Handle editable and enabled flags
            if not (index.flags() & QtCore.Qt.ItemIsEditable):
                check_box_style_option.state |= QtGui.QStyle.State_ReadOnly
            if index.flags() & QtCore.Qt.ItemIsEnabled:
                check_box_style_option.state |= QtGui.QStyle.State_Enabled

            #Set the check state
            if checked:
                check_box_style_option.state |= QtGui.QStyle.State_On
            else:
                check_box_style_option.state |= QtGui.QStyle.State_Off

            check_box_style_option.rect = self.getCheckBoxRect(option)

            #Paint the box then restore the painter
            painter.save()
            QtGui.QApplication.style().drawControl(QtGui.QStyle.CE_CheckBox,
                                                   check_box_style_option,
                                                   painter)
            painter.restore()
        else:
            QtGui.QStyledItemDelegate.paint(self, painter, option, index)

    def createEditor(self, parent, option, index):
        """Re-implemented to allow for non-standard cell editors"""
        field = index.model().dataset.fieldobjs[index.column()]
        if field.editor == field.DateEditEditor:
            de = QtGui.QDateEdit(parent)
            return de
        elif field.editor == field.DoubleSpinBoxEditor:
            spinbox = QtGui.QDoubleSpinBox(parent)
            spinbox.setDecimals(3)
            return spinbox
        elif field.editor == field.CheckBoxEditor:
            #Checkbox has no editor since it is its own editor
            return
        else:
            return QtGui.QStyledItemDelegate.createEditor(self, parent,
                                                          option, index)

    def setEditorData(self, editor, index):
        field = index.model().dataset.fields[index.column()]
        fieldobj = index.model().dataset.getFieldByName(field)
        feditor = fieldobj.editor
        data = index.model().data(index, QtCore.Qt.DisplayRole)
        if data:
            text = data.toString()
        else:
            text = ''
        if feditor == fieldobj.ComboBoxEditor:
            editor.lineEdit().setText(text)
        elif feditor == fieldobj.DateEditEditor:
            editor.setDate(QtCore.QDate.fromString(text,
                                                   'MM/dd/yyyy'))
        else:
            QtGui.QStyledItemDelegate.setEditorData(self, editor, index)

    def editorEvent(self, event, model, option, index):
        """Re-implemented to handle the checkbox as an editor"""
        field = index.model().dataset.fieldobjs[index.column()]
        if field.editor == field.CheckBoxEditor:
            # Change the data in the model and the state of the check box
            # if the user presses the left mouse button or presses
            # Key_Space or Key_Select and this cell is editable.
            # Otherwise do nothing.
            if not (index.flags() & QtCore.Qt.ItemIsEditable):
                return False

            # Do not change the check box-state
            if (event.type() == QtCore.QEvent.MouseButtonRelease or
                event.type() == QtCore.QEvent.MouseButtonDblClick):
                if (event.button() != QtCore.Qt.LeftButton or not
                    self.getCheckBoxRect(option).contains(event.pos())):
                    return False
                if event.type() == QtCore.QEvent.MouseButtonDblClick:
                    return True
            elif event.type() == QtCore.QEvent.KeyPress:
                if (event.key() != QtCore.Qt.Key_Space and
                    event.key() != QtCore.Qt.Key_Select):
                    return False
            else:
                return False

            # Change the check box-state
            self.setModelData(None, model, index)
            return True
        else:
            return QtGui.QStyledItemDelegate.editorEvent(self, event, model,
                                                   option, index)

    def setModelData(self, editor, model, index):
        field = index.model().dataset.fieldobjs[index.column()]
        if field.editor == field.CheckBoxEditor:
            value = index.data().toBool()
            newValue = not value
            model.setData(index, QtCore.QVariant(newValue), QtCore.Qt.EditRole)
        else:
            QtGui.QStyledItemDelegate.setModelData(self, editor, model, index)
        # Emit dataChanged here for all indices because if this field is
        # being copied the check box editor doesn't refresh the entire view
        # and then there will be a lag in the update of the copied data.
        model.dataChanged.emit(QtCore.QModelIndex(), QtCore.QModelIndex())

    def getCheckBoxRect(self, option):
        """Returns the QRect for the given checkbox style option"""
        check_box_style_option = QtGui.QStyleOptionButton()
        check_box_rect = QtGui.QApplication.style().subElementRect(QtGui.QStyle.SE_CheckBoxIndicator, check_box_style_option, None)
        check_box_point = QtCore.QPoint(option.rect.x() +
                            option.rect.width() / 2 -
                            check_box_rect.width() / 2,
                            option.rect.y() +
                            option.rect.height() / 2 -
                            check_box_rect.height() / 2)
        return QtCore.QRect(check_box_point, check_box_rect.size())


class mileageTable(QtGui.QTableView):
    """ Subclass to provide minimal custom functionality """

    def selectCell(self, index):
        """ Select the cel at the given index """
        smodel = self.selectionModel()
        smodel.select(index, smodel.ClearAndSelect)
