import sys
import pandas as pd
import numpy as np

from collections import namedtuple
from PyQt5 import QtWidgets, uic
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QFileDialog, QHeaderView

from shipment_models import ShipmentMapModel, ShipmentListModel, ShipmentModel

ShipmentListColumns = namedtuple('ShipmentListColumns', 'code st0 st1 st2 st3 st4')


class ShipmentPackingAssistantUI(QtWidgets.QMainWindow):
    def __init__(self):
        super(ShipmentPackingAssistantUI, self).__init__()
        uic.loadUi('ui/spa2.ui', self)
        # general settings
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
        self.shipment = ShipmentModel()
        self.list_view.setModel(self.shipment.list_model)
        self.map_view.setModel(self.shipment.map_model)
        # dbg_samples_df = pd.DataFrame('0000000T0(00)',
        #                               index=np.arange(0, 20),
        #                               columns=['Код', 'st0', 'st1', 'st2', 'st3', 'st4'])
        # self.list_model = ShipmentListModel()
        # self.list_view.setModel(self.list_model)

        # dbg_map_df = pd.DataFrame('0000000T0(00) 0.55', index=np.arange(0, 20), columns=list('abcdefghi'))
        # self.map_model = ShipmentMapModel()
        # self.map_view.setModel(self.map_model)

        # setup components look
        self.list_view.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.list_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.list_view.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)

        self.map_view.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.map_view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.map_view.setFont(self.font)

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

        self.shipment.load(file_df)
        # self.list_model.import_from(file_df)
        self.shipment.list_model.layoutChanged.emit()

        # self.map_model.import_from(file_df)
        self.shipment.map_model.layoutChanged.emit()

    def debug_action(self):
        cond = (self.map_model.df.index != '')
        self.map_model.df[cond] += ' 0.55'
        self.map_model.layoutChanged.emit()


# start GUI
if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = ShipmentPackingAssistantUI()
    app.exec_()
