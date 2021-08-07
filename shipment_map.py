import typing

import pandas as pd

import settings
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.Qt import Qt
from additional import AbstractDataFrameModel


# -------------------- QTableView --------------------
class ShipmentMapView(QtWidgets.QTableView):
    def selectionCommand(self, index: QtCore.QModelIndex, event: typing.Optional[QtCore.QEvent] = ...) \
            -> QtCore.QItemSelectionModel.SelectionFlags:
        if not self.model().index_validate(index):
            return QtCore.QItemSelectionModel.SelectionFlags(QtCore.QItemSelectionModel.Deselect)
        else:
            return super(ShipmentMapView, self).selectionCommand(index, event)

    # def selectionChanged(self, selected: QtCore.QItemSelection, deselected: QtCore.QItemSelection) -> None:
    #     if not selected or not deselected:
    #         return
    #     if self.model().data(selected.indexes()[0]) == '':
    #         self.clearSelection()
    #         # self.selectionModel().select(deselected.indexes()[0], QtCore.QItemSelectionModel.ClearAndSelect)
    #     # super(ShipmentMapView, self).selectionChanged(selected, deselected)


# -------------------- QAbstractTableModel --------------------
class ShipmentMapModel(AbstractDataFrameModel):
    """ Model for shipment map """
    def __init__(self, df: pd.DataFrame, index_validate: typing.Callable):
        """ :param index_validate(index: QModelIndex) -> bool
                function for validating indexes according to ListModel """
        super(ShipmentMapModel, self).__init__(df)
        self.index_validate = index_validate

    def data(self, index: QtCore.QModelIndex, role=Qt.DisplayRole):
        if not index.isValid():
            return
        if role == Qt.DisplayRole:
            return str(self._df.iloc[index.row(), index.column()])
        elif role == Qt.TextAlignmentRole:
            return Qt.AlignCenter
        elif role == Qt.TextWordWrap:
            return True
        elif role == Qt.BackgroundColorRole:
            if self.index_validate(index):
                return QtGui.QColor(*settings.color_packed) \
                    if self.data(index).find(' ') > 0 else QtGui.QColor(*settings.color_unpacked)
            else:
                return QtGui.QColor(*settings.color_na)
        # if role == Qt.FontRole:
        #     return QFont('Courier New')
