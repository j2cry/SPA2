import sys
import pandas as pd
import numpy as np

from collections import namedtuple
from PyQt5 import QtWidgets, uic
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

        # setup components
        # self.list_view.horizontalHeader().setContentsMargins(2, 2, 2, 2)
        self.list_view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # bind actions
        self.load_button.clicked.connect(self.load_list)
        self.work_button.clicked.connect(self.debug_action)

        # initialize models for tables
        self.list_df = pd.DataFrame(0, index=[], columns=list(self.list_columns))
        self.list_model = ShipmentModel(self.list_df)
        self.list_view.setModel(self.list_model)

        self.map_df = pd.DataFrame(0, index=[3, 4, 5], columns=self.map_columns)
        self.map_model = ShipmentModel(self.map_df)
        self.map_view.setModel(self.map_model)

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
        # get list of samples with its placements
        samples_df = file_df[list(self.list_columns)]

        # get amount of required rows for samples
        max_size = np.ceil(samples_df.shape[0] / self.box_columns) * self.box_columns

        # задача: собрать датафрейм из списка
        arr = pd.Series(samples_df[self.list_columns.code], index=np.arange(0, max_size)).values.reshape((-1, self.box_columns))


        self.map_df = pd.DataFrame(arr,
                                   index=np.arange(0, max_size),
                                   columns=self.map_columns)
        self.map_model.layoutChanged.emit()

    def debug_action(self):
        self.map_df += 1
        self.map_model.layoutChanged.emit()


# start GUI
if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = ShipmentPackingAssistantUI()
    app.exec_()
