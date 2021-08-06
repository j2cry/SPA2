import settings
import pandas as pd
import numpy as np
from string import ascii_lowercase
from PyQt5 import QtCore
from PyQt5.Qt import Qt
from additional import BoxOptions
from shipment_list import ShipmentListModel
from shipment_map import ShipmentMapModel


class ShipmentModel:
    """ Main class for operating with shipment data """
    def __init__(self, **kwargs):
        if len(kwargs.keys() & {'df', 'columns'}) > 1:
            raise ValueError('Only one keyword argument is allowed: df or columns.')

        # parse box options
        self.box_options = BoxOptions(*[v if k not in kwargs.keys() else kwargs.get(k)
                                        for k, v in settings.default_box_options.items()])

        # if df is not specified generate new one with given columns
        df = kwargs.get('df', pd.DataFrame(columns=kwargs.get('columns', settings.default_columns)))
        self.columns = df.columns
        self.map_columns = kwargs.get('map_columns', list(ascii_lowercase[:self.box_options.columns]))

        self.list_model = ShipmentListModel(df, self.__update_map_value)
        self.map_model = ShipmentMapModel(self.list_to_map())

    def __update_map_value(self, index: QtCore.QModelIndex):
        """ Update shipment map cell value according to list item at index """
        # collect value
        weight = self.list_model.df.loc[index.row(), settings.weight_column]
        code = self.list_model.df.loc[index.row(), settings.code_column]
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

    def list_to_map(self) -> pd.DataFrame:
        """ Convert samples list (Series) to shipment map (DataFrame)"""
        samples = self.list_model.df[settings.code_column].copy()
        weights = self.list_model.df[settings.weight_column]
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
        if any([col not in df.columns for col in self.columns if col != settings.weight_column]):
            return 'ERROR! Cannot find one or more required columns in selected file!'
        df[settings.weight_column] = ''
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
        list_index = self.list_model.index(index, self.list_model.weight_column_index)
        self.list_model.setData(list_index, weight, Qt.EditRole)
