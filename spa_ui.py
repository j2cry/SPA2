import sys
import pandas as pd
import numpy as np

from collections import namedtuple
from PyQt5 import QtWidgets, uic
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QFileDialog, QHeaderView
from string import ascii_lowercase

from shipment_models import ShipmentModel

ShipmentListColumns = namedtuple('ShipmentListColumns', 'code st0 st1 st2 st3 st4')


class ShipmentPackingAssistantUI(QtWidgets.QMainWindow):
    def __init__(self):
        super(ShipmentPackingAssistantUI, self).__init__()
        uic.loadUi('ui/spa2.ui', self)
        # general settings
        self.box_columns = 9
        self.box_rows = 9
        self.separator = 2
        self.list_columns = ShipmentListColumns('Код', 'st0', 'st1', 'st2', 'st3', 'st4')
        self.map_columns = [''] + list(ascii_lowercase[:self.box_columns])
        self.font = QFont('Courier New')

        # initialize components
        self.status_bar = self.findChild(QtWidgets.QStatusBar, 'status_bar')
        self.boxes_amount = self.findChild(QtWidgets.QLabel, 'boxes_amount')
        self.map_view = self.findChild(QtWidgets.QTableView, 'map_view')
        self.list_view = self.findChild(QtWidgets.QTableView, 'list_view')
        self.shipment_number = self.findChild(QtWidgets.QLineEdit, 'shipment_number')
        self.load_button = self.findChild(QtWidgets.QPushButton, 'load_button')
        self.save_button = self.findChild(QtWidgets.QPushButton, 'save_button')
        self.work_button = self.findChild(QtWidgets.QPushButton, 'work_button')
        self.current_sample = self.findChild(QtWidgets.QLabel, 'current_sample')
        self.pos_from = self.findChild(QtWidgets.QPushButton, 'pos_from')
        self.pos_to = self.findChild(QtWidgets.QPushButton, 'pos_to')

        # bind actions
        self.load_button.clicked.connect(self.load_list)
        self.work_button.clicked.connect(self.debug_action)

        # initialize models for tables
        # samples_df = pd.DataFrame('0000000T0(00)', index=[3, 4, 5], columns=list(self.list_columns))
        samples_df = pd.DataFrame(index=[], columns=list(self.list_columns))
        self.list_model = ShipmentModel(samples_df, 'list')
        self.list_view.setModel(self.list_model)

        # self.map_df = pd.DataFrame('0000000T0(00) 0.55', index=[3, 4, 5], columns=self.map_columns)
        map_df = pd.DataFrame(index=[], columns=self.map_columns)
        self.map_model = ShipmentModel(map_df, 'map')
        self.map_view.setModel(self.map_model)

        # setup components look
        self.list_view.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.list_view.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.list_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.list_view.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        # self.list_view.horizontalHeader().setOffset(2)
        # self.list_view.setContentsMargins(2, 2, 2, 2)
        self.list_view.horizontalHeader().setMinimumSectionSize(24)

        self.map_view.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.map_view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.map_view.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.map_view.horizontalHeader().setMinimumSectionSize(32)
        self.map_view.setFont(self.font)
        self.map_view.setWordWrap(True)

        # show form
        self.show()

    def load_list(self):
        list_file = QtWidgets.QFileDialog(caption='Open shipment list',
                                          filter='Excel files (*.xls, *.xlsx);')
        list_file.setFileMode(QFileDialog.ExistingFile)
        if not list_file.exec():
            self.status_bar.showMessage(f'File was not opened.')
            return
        self.status_bar.showMessage(f'Opening file "{list_file.selectedFiles()[0]}"')
        file_df = pd.read_excel(list_file.selectedFiles()[0])
        # if target columns was not found --> exit
        if any([col not in file_df.columns for col in self.list_columns]):
            self.status_bar.showMessage(f'ERROR! Cannot find column(s) "{self.list_columns}" in selected file!')
            return
        # get list of samples with its placements and put it to view
        samples_df = file_df[list(self.list_columns)]
        self.list_model = ShipmentModel(samples_df, 'list')
        self.list_view.setModel(self.list_model)

        # get amount of required rows in map for samples
        max_rows = int(np.ceil(samples_df.shape[0] / self.box_columns))

        # convert list to map
        samples = file_df[self.list_columns.code]
        arr = [['', *samples.values[i:i + self.box_columns]] for i in range(0, samples.size, self.box_columns)]
        map_df = pd.DataFrame(arr, index=np.arange(0, max_rows), columns=self.map_columns)
        # generate first map column
        map_df.iloc[:, 0] = [n % self.box_columns for n in range(1, max_rows + 1)]
        # insert separators
        # TODO: insert separators

        self.map_model = ShipmentModel(map_df.fillna(''), 'map')
        self.map_view.setModel(self.map_model)

    def debug_action(self):
        self.map_model.df.iloc[:, 1:] += ' 0.55'
        self.map_model.layoutChanged.emit()


# start GUI
if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = ShipmentPackingAssistantUI()
    app.exec_()
