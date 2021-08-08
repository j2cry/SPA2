import settings
import pandas as pd
import numpy as np
from string import ascii_lowercase
from PyQt5 import QtCore
from PyQt5.Qt import Qt
from additional import BoxOptions, range_generator
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

        self.update_ui_func = None
        # if df is not specified generate new one with given columns
        df = kwargs.get('df', pd.DataFrame(columns=kwargs.get('columns', settings.default_columns)))
        self.columns = df.columns
        self.map_columns = kwargs.get('map_columns', list(ascii_lowercase[:self.box_options.columns]))

        self.list_model = ShipmentListModel(df, self.__update_map_value)
        self.map_model = ShipmentMapModel(self.list_to_map(), self.__map_index_validate)
        self.number = ''

    def bind_ui_updater(self, func):
        """ Bind function to update UI """
        self.update_ui_func = func

    def __update_map_value(self, start: QtCore.QModelIndex = None, end: QtCore.QModelIndex = None):
        """ Update shipment map cell value according to list item at index.
            If index is not specified rebuild map """
        if start and end:
            # weights = self.list_model.df.loc[start.row():end.row(), settings.weight_column]
            # codes = self.list_model.df.loc[start.row():end.row(), settings.code_column]
            for i in range_generator(start.row(), end.row(), endpoint=True):
                weight = self.list_model.df.loc[i, settings.weight_column]
                code = self.list_model.df.loc[i, settings.code_column]
                value = f'{code} {weight}' if weight else code
                map_index = self.item_position(i)
                self.map_model.setData(map_index, value, Qt.EditRole)

            map_start = self.item_position(start.row())
            map_end = self.item_position(end.row())
            self.map_model.dataChanged.emit(map_start, map_end, [Qt.DisplayRole])
        if start:
            # collect value
            weight = self.list_model.df.loc[start.row(), settings.weight_column]
            code = self.list_model.df.loc[start.row(), settings.code_column]
            value = f'{code} {weight}' if weight else code
            # create QModelIndex and set data
            map_index = self.item_position(start.row())
            self.map_model.setData(map_index, value, Qt.EditRole)
            self.map_model.dataChanged.emit(map_index, map_index, [Qt.DisplayRole])
        else:
            self.map_model.df = self.list_to_map()

    def __map_index_validate(self, index: QtCore.QModelIndex) -> bool:
        """ Validates map index according to list data """
        return self.item_position(index.row(), index.column()).isValid()

    @property
    def box_amount(self):
        """ Return amount of required boxes """
        return str(np.ceil(self.list_model.df.shape[0] /
                           (self.box_options.columns * self.box_options.rows)).astype('int'))

    def list_to_map(self, export_mode=False) -> pd.DataFrame:
        """ Convert samples list (Series) to shipment map (DataFrame)"""
        samples = self.list_model.df[settings.code_column].copy()
        weights = self.list_model.df[settings.weight_column]
        weight_exists = weights != ''
        samples.loc[weight_exists] += ' ' + weights.loc[weight_exists]

        array, indexes = [], []
        box_capacity = self.box_options.rows * self.box_options.columns
        max_samples = samples.size if not export_mode else int(np.ceil(samples.size / box_capacity)) * box_capacity
        for index in range_generator(0, max_samples, self.box_options.columns):
            row = (index // self.box_options.columns) % self.box_options.rows + 1
            if export_mode and (row % self.box_options.rows) == 1:
                array.append(['', f'{self.number}.{int((index + 1) / box_capacity + 1)}'] +
                             [''] * (len(self.map_columns) - 2))
                array.append(self.map_columns)
                indexes.extend([np.NaN, np.NaN])

            row_values = samples.values[index:index + self.box_options.columns]
            if (delta := len(self.map_columns) - row_values.size) > 0:      # ?len(array) == 0 and
                row_values = np.append(row_values, [''] * delta)
            array.append(row_values)
            indexes.append(row)
            # add separators
            if row == self.box_options.rows:
                array.extend([[''] * self.box_options.columns] * self.box_options.separator)
                indexes.extend([''] * self.box_options.separator)

        if self.update_ui_func:
            self.update_ui_func()
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
            return self.list_model.index(*index) if row_in_box < self.box_options.rows else QtCore.QModelIndex()
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
