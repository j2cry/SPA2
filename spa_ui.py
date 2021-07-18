import re
import sys
from functools import partial

import pandas as pd

from collections import namedtuple
from PyQt5 import QtWidgets, uic, QtCore
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QFileDialog, QHeaderView

from shipment_models import ShipmentModel

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
        self.import_button = self.findChild(QtWidgets.QPushButton, 'import_button')
        self.export_button = self.findChild(QtWidgets.QPushButton, 'export_button')
        self.work_button = self.findChild(QtWidgets.QPushButton, 'work_button')
        self.current_sample = self.findChild(QtWidgets.QLabel, 'current_sample')
        self.pos_from = self.findChild(QtWidgets.QPushButton, 'pos_from')
        self.pos_to = self.findChild(QtWidgets.QPushButton, 'pos_to')

        # initialize models for tables
        self.shipment = ShipmentModel()
        self.list_view.setModel(self.shipment.list_model)
        self.map_view.setModel(self.shipment.map_model)

        # bind actions
        self.import_button.clicked.connect(self.import_shipment)
        self.work_button.clicked.connect(self.debug_action)

        self.list_view.selectionModel().selectionChanged.connect(partial(self.back_selection, 'list'))
        self.map_view.selectionModel().selectionChanged.connect(partial(self.back_selection, 'map'))
        # self.list_view.clicked.connect(partial(self.back_selection, 'list'))
        # self.map_view.clicked.connect(partial(self.back_selection, 'map'))

        # setup components look - this takes too much resources
        self.list_view.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.list_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.list_view.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.map_view.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.map_view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.map_view.setFont(self.font)

        # show form
        self.show()

    def import_shipment(self):
        """ Create shipment model from Excel file """
        list_file = QtWidgets.QFileDialog(caption='Open shipment list',
                                          filter='Excel files (*.xls, *.xlsx);')
        list_file.setFileMode(QFileDialog.ExistingFile)
        if not list_file.exec():
            self.status_bar.showMessage(f'File was not opened.')
            return
        filepath = list_file.selectedFiles()[0]
        self.status_bar.showMessage(f'Opening file "{filepath}"')
        file_df = pd.read_excel(filepath)
        self.shipment.load(file_df)
        self.boxes_amount.setText(self.shipment.box_amount)
        # get shipment number from path
        num = re.search(r'\d+', filepath)
        self.shipment_number.setText(num.group(0) if num else '')

    def back_selection(self, caller):
        caller_map = {'list': self.list_view.selectedIndexes,
                      'map': self.map_view.selectedIndexes}
        if not (selected := caller_map.get(caller)()) or selected[0].data() == '':
            self.list_view.clearSelection()
            self.map_view.clearSelection()
            return
        selected = selected[0]
        self.status_bar.showMessage(f'{selected.data()}: {selected.row()} {selected.column()}')

        if caller == 'list':
            new_selection = self.shipment.item_position(selected.row())
            self.map_view.selectionModel().select(new_selection, QtCore.QItemSelectionModel.ClearAndSelect)
            self.map_view.scrollTo(new_selection)
        elif caller == 'map':
            new_selection = self.shipment.item_position(selected.row(), selected.column())
            self.list_view.selectRow(new_selection.row())

    def select(self, direction):
        """ Select next or previous item in list
            @direction = 'next' or 'prev' """
        pass

    def debug_action(self):
        self.shipment.set_weight(self.list_view.selectedIndexes()[0].row(), 0.55)
        # cond = (self.shipment.map_model.df.index != '')
        # self.shipment.map_model.df[cond] += ' 0.55'
        # self.shipment.map_model.layoutChanged.emit()


# start GUI
if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = ShipmentPackingAssistantUI()
    app.exec_()
