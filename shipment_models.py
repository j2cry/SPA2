import typing
from collections import namedtuple
from string import ascii_lowercase

import pandas as pd
import numpy as np
from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.Qt import Qt

# ----------------- default parameters -----------------
BoxOptions = namedtuple('BoxOptions', 'rows columns separator')
default_box_options = {'rows': 9,
                       'columns': 9,
                       'separator': 2}

default_code_column = 'Код'
default_columns = (default_code_column, 'st0', 'st1', 'st2', 'st3', 'st4', 'Weight')


class ShipmentModel:
    """ Main class for operating with shipment data """
    def __init__(self, **kwargs):
        if len(kwargs.keys() & {'df', 'columns'}) > 1:
            raise ValueError('Only one keyword argument is allowed: df or columns.')

        # parse box options
        self.box_options = BoxOptions(*[v if k not in kwargs.keys() else kwargs.get(k)
                                        for k, v in default_box_options.items()])

        # if df is not specified generate new one with given columns
        df = kwargs.get('df', pd.DataFrame(columns=kwargs.get('columns', default_columns)))
        self.columns = df.columns
        self.code_column = kwargs.get('code_column', default_code_column)
        self.map_columns = kwargs.get('map_columns', list(ascii_lowercase[:self.box_options.columns]))

        self.list_model = ShipmentListModel(df)
        self.map_model = ShipmentMapModel(self.list_to_map())

    @property
    def box_amount(self):
        return str(np.ceil(self.list_model.df.shape[0] /
                           (self.box_options.columns * self.box_options.rows)).astype('int'))

    def list_to_map(self) -> pd.DataFrame:
        """ Convert samples list (Series) to shipment map (DataFrame)"""
        samples = self.list_model.df[self.code_column]
        weights = self.list_model.df['Weight']
        # add weight if it is set
        weight_exists = weights != ''
        # samples.loc[weight_exists] = samples[weight_exists] + ' ' + weights[weight_exists].values
        samples = samples + ' ' + weights

        array, indexes = [], []
        for index in range(0, samples.size, self.box_options.columns):
            row = (index // self.box_options.columns) % self.box_options.rows + 1
            array.append(samples.values[index:index + self.box_options.columns])
            indexes.append(row)
            # add separators
            if row == self.box_options.rows:
                array.extend([[''] * self.box_options.columns] * self.box_options.separator)
                indexes.extend([''] * self.box_options.separator)
        return pd.DataFrame(array, index=indexes, columns=self.map_columns).fillna('')

    def load(self, df: pd.DataFrame):
        # if target columns was not found --> exit
        if any([col not in df.columns for col in self.columns if col != 'Weight']):
            return 'ERROR! Cannot find one or more required columns in selected file!'
        df['Weight'] = ''
        self.list_model.df = df[self.columns]
        self.map_model.df = self.list_to_map()

    def item_position(self, row, column=None):
        """ Get item position in list/map by its indexes in map/list """
        box_capacity = self.box_options.rows * self.box_options.columns
        if column is not None:      # find in list by map indexes
            full_boxes = row // (self.box_options.rows + self.box_options.separator)
            row_in_box = row % (self.box_options.rows + self.box_options.separator)
            index = (full_boxes * box_capacity + row_in_box * self.box_options.columns + column, 0)
            return self.list_model.index(*index)
        else:                       # find in map by list index
            full_boxes = row // box_capacity
            row_in_map = (row // self.box_options.columns) + self.box_options.separator * full_boxes
            col_in_map = row % self.box_options.columns
            return self.map_model.index(row_in_map, col_in_map)

    def set_weight(self, index, weight: float):
        """ Set weight to item by its index in list """
        # translate index to map position
        row, col = self.item_position(index).row(), self.item_position(index).column()
        # create QItemIndex
        list_index = self.list_model.index(index, self.list_model.df.columns.get_loc('Weight'))
        map_index = self.map_model.index(row, col)
        # set data
        code = self.list_model.df.loc[index, self.code_column]
        weight = np.round(weight, 2)
        result = f'{code} {weight}' if weight else code
        self.list_model.setData(list_index, weight, Qt.EditRole)
        self.map_model.setData(map_index, result, Qt.EditRole)


# ------------------- model classes --------------------
class AbstractDataFrameModel(QtCore.QAbstractTableModel):
    def __init__(self, df: pd.DataFrame):
        super(AbstractDataFrameModel, self).__init__()
        self._df = None
        self._df = df

    def rowCount(self, parent=None):
        return self._df.shape[0]

    def columnCount(self, parent=None):
        return self._df.shape[1]

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = ...):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return self._df.columns[section]
            if orientation == Qt.Vertical:
                return str(self._df.index[section])
        if role == Qt.TextAlignmentRole:
            return Qt.AlignCenter

    def setData(self, index: QtCore.QModelIndex, value: typing.Any, role: int = ...) -> bool:
        if not index.isValid():
            return False

        if role == Qt.EditRole:
            self._df.iloc[index.row(), index.column()] = value
            self.dataChanged.emit(index, index, [Qt.DisplayRole])
            return True
        return False

    @property
    def df(self):
        return self._df

    @df.setter
    def df(self, value):
        # update whole model
        self.beginResetModel()
        self._df = value
        self.endResetModel()


class ShipmentListModel(AbstractDataFrameModel):
    """ Model for shipment list """
    def flags(self, index: QtCore.QModelIndex) -> Qt.ItemFlags:
        # TODO: set it in GUI designer?
        flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable
        if index.column() == 0:
            return Qt.ItemFlags(flags | Qt.ItemIsEditable)
        else:
            return Qt.ItemFlags(flags)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return

        if (role == Qt.DisplayRole) or (role == Qt.EditRole):
            return str(self._df.iloc[index.row(), index.column()])
        elif role == Qt.TextAlignmentRole:        # for first column in list set left text alignment
            return Qt.AlignVCenter if index.column() == 0 else Qt.AlignCenter
        # if role == Qt.FontRole:
        #     return QFont('Courier New')


class ShipmentMapModel(AbstractDataFrameModel):
    """ Model for shipment map, based on shipment list (ShipmentListModel) """
    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return

        if role == Qt.DisplayRole:
            return str(self._df.iloc[index.row(), index.column()])
        if role == Qt.TextAlignmentRole:
            return Qt.AlignCenter
        # if role == Qt.TextWordWrap:
        #     return True
        # if role == Qt.FontRole:
        #     return QFont('Courier New')


class ShipmentListDelegate(QtWidgets.QStyledItemDelegate):
    pass
    # def createEditor(self, parent: QtWidgets.QWidget, option: 'QtWidgets.QStyleOptionViewItem',
    #                  index: QtCore.QModelIndex) -> QtWidgets.QWidget:
    #     if index.column() == 0:
    #         editor = QtWidgets.QLineEdit()
    #     else:
    #         editor = None
    #     return editor

    # def paint(self, painter: QtGui.QPainter, option: 'QtWidgets.QStyleOptionViewItem', index: QtCore.QModelIndex):
    #     if index.column() == 0:
    #         return
    #     else:
    #         super(ShipmentListDelegate, self).paint(painter, option, index)
