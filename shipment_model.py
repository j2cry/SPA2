import settings
import pandas as pd
import numpy as np
from string import ascii_lowercase
from PyQt5 import QtCore
from PyQt5.Qt import Qt
from additional import BoxOptions, range_generator, PositionStatus
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

        self.list_model = ShipmentListModel(df)
        self.map_model = ShipmentMapModel(self.list_to_map(), self.get_position_status)
        self.list_model.dataChanged.connect(self.update_map_value)

        self.number = ''

    def update_map_value(self, first_index: QtCore.QModelIndex, last_index: QtCore.QModelIndex):
        """ Update shipment map cell value according to list item at index.
            If index is not specified rebuild map """
        # convert list indexes to map indexes
        start_map_index = self.item_position(first_index.row())
        end_map_index = self.item_position(last_index.row())

        if first_index == last_index:
            # collect value
            weight = self.list_model.df.loc[first_index.row(), settings.weight_column]
            code = self.list_model.df.loc[first_index.row(), settings.code_column]
            value = f'{code} {weight}' if weight else code
            self.map_model.setData(start_map_index, value, Qt.EditRole)
        else:
            self.map_model.df = self.list_to_map()
        # todo вернуть итерацию по части карты? - будет ли быстрее?
        # if not start_map_index.isValid() or not end_map_index.isValid():
        #     self.map_model.df = self.list_to_map()
        #     return
        # #     # тут надо собирать карту - с индексами и прочей поеботой
        # #
        # self.map_model.beginResetModel()
        # for row_number in range_generator(start.row(), end.row(), endpoint=True):
        #     # collect info
        #     weight = self.list_model.df.loc[row_number, settings.weight_column]
        #     code = self.list_model.df.loc[row_number, settings.code_column]
        #     value = f'{code} {weight}' if weight else code
        #     # set data to map
        #     map_index = self.item_position(row_number)
        #     self.map_model.setData(map_index, value, Qt.EditRole)
        # self.map_model.endResetModel()
        # #
        # #     # self.map_model.df = self.list_to_map()
        # #     # pass

    def get_position_status(self, map_index: QtCore.QModelIndex) -> PositionStatus:
        """ Determine whether index refers to sample, free box place or separator """
        list_index = self.item_position(map_index.row(), map_index.column())
        if list_index.isValid():
            weight = self.list_model.df.iloc[list_index.row(), self.list_model.weight_column_index]
            return PositionStatus.PACKED_SAMPLE if weight else PositionStatus.UNPACKED_SAMPLE
        elif self.map_model.df.index[map_index.row()] != '':
            return PositionStatus.FREE
        else:
            return PositionStatus.SEPARATOR

    @property
    def box_amount(self):
        """ Return amount of required boxes """
        return str(np.ceil(self.list_model.df.shape[0] /
                           (self.box_options.columns * self.box_options.rows)).astype('int'))

    # DEPRECATED
    # def list_to_map(self, export_mode=False) -> pd.DataFrame:
    #     """ Convert samples list (Series) to shipment map (DataFrame)"""
    #     samples = self.list_model.df[settings.code_column].copy()
    #     weights = self.list_model.df[settings.weight_column]
    #     weight_exists = weights != ''
    #     samples.loc[weight_exists] += ' ' + weights.loc[weight_exists]
    #
    #     array, indexes = [], []
    #     box_capacity = self.box_options.rows * self.box_options.columns
    #     max_samples = samples.size if not export_mode else int(np.ceil(samples.size / box_capacity)) * box_capacity
    #     for index in range_generator(0, max_samples, self.box_options.columns):
    #         row = (index // self.box_options.columns) % self.box_options.rows + 1
    #         if export_mode and (row % self.box_options.rows) == 1:
    #             array.append(['', f'{self.number}.{int((index + 1) / box_capacity + 1)}'] +
    #                          [''] * (len(self.map_columns) - 2))
    #             array.append(self.map_columns)
    #             indexes.extend([np.NaN, np.NaN])
    #
    #         row_values = samples.values[index:index + self.box_options.columns]
    #         if (delta := len(self.map_columns) - row_values.size) > 0:      # ?len(array) == 0 and
    #             row_values = np.append(row_values, [''] * delta)
    #         array.append(row_values)
    #         indexes.append(row)
    #         # add separators
    #         if row == self.box_options.rows:
    #             array.extend([[''] * self.box_options.columns] * self.box_options.separator)
    #             indexes.extend([''] * self.box_options.separator)
    #
    #     return pd.DataFrame(array, index=indexes, columns=self.map_columns).fillna('')

    def list_to_map(self, export_mode=False) -> pd.DataFrame:
        """ Convert samples list (Series) to shipment map (DataFrame) """
        samples = self.list_model.df[settings.code_column].copy()
        if not samples.size:
            return pd.DataFrame(columns=self.map_columns)
        weights = self.list_model.df[settings.weight_column]
        weight_exists = weights != ''
        samples.loc[weight_exists] += ' ' + weights.loc[weight_exists]
        del weights

        # fill list with zeroes to full boxes
        samples = samples.values
        box_capacity = self.box_options.rows * self.box_options.columns
        if (delta_size := (box_capacity - samples.size % box_capacity) % box_capacity) > 0:
            samples = np.append(samples, [''] * delta_size)

        # collect map data with separators and export headers if required
        map_data = np.empty((0, 9), dtype='str')
        for i in range(0, samples.size, box_capacity):
            # create header if required
            if export_mode:
                header = [['', f'{self.number}.{(i + 1) // box_capacity + 1}'] + [''] * (len(self.map_columns) - 2),
                          self.map_columns]
            else:
                header = np.empty((0, 9), dtype='str')
            # create separator if required
            if i + box_capacity <= samples.size:
                separators = np.empty((self.box_options.separator, self.box_options.columns), dtype='str')
            else:
                separators = np.empty((0, 9), dtype='str')
            # collect box data
            box_data = samples[i:i + box_capacity].reshape((-1, self.box_options.columns))
            # stack 'em all
            map_data = np.vstack((map_data, header, box_data, separators))

        # create index
        index = [i + 1 for i in range(self.box_options.rows)] + [''] * self.box_options.separator
        if export_mode:
            index = [''] * 2 + index
        index *= samples.size // box_capacity

        return pd.DataFrame(map_data, columns=self.map_columns, index=index)

    def load(self, df: pd.DataFrame):
        """ Load shipment list from DataFrame and build shipment map """
        # if target columns was not found --> exit
        if any([col not in df.columns for col in self.columns if col != settings.weight_column]):
            return 'ERROR! Cannot find one or more required columns in selected file!'
        df[settings.weight_column] = ''
        self.list_model.df = df[self.columns]

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
