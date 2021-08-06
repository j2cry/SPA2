import typing
from collections import namedtuple
from string import ascii_lowercase

import pandas as pd
import numpy as np
from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.Qt import Qt

# ----------------- default parameters -----------------
BoxOptions = namedtuple('BoxOptions', 'rows columns separator')
default_box_options = {'rows': 9,
                       'columns': 9,
                       'separator': 2}

code_column = 'Код'
weight_column = 'Weight'
default_columns = (code_column, 'st0', 'st1', 'st2', 'st3', 'st4', weight_column)
color_unpacked = (200, 10, 10, 50)      # RGBA cell background color without `space` symbol: that means it's unpacked
color_packed = (10, 200, 10, 50)        # RGBA cell background color with `space` symbol: that means it's packed


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
        self.map_columns = kwargs.get('map_columns', list(ascii_lowercase[:self.box_options.columns]))

        self.list_model = ShipmentListModel(df, self.__update_map)
        # self.list_model.dataChanged.connect(self.__update_map)      # for updating map on ListView edit
        self.map_model = ShipmentMapModel(self.list_to_map())

        self.code_column_index = self.list_model.df.columns.get_loc(code_column)
        self.weight_column_index = self.list_model.df.columns.get_loc(weight_column)

    def __update_map(self, index: QtCore.QModelIndex):
        """ Update shipment map if list item was changed """
        # collect value
        weight = self.list_model.df.loc[index.row(), weight_column]
        code = self.list_model.df.loc[index.row(), code_column]
        value = f'{code} {weight}' if weight else code
        # create QModelIndex and set data
        map_index = self.item_position(index.row())
        self.map_model.setData(map_index, value, Qt.EditRole)
        self.map_model.dataChanged.emit(map_index, map_index, [Qt.DisplayRole])

    @property
    def box_amount(self):
        """ Return amount of required boxes """
        return str(np.ceil(self.list_model.df.shape[0] /
                           (self.box_options.columns * self.box_options.rows)).astype('int'))

    def list_to_map(self) -> pd.DataFrame:      # todo IT'S VERY SLOW
        """ Convert samples list (Series) to shipment map (DataFrame)"""
        samples = self.list_model.df[code_column].copy()
        weights = self.list_model.df[weight_column]
        weight_exists = weights != ''
        samples.loc[weight_exists] += ' ' + weights.loc[weight_exists]

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
        """ Load shipment list from DataFrame and build shipment map """
        # if target columns was not found --> exit
        if any([col not in df.columns for col in self.columns if col != weight_column]):
            return 'ERROR! Cannot find one or more required columns in selected file!'
        df[weight_column] = ''
        self.list_model.df = df[self.columns]
        self.map_model.df = self.list_to_map()

    def item_position(self, row: int, column=None):
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

    def set_weight(self, index: int, weight: str):
        """ Set weight to item by its index in list """
        # create QModelIndex
        list_index = self.list_model.index(index, self.weight_column_index)
        self.list_model.setData(list_index, weight, Qt.EditRole)

    def move_row(self, source: QtCore.QModelIndex, destination: QtCore.QModelIndex) -> bool:
        """ Move row from source to destination.
            Attention! This function drops selection! """
        # TODO: IT'S VERY SLOW!!!
        if not source.isValid() or not destination.isValid():
            return False

        index = self.list_model.df.index.to_list()
        item = index.pop(source.row())
        index.insert(destination.row(), item)
        self.list_model.df = self.list_model.df.reindex(index)
        self.map_model.df = self.list_to_map()
        return True


# ------------------- model classes --------------------
class AbstractDataFrameModel(QtCore.QAbstractTableModel):
    """ Parent abstract DataFrame-based model class for QTableView (map and list) """
    def __init__(self, df: pd.DataFrame, update_function: typing.Callable = None):
        """ Initialize model
            :param df
                model data as DataFrame
            :param update_function(index: QModelIndex):
                function for updating dependent models;
                specify this for the model that is being edited by the user (by default, ListModel), so that the
                changes are translated to the dependent models (MapModel)
        """
        super(AbstractDataFrameModel, self).__init__()
        self._df = None
        self._df = df
        self._update_dependent_models = update_function

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
            # call function to update dependent models
            if self._update_dependent_models is not None:
                self._update_dependent_models(index)
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
        flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable
        if (index.column() == self.df.columns.get_loc(code_column)) or \
                (index.column() == self.df.columns.get_loc(weight_column)):   # 0: Code; 6: Weight
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
                return QtGui.QColor(*color_packed) if value.find(' ') > 0 else QtGui.QColor(*color_unpacked)
        # if role == Qt.FontRole:
        #     return QFont('Courier New')


class ShipmentListDelegate(QtWidgets.QStyledItemDelegate):
    def editorEvent(self, event: QtCore.QEvent, model: QtCore.QAbstractItemModel,
                    option: 'QtWidgets.QStyleOptionViewItem', index: QtCore.QModelIndex) -> bool:
        if (event.type() == QtCore.QEvent.KeyPress) and index.column() != 6:
            return True

        return super(ShipmentListDelegate, self).editorEvent(event, model, option, index)

    # def createEditor(self, parent: QtWidgets.QWidget, option: 'QtWidgets.QStyleOptionViewItem',
    #                  index: QtCore.QModelIndex) -> QtWidgets.QWidget:
    #     return super(ShipmentListDelegate, self).createEditor(parent, option, index)
