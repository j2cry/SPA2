import settings
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.Qt import Qt
from additional import AbstractDataFrameModel


# -------------------- QTableView --------------------
class ShipmentMapView(QtWidgets.QTableView):
    pass


# -------------------- QAbstractTableModel --------------------
class ShipmentMapModel(AbstractDataFrameModel):
    """ Model for shipment map """
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
            if value := self.data(index):
                return QtGui.QColor(*settings.color_packed) \
                    if value.find(' ') > 0 else QtGui.QColor(*settings.color_unpacked)
        # if role == Qt.FontRole:
        #     return QFont('Courier New')
