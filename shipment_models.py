from collections import namedtuple
from string import ascii_lowercase

import pandas as pd
from PyQt5.QtCore import QAbstractTableModel, Qt

# ----------------- default parameters -----------------
BoxOptions = namedtuple('BoxOptions', 'rows columns separator')
default_box_options = {'rows': 9,
                       'columns': 9,
                       'separator': 2}

default_code_column = 'Код'
default_columns = (default_code_column, 'st0', 'st1', 'st2', 'st3', 'st4')


# ------------------- model classes --------------------
class ShipmentModel:
    def __init__(self, **kwargs):
        if len(kwargs.keys() & {'df', 'columns'}) > 1:
            raise ValueError('Only one keyword argument is required: df or columns.')

        # parse box options
        self.box_options = BoxOptions(*[v if k not in kwargs.keys() else kwargs.get(k)
                                        for k, v in default_box_options.items()])

        # if df is not specified generate new one with given columns
        df = kwargs.get('df', pd.DataFrame(columns=kwargs.get('columns', default_columns)))
        self.columns = df.columns
        self.code_column = kwargs.get('code_column', default_code_column)
        self.map_columns = kwargs.get('map_columns', list(ascii_lowercase[:self.box_options.columns]))

        self.list_model = ShipmentListModel(df)
        self.map_model = ShipmentMapModel(self.list_to_map(inplace=False))

    def list_to_map(self, *, inplace=True):
        """ Convert samples list (Series) to shipment map (DataFrame)"""
        samples = self.list_model.df[self.code_column]
        array, indexes = [], []
        for index in range(0, samples.size, self.box_options.columns):
            row = (index // self.box_options.columns) % self.box_options.rows + 1
            array.append(samples.values[index:index + self.box_options.columns])
            indexes.append(row)
            # add separators
            if row == self.box_options.rows:
                array.extend([[''] * self.box_options.columns] * self.box_options.separator)
                indexes.extend([''] * self.box_options.separator)

        df = pd.DataFrame(array, index=indexes, columns=self.map_columns).fillna('')
        if inplace:
            self.map_model.df = df
        else:
            return df

    def load(self, df: pd.DataFrame):
        # if target columns was not found --> exit
        if any([col not in df.columns for col in self.columns]):
            return 'ERROR! Cannot find one or more required columns in selected file!'
        self.list_model.df = df[self.columns]
        self.list_to_map()

    def box_amount(self):
        # TODO
        pass



class AbstractDataFrameModel(QAbstractTableModel):
    def __init__(self, df: pd.DataFrame):
        QAbstractTableModel.__init__(self)
        self._data = df

    def rowCount(self, parent=None):
        return self._data.shape[0]

    def columnCount(self, parent=None):
        return self._data.shape[1]

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = ...):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return self._data.columns[section]
            if orientation == Qt.Vertical:
                return str(self._data.index[section])
        if role == Qt.TextAlignmentRole:
            return Qt.AlignCenter

    @property
    def df(self):
        return self._data

    @df.setter
    def df(self, value):
        self._data = value


class ShipmentListModel(AbstractDataFrameModel):
    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return

        if role == Qt.DisplayRole:
            return str(self._data.iloc[index.row(), index.column()])
        if role == Qt.TextAlignmentRole:        # for first column in list set left text alignment
            return Qt.AlignVCenter if index.column() == 0 else Qt.AlignCenter
        # if role == Qt.FontRole:
        #     return QFont('Courier New')

    # def import_from(self, df: pd.DataFrame):
    #     # if target columns was not found --> exit
    #     if any([col not in df.columns for col in self._data.columns]):
    #         return 'ERROR! Cannot find one or more required columns in selected file!'
    #     self._data = df


class ShipmentMapModel(AbstractDataFrameModel):
    """ Model for shipment map, based on shipment list (ShipmentListModel) """
    # def __init__(self, df: pd.DataFrame = None, **kwargs):
        # parse box options
        # self.box_options = BoxOptions(*[v if k not in kwargs.keys() else kwargs.get(k)
        #                                 for k, v in default_box_options.items()])
        # # get columns options
        # self.code_column = kwargs.pop('code_column', default_code_column)
        # self.columns = kwargs.pop('columns', list(ascii_lowercase[:self.box_options.columns]))
        #
        # # TODO: сохранять данные списком или брать их из соседней модели?
        # if df is None:
        #     df = pd.DataFrame(columns=self.columns)
        # super(ShipmentMapModel, self).__init__(df)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return

        if role == Qt.DisplayRole:
            return str(self._data.iloc[index.row(), index.column()])        # TODO: + weight if notna
        if role == Qt.TextAlignmentRole:
            return Qt.AlignCenter
        # if (self.model_type == 'map') and (role == Qt.TextWordWrap):
        #     return True
        # if role == Qt.FontRole:
        #     return QFont('Courier New')

    # def import_from(self, df: pd.DataFrame):
    #     samples = df[self.code_column]
    #     array, indexes = [], []
    #     for index in range(0, samples.size, self.box_options.columns):
    #         row = (index // self.box_options.columns) % self.box_options.rows + 1
    #         array.append(samples.values[index:index + self.box_options.columns])
    #         indexes.append(row)
    #         # add separators
    #         if row == self.box_options.rows:
    #             array.extend([[''] * self.box_options.columns] * self.box_options.separator)
    #             indexes.extend([''] * self.box_options.separator)
    #     self._data = pd.DataFrame(array, index=indexes, columns=self.columns).fillna('')
