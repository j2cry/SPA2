import enum
import typing
from functools import wraps

import pandas as pd
from collections import defaultdict, namedtuple
from PyQt5 import QtCore
from PyQt5.Qt import Qt

BoxOptions = namedtuple('BoxOptions', 'rows columns separator')
SampleInfo = namedtuple('SampleInfo', 'code position end_position alarm')


# -------------------- Generators --------------------
def range_generator(start: int, stop: int, step: int = 1, endpoint=False):
    """ Range generator. Keeps the direction """
    if start < stop:
        if step < 0:
            step = -step
        result = start
        while (result <= stop) if endpoint else (result < stop):
            yield result
            result += step
    elif start > stop:
        if step > 0:
            step = -step
        result = start
        while (result >= stop) if endpoint else (result > stop):
            yield result
            result += step


# -------------------- Enumerations --------------------
class ItemSelection(enum.Enum):
    # selection constants
    CLEAR = 0
    PREVIOUS = 1
    NEXT = 2

    @staticmethod
    def selector():
        switcher = defaultdict(lambda pos: lambda: -1,
                               {ItemSelection.CLEAR: lambda pos: -1,
                                ItemSelection.PREVIOUS: lambda pos: pos - 1,
                                ItemSelection.NEXT: lambda pos: pos + 1})
        return switcher


class Direction(tuple):
    BACKWARD = (0, 1)
    FORWARD = (1, 0)


class PositionStatus(int):
    SEPARATOR = 0
    UNPACKED_SAMPLE = 1
    PACKED_SAMPLE = 2
    FREE = 3


# -------------------- QAbstractTableModel --------------------
class AbstractDataFrameModel(QtCore.QAbstractTableModel):
    """ Parent abstract DataFrame-based model class for QTableView (map and list) """
    def __init__(self, df: pd.DataFrame):
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
            self.dataChanged.emit(index, index, [role])
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
        first_index = self.index(0, 0)
        last_index = self.index(self._df.shape[0] - 1, self._df.shape[1] - 1)
        self.dataChanged.emit(first_index, last_index, [Qt.DisplayRole])


# -------------------- Decorators --------------------
def validate_selection(path: str = ''):
    """ Check if item is selected else return None. Decorated function must receive kwargs or `selected` keyword.
        :param path
            Path from self to selectedIndexes excluding self. and .selectIndexes points. Use `.` as separator """
    def validator(method):
        @wraps(method)
        def wrapper(self, *args, **kwargs):
            obj = self          # find selectIndexes
            for attr_name in f'{path}.selectedIndexes'.split('.'):
                if not attr_name:
                    continue
                obj = getattr(obj, attr_name, None)
                if not obj:
                    raise ValueError(f'Cannot find attribute `{attr_name}` at `{obj}` in decorator!')
            selected = selected[0] if (selected := obj()) else None
            return method(self, *args, selected=selected, **kwargs) if selected else None
        return wrapper
    return validator
