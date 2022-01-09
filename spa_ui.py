import settings
import pathlib
import re
import sys
import pandas as pd
from functools import partial

from PyQt5 import QtWidgets, uic, QtCore, QtGui
from PyQt5.Qt import Qt
from PyQt5.QtWidgets import QFileDialog, QHeaderView

from additional import ItemSelection, validate_selection
from shipment_list import ShipmentListView
from shipment_model import ShipmentModel
from recognizer import Recognizer


class ShipmentPackingAssistantUI(QtWidgets.QMainWindow):
    def __init__(self):
        super(ShipmentPackingAssistantUI, self).__init__()
        uic.loadUi(pathlib.Path().joinpath('ui', 'spa2.ui'), self)
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
        self.alarm_label = self.findChild(QtWidgets.QLabel, 'alarm_label')
        self.insert_button = self.findChild(QtWidgets.QPushButton, 'insert_button')
        self.remove_button = self.findChild(QtWidgets.QPushButton, 'remove_button')

        # create insert popup
        self.insert_popup = QtWidgets.QMenu(self)
        one_item_insert = QtWidgets.QAction('1 item', self)
        one_item_insert.triggered.connect(self.insert_action)
        multi_insert = QtWidgets.QAction(f'{settings.default_box_options.get("columns")} items', self)
        multi_insert.triggered.connect(partial(self.insert_action, Qt.AltModifier))

        self.insert_popup.addAction(one_item_insert)
        self.insert_popup.addAction(multi_insert)
        # initialize models for tables
        self.shipment = ShipmentModel()
        self.list_view.setModel(self.shipment.list_model)
        self.map_view.setModel(self.shipment.map_model)

        # bind actions
        self.shipment_number.textChanged.connect(self.set_shipment_number)
        self.insert_button.clicked.connect(self.show_insert_popup)
        self.remove_button.clicked.connect(self.remove_action)
        self.import_button.clicked.connect(self.import_shipment)
        self.export_button.clicked.connect(self.export_map)
        self.work_button.clicked.connect(self.work_action)

        # bind events
        self.list_view.selectionModel().selectionChanged.connect(self.back_selection)
        self.map_view.selectionModel().selectionChanged.connect(self.back_selection)
        self.list_view.selectionModel().selectionChanged.connect(self.update_ui_labels)
        # self.list_view.setItemDelegate(ShipmentListDelegate())

        # setup components look - this takes too much resources
        # NOTE: IT MAY BE THE REASON OF UI LAGS
        self.list_view.verticalHeader().setDefaultSectionSize(20)
        self.list_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.list_view.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.map_view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.map_view.setFont(self.font)

        self.rec_thread = Recognizer(self.apply_rec_result)
        self.rec_thread.start()
        self.list_view.switch_selection.connect(self.select)

        # show form
        self.show()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.rec_thread.stop()
        self.rec_thread.join()

    def show_insert_popup(self):
        """ Show popup menu """
        point = self.insert_button.cursor().pos()
        self.insert_popup.exec_(point)

    def set_shipment_number(self, value):
        """ Set shipment number """
        self.shipment.number = value

    def update_ui_labels(self):
        """ Update labels on frame """
        self.boxes_amount.setText(self.shipment.box_amount)
        if info := self.list_view.get_selected_sample_info():
            self.current_sample.setText(info.code)
            self.pos_from.setText(info.position)
            self.pos_to.setText(info.end_position)
            self.alarm_label.setVisible(bool(info.alarm))

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
                                          filter='Excel files (*.xls *.xlsx);;')
        list_file.setFileMode(QFileDialog.ExistingFile)
        if not list_file.exec():
            self.status_bar.showMessage(f'File was not opened.')
            return
        filepath = list_file.selectedFiles()[0]
        self.status_bar.showMessage(f'Opening file "{filepath}"')
        file_df = pd.read_excel(filepath)
        self.shipment.load(file_df)
        # get shipment number from path
        num = re.search(r'\d+', pathlib.Path(filepath).name)
        self.shipment_number.setText(num.group(0) if num else '')
        self.list_view.selectRow(0)

    def export_map(self):
        """ Save shipment map to Excel file """
        if self.shipment.list_model.rowCount() == 0:
            self.status_bar.showMessage(f'No data to export!')
            return

        if not self.shipment.number:
            self.status_bar.showMessage(f'Specify the shipment number!')
            self.shipment_number.setFocus()
            return

        modifiers = QtWidgets.QApplication.keyboardModifiers()
        if (int(modifiers) & Qt.ShiftModifier) == Qt.ShiftModifier:
            dialog = QtWidgets.QFileDialog(caption='Export shipment map',
                                           filter='Excel files (*.xlsx);;')
            dialog.setFileMode(QFileDialog.AnyFile)
            dialog.setAcceptMode(QFileDialog.AcceptSave)
            if not dialog.exec():
                self.status_bar.showMessage(f'File was not selected.')
                return
            filepath = dialog.selectedFiles()[0]
            if filepath.endswith('.xls'):
                filepath += 'x'
            elif not filepath.endswith('.xlsx'):
                filepath += '.xlsx'
        else:
            filepath = settings.save_path.joinpath(f'Map {self.shipment.number}.xlsx')
        try:
            self.shipment.save(filepath)
        except IOError as e:
            self.status_bar.showMessage(e)
            return
        self.status_bar.showMessage(f'File saved "{filepath}"')

    def insert_action(self, add_modifiers=None):
        """ Insert free row into shipment list """
        modifiers = int(QtWidgets.QApplication.keyboardModifiers()) | add_modifiers
        self.list_view.insert_free_row(modifiers=modifiers)

    def remove_action(self):
        """ Remove selected row from shipment list """
        self.list_view.remove_row()

    def work_action(self):
        """ Start/stop recognizer thread"""
        if self.shipment.list_model.rowCount() == 0:
            self.status_bar.showMessage(f'No data for processing!')
            return
        self.rec_thread.switch_pause()

        if self.rec_thread.suspended:
            self.status_bar.showMessage(f'Recognizer suspended!')
            self.work_button.setText('start')
            self.work_button.setIcon(QtGui.QIcon(pathlib.Path().joinpath('resources', 'start.svg').as_posix()))
        else:
            self.status_bar.showMessage(f'Recognizer started!')
            self.work_button.setText('pause')
            self.work_button.setIcon(QtGui.QIcon(pathlib.Path().joinpath('resources', 'pause.svg').as_posix()))

    def apply_rec_result(self, data, command: bool):
        """ Post-Process the recognized value or run voice command """
        if command:
            if data == -1:
                self.rec_thread.switch_pause()
                self.status_bar.showMessage(f'Recognizer suspended!')
                self.work_button.setText('start')
                self.work_button.setIcon(QtGui.QIcon(pathlib.Path().joinpath('resources', 'start.svg').as_posix()))
            else:
                self.list_view.switch_selection.emit(data)
        else:
            self.shipment.set_weight(self.list_view.selectedIndexes()[0].row(), data)
            self.list_view.switch_selection.emit(ItemSelection.NEXT)

    @validate_selection('list_view')
    def debug_action(self, *args, selected=None, **kwargs):
        # откуда тут в args берется False?
        pass


# start GUI
if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = ShipmentPackingAssistantUI()
    app.exec_()
