import settings
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import Qt
from additional import AbstractDataFrameModel


# -------------------- QTableView --------------------
class ShipmentListView(QtWidgets.QTableView):
    def keyPressEvent(self, e: QtGui.QKeyEvent) -> None:
        if e.key() == Qt.Key_Enter:         # select next on Enter
            row = self.selectedIndexes()[0].row()
            self.selectRow(row + 1)
        super(ShipmentListView, self).keyPressEvent(e)

    def currentChanged(self, current: QtCore.QModelIndex, previous: QtCore.QModelIndex) -> None:
        # if current.row() == previous.row():
        index = self.model().index(current.row(), self.model().weight_column_index)
        self.setCurrentIndex(index)


# -------------------- QAbstractTableModel --------------------
class ShipmentListModel(AbstractDataFrameModel):
    """ Model for shipment list """
    def flags(self, index: QtCore.QModelIndex) -> Qt.ItemFlags:
        flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable
        if (index.column() == self.code_column_index) or \
                (index.column() == self.weight_column_index):
            return Qt.ItemFlags(flags | Qt.ItemIsEditable)
        else:
            return Qt.ItemFlags(flags)

    def data(self, index: QtCore.QModelIndex, role=Qt.DisplayRole):
        if not index.isValid():
            return
        elif (role == Qt.DisplayRole) or (role == Qt.EditRole):
            return str(self._df.iloc[index.row(), index.column()])
        elif role == Qt.TextAlignmentRole:        # for first column in list set left text alignment
            return Qt.AlignVCenter if index.column() == 0 else Qt.AlignCenter
        # if role == Qt.FontRole:
        #     return QFont('Courier New')

    @property
    def weight_column_index(self):
        return self.df.columns.get_loc(settings.weight_column)

    @property
    def code_column_index(self):
        return self.df.columns.get_loc(settings.code_column)


# -------------------- QStyledItemDelegate --------------------
# class ShipmentListDelegate(QtWidgets.QStyledItemDelegate):
#     def editorEvent(self, event: QtCore.QEvent, model: QtCore.QAbstractItemModel,
#                     option: 'QtWidgets.QStyleOptionViewItem', index: QtCore.QModelIndex) -> bool:
#         return super(ShipmentListDelegate, self).editorEvent(event, model, option, index)
#
#     def createEditor(self, parent: QtWidgets.QWidget, option: 'QtWidgets.QStyleOptionViewItem',
#                      index: QtCore.QModelIndex) -> QtWidgets.QWidget:
#         return super(ShipmentListDelegate, self).createEditor(parent, option, index)
