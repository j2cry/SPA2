import pandas as pd
from PyQt5 import QtWidgets
from PyQt5.QtCore import QAbstractTableModel, Qt
from PyQt5.QtGui import QFont


class ShipmentModel(QAbstractTableModel):
    def __init__(self, df: pd.DataFrame, model_type):
        QAbstractTableModel.__init__(self)
        self.model_type = model_type
        self._data = df

    def rowCount(self, parent=None):
        return self._data.shape[0]

    def columnCount(self, parent=None):
        return self._data.shape[1]

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return
        if role == Qt.DisplayRole:
            return str(self._data.iloc[index.row(), index.column()])

        if role == Qt.TextAlignmentRole:
            # for first column in list-model set left text alignment
            if (self.model_type == 'list') and (index.column() == 0):
                return Qt.AlignVCenter
            return Qt.AlignCenter
        # if (self.model_type == 'map') and (role == Qt.TextWordWrap):
        #     return True
        # if role == Qt.FontRole:
        #     return QFont('Courier New')

    def headerData(self, col: int, orientation: Qt.Orientation, role: int = ...):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self._data.columns[col]
        return None

    @property
    def df(self):
        return self._data

    @df.setter
    def df(self, value):
        self._data = value
