import settings
import pandas as pd
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import Qt
from additional import AbstractDataFrameModel


# -------------------- QTableView --------------------
class ShipmentListView(QtWidgets.QTableView):
    def keyPressEvent(self, e: QtGui.QKeyEvent) -> None:
        selected = self.selectedIndexes()[0] if self.selectedIndexes() else None
        move_step = 0

        if selected:
            if e.key() == Qt.Key_Enter:         # select next on Enter
                self.selectRow(selected.row() + 1)
            elif e.key() == Qt.Key_Down:
                if e.modifiers() == Qt.ShiftModifier:           # one row down on SHIFT + DOWN
                    move_step = 1
                elif e.modifiers() == Qt.AltModifier:           # one box row down on ALT + DOWN
                    move_step = settings.default_box_options.get('columns')
                elif e.modifiers() == Qt.ControlModifier:       # at the bottom on CTRL + DOWN
                    move_step = self.model().rowCount() - selected.row() - 1
            elif e.key() == Qt.Key_Up:
                if e.modifiers() == Qt.ShiftModifier:           # one row up on SHIFT + UP
                    move_step = -1
                elif e.modifiers() == Qt.AltModifier:           # one box row up on ALT + DOWN
                    move_step = -settings.default_box_options.get('columns')
                elif e.modifiers() == Qt.ControlModifier:       # at the top on CTRL + UP
                    move_step = -selected.row()

        if move_step:
            destination = self.model().index(selected.row() + move_step, selected.column())
            self.model().move_row_to(selected, destination)
            self.selectRow(selected.row() + move_step)
            return

        super(ShipmentListView, self).keyPressEvent(e)

    def currentChanged(self, current: QtCore.QModelIndex, previous: QtCore.QModelIndex) -> None:
        # if current.row() == previous.row():
        index = self.model().index(current.row(), self.model().weight_column_index)

        self.setCurrentIndex(index)
        super(ShipmentListView, self).currentChanged(current, previous)


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
        # elif role == Qt.BackgroundColorRole:
        #     return QtGui.QColor(50, 50, 50, 50)
        # if role == Qt.FontRole:
        #     return QFont('Courier New')

    @property
    def weight_column_index(self):
        """ Return index of column named settings.weight_column """
        return self.df.columns.get_loc(settings.weight_column)

    @property
    def code_column_index(self):
        """ Return index of column named settings.code_column """
        return self.df.columns.get_loc(settings.code_column)

    def move_row_to(self, source: QtCore.QModelIndex, destination: QtCore.QModelIndex):
        """ Move row from source to destination and updates dependent model """
        if not source.isValid() or not destination.isValid():
            return False

        index = self.df.index.to_list()
        item = index.pop(source.row())
        index.insert(destination.row(), item)
        self.df = self.df.reindex(index).reset_index(drop=True)

        # self._update_dependent_models()
        self._update_dependent_models(self.index(source.row(), 0), self.index(destination.row(), 0))
        return True

    def insert_row_at(self, row: int, data: pd.Series):
        """ Insert data at row index """
        df_a = self.df.iloc[:row]
        df_b = self.df.iloc[row:]
        self.df = df_a.append(data, ignore_index=True).append(df_b).reset_index(drop=True)
        self._update_dependent_models()


# -------------------- QStyledItemDelegate --------------------
# class ShipmentListDelegate(QtWidgets.QStyledItemDelegate):
#     def editorEvent(self, event: QtCore.QEvent, model: QtCore.QAbstractItemModel,
#                     option: 'QtWidgets.QStyleOptionViewItem', index: QtCore.QModelIndex) -> bool:
#         return super(ShipmentListDelegate, self).editorEvent(event, model, option, index)
#
#     def createEditor(self, parent: QtWidgets.QWidget, option: 'QtWidgets.QStyleOptionViewItem',
#                      index: QtCore.QModelIndex) -> QtWidgets.QWidget:
#         return super(ShipmentListDelegate, self).createEditor(parent, option, index)
