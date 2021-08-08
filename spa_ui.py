import datetime
import pathlib
import re
import sys

import pandas as pd

from PyQt5 import QtWidgets, uic, QtCore, QtGui
from PyQt5.Qt import Qt
from PyQt5.QtWidgets import QFileDialog, QHeaderView

from additional import ItemSelection, validate_selection, Direction
from shipment_list import ShipmentListView
from shipment_model import ShipmentModel


class ShipmentPackingAssistantUI(QtWidgets.QMainWindow):
    def __init__(self):
        super(ShipmentPackingAssistantUI, self).__init__()
        uic.loadUi('ui/spa2.ui', self)
        # general settings
        self.font = QtGui.QFont('Courier New')
        self.recursion_depth = 0

        # initialize components
        self.status_bar = self.findChild(QtWidgets.QStatusBar, 'status_bar')
        self.boxes_amount = self.findChild(QtWidgets.QLabel, 'boxes_amount')
        self.map_view = self.findChild(QtWidgets.QTableView, 'map_view')
        self.list_view = self.findChild(ShipmentListView, 'list_view')
        self.shipment_number = self.findChild(QtWidgets.QLineEdit, 'shipment_number')
        self.import_button = self.findChild(QtWidgets.QPushButton, 'import_button')
        self.export_button = self.findChild(QtWidgets.QPushButton, 'export_button')
        self.work_button = self.findChild(QtWidgets.QPushButton, 'work_button')
        self.current_sample = self.findChild(QtWidgets.QLabel, 'current_sample')
        self.pos_from = self.findChild(QtWidgets.QLabel, 'pos_from')
        self.pos_to = self.findChild(QtWidgets.QLabel, 'pos_to')
        self.insert_button = self.findChild(QtWidgets.QPushButton, 'insert_button')
        self.remove_button = self.findChild(QtWidgets.QPushButton, 'remove_button')

        # initialize models for tables
        self.shipment = ShipmentModel()
        self.shipment.bind_ui_updater(self.update_ui)
        self.list_view.setModel(self.shipment.list_model)
        self.map_view.setModel(self.shipment.map_model)

        # bind actions
        self.insert_button.clicked.connect(self.insert_action)
        self.remove_button.clicked.connect(self.remove_action)
        self.import_button.clicked.connect(self.import_shipment)
        self.export_button.clicked.connect(self.export_map)
        self.work_button.clicked.connect(self.debug_action)

        self.list_view.selectionModel().selectionChanged.connect(self.back_selection)
        self.map_view.selectionModel().selectionChanged.connect(self.back_selection)
        self.list_view.selectionModel().selectionChanged.connect(self.update_ui)
        # self.list_view.setItemDelegate(ShipmentListDelegate())

        # setup components look - this takes too much resources
        # NOTE: THIS IS THE REASON OF UI LAGS
        self.list_view.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.list_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.list_view.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)

        self.map_view.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.map_view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.map_view.setFont(self.font)

        # show form
        self.show()

    def update_ui(self):
        """ Update labels on frame """
        code, start, end = info if (info := self.list_view.get_selected_sample_info()) else ('', '', '')
        self.boxes_amount.setText(self.shipment.box_amount)
        self.current_sample.setText(code)
        self.pos_from.setText(start)
        self.pos_to.setText(end)

    def back_selection(self, selection_range):
        """ Update selection on another view on caller-vew selection changed. """
        selected_length = len(selection_range.indexes())

        if selected_length == 1:        # back select in list
            # collect new selection and flags
            selected = selection_range.indexes()[0]
            new_selection = self.shipment.item_position(selected.row(), selected.column())
            flags = QtCore.QItemSelectionModel.ClearAndSelect | QtCore.QItemSelectionModel.Rows
            # set selection to list and scroll
            self.list_view.selectionModel().select(new_selection, flags)
            self.list_view.scrollTo(new_selection)

        elif selected_length >= self.shipment.list_model.weight_column_index:        # back select in map
            # collect new selection and flags
            selected = selection_range.indexes()[self.shipment.list_model.weight_column_index]
            new_selection = self.shipment.item_position(selected.row())
            flags = QtCore.QItemSelectionModel.ClearAndSelect
            # set selection to map and scroll
            self.map_view.selectionModel().select(new_selection, flags)
            self.map_view.scrollTo(new_selection)
            # correct list current index
            self.list_view.setCurrentIndex(selected)
            self.list_view.setFocus()

        else:           # selection out of range => clear select
            self.list_view.clearSelection()
            self.map_view.clearSelection()

    def select(self, direction: ItemSelection):
        """ Select next or previous item in list """
        if not (selected := self.list_view.selectedIndexes()):
            return
        selector = ItemSelection.selector()
        if (new_index := selector.get(direction)(selected[0].row())) > -1:
            self.list_view.selectRow(new_index)
        else:
            self.list_view.clearSelection()

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
        num = re.search(r'\d+', pathlib.Path(filepath).name)
        self.shipment_number.setText(num.group(0) if num else '')
        self.list_view.selectRow(0)

    def export_map(self):
        """ Save shipment map to Excel file """
        pass

    def insert_action(self):
        """ Insert free row into shipment list """
        modifiers = QtWidgets.QApplication.keyboardModifiers()
        self.list_view.insert_free_row(modifiers=modifiers)

    def remove_action(self):
        """ Remove selected row from shipment list """
        self.list_view.remove_row()

    @validate_selection('list_view')
    def debug_action(self, *args, selected=None, **kwargs):
        print(selected)
        pass
        # self.shipment.set_weight(self.list_view.selectedIndexes()[0].row(), '0.55')
        # self.select(ItemSelection.PREVIOUS)
        # cur_row = self.list_view.selectedIndexes()[0]
        # next_row = self.shipment.list_model.index(cur_row.row() - 1, cur_row.column())
        # self.shipment.move_row(cur_row, next_row)


# start GUI
if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = ShipmentPackingAssistantUI()
    app.exec_()
