import settings
import typing
import pandas as pd
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.Qt import Qt
from additional import AbstractDataFrameModel, range_generator, PositionStatus


# -------------------- QTableView --------------------
class ShipmentMapView(QtWidgets.QTableView):
    def selectionCommand(self, index: QtCore.QModelIndex, event: typing.Optional[QtCore.QEvent] = ...) \
            -> QtCore.QItemSelectionModel.SelectionFlags:
        if not index.isValid():
            return super(ShipmentMapView, self).selectionCommand(index, event)
        pos_status = self.model().position_status_func(index)
        if (pos_status == PositionStatus.PACKED_SAMPLE) or (pos_status == PositionStatus.UNPACKED_SAMPLE):
            return super(ShipmentMapView, self).selectionCommand(index, event)
        else:
            return QtCore.QItemSelectionModel.SelectionFlags(QtCore.QItemSelectionModel.Deselect)

    def dataChanged(self, topLeft: QtCore.QModelIndex, bottomRight: QtCore.QModelIndex,
                    roles: typing.Iterable[int] = ...) -> None:
        for row in range_generator(topLeft.row(), bottomRight.row() + 1):
            self.resizeRowToContents(row)
        super(ShipmentMapView, self).dataChanged(topLeft, bottomRight, roles)


# -------------------- QAbstractTableModel --------------------
class ShipmentMapModel(AbstractDataFrameModel):
    """ Model for shipment map """
    def __init__(self, df: pd.DataFrame, position_status_func: typing.Callable):
        """ :param index_validate(index: QModelIndex) -> bool
                function for validating indexes according to ListModel """
        super(ShipmentMapModel, self).__init__(df)
        self.position_status_func = position_status_func

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
            pos_status = self.position_status_func(index)
            if pos_status == PositionStatus.PACKED_SAMPLE:
                return QtGui.QColor(*settings.color_packed)
            elif pos_status == PositionStatus.UNPACKED_SAMPLE:
                return QtGui.QColor(*settings.color_unpacked)
            elif pos_status == PositionStatus.FREE:
                return QtGui.QColor(*settings.color_free)
            elif pos_status == PositionStatus.SEPARATOR:
                return QtGui.QColor(*settings.color_separator)
        # if role == Qt.FontRole:
        #     return QFont('Courier New')
