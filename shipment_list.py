import settings
import pandas as pd
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import Qt
from additional import AbstractDataFrameModel, Direction, validate_selection


# -------------------- QTableView --------------------
class ShipmentListView(QtWidgets.QTableView):
    def keyPressEvent(self, e: QtGui.QKeyEvent) -> None:
        selected = self.selectedIndexes()[0] if self.selectedIndexes() else None

        if selected:
            if e.key() == Qt.Key_Enter:         # select next on Enter
                self.selectRow(selected.row() + 1)
            # moving row
            elif ((down := (e.key() == Qt.Key_Down)) or not (down := (e.key() != Qt.Key_Up))) \
                    and e.modifiers() != Qt.NoModifier:
                self.move_row(Direction.FORWARD if down else Direction.BACKWARD, modifiers=e.modifiers())
                return
            # inserting row
            elif e.key() == Qt.Key_Insert:
                self.insert_free_row(modifiers=e.modifiers())
            # removing row
            elif (e.key() == Qt.Key_Delete) and (e.modifiers() == Qt.ShiftModifier):
                self.remove_row(selected.row())
        super(ShipmentListView, self).keyPressEvent(e)

    def currentChanged(self, current: QtCore.QModelIndex, previous: QtCore.QModelIndex) -> None:
        index = self.model().index(current.row(), self.model().weight_column_index)
        self.setCurrentIndex(index)
        super(ShipmentListView, self).currentChanged(current, previous)

    @validate_selection()
    def move_row(self, direction: Direction, modifiers=QtWidgets.QApplication.keyboardModifiers(), *, selected=None):
        """ Move selected row to direction by step """
        move_step = 0
        if direction == Direction.BACKWARD:
            if modifiers == Qt.ShiftModifier:  # one row up on SHIFT + UP
                move_step = -settings.move_step[0]
            elif modifiers == Qt.AltModifier:  # one box row up on ALT + DOWN
                move_step = -settings.move_step[1]
            elif modifiers == Qt.ControlModifier:  # at the top on CTRL + UP
                move_step = -selected.row()
        elif direction == Direction.FORWARD:
            if modifiers == Qt.ShiftModifier:  # one row up on SHIFT + UP
                move_step = settings.move_step[0]
            elif modifiers == Qt.AltModifier:  # one box row up on ALT + DOWN
                move_step = settings.move_step[1]
            elif modifiers == Qt.ControlModifier:  # at the top on CTRL + UP
                move_step = self.model().rowCount() - selected.row() - 1
        if move_step:
            destination = self.model().index(selected.row() + move_step, selected.column())
            self.model().move_row_to(selected.row(), destination.row())
            self.selectRow(selected.row() + move_step)
            return True
        else:
            return False

    @validate_selection()
    def insert_free_row(self, modifiers=QtWidgets.QApplication.keyboardModifiers(), *, keep_selection: bool = True,
                        selected: QtCore.QModelIndex = None):
        """ Insert one free row to direction and keeps selection back if required """
        # check if SHIFT is pressed
        direction = Direction.FORWARD if (int(modifiers) & Qt.ShiftModifier) == Qt.ShiftModifier else Direction.BACKWARD
        # check if ALT is pressed
        rows_amount = settings.insert_many if (int(modifiers) & Qt.AltModifier) == Qt.AltModifier else 1

        columns_count = self.model().df.shape[1]
        data = pd.DataFrame([[''] + ['-'] * (columns_count - 2) + ['']] * rows_amount, columns=self.model().df.columns)
        self.model().insert_row_at(selected.row() + direction[0], data)
        if keep_selection:
            self.selectRow(selected.row() + direction[1] * rows_amount)

    @validate_selection()
    def remove_row(self, *args, keep_selection: bool = True, selected: QtCore.QModelIndex = None):
        """ Remove selected row """
        self.model().remove_row_at(selected.row())
        if keep_selection:
            row = row if (row := selected.row()) < self.model().rowCount() else row - 1
            self.selectRow(row)


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
        """ Return index of column named settings.weight_column """
        return self.df.columns.get_loc(settings.weight_column)

    @property
    def code_column_index(self):
        """ Return index of column named settings.code_column """
        return self.df.columns.get_loc(settings.code_column)

    def move_row_to(self, source: int, destination: int):
        """ Move row from source to destination and updates dependent model """
        source_index = self.index(source, 0)
        destination_index = self.index(destination, 0)
        if not source_index.isValid() or not destination_index.isValid():
            return False

        index = self.df.index.to_list()
        item = index.pop(source)
        index.insert(destination, item)
        self.df = self.df.reindex(index).reset_index(drop=True)
        self._update_dependent_models(source_index, destination_index)
        return True

    def insert_row_at(self, row: int, data: pd.Series):
        """ Insert data at row index """
        df_a = self.df.iloc[:row]
        df_b = self.df.iloc[row:]
        self.df = df_a.append(data, ignore_index=True).append(df_b).reset_index(drop=True)
        self._update_dependent_models()

    def remove_row_at(self, row: int):
        """ Remove row at row index """
        df_a = self.df.iloc[:row]
        df_b = self.df.iloc[row + 1:]
        self.df = df_a.append(df_b).reset_index(drop=True)
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
