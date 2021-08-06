from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import Qt


class ShipmentListView(QtWidgets.QTableView):
    def keyPressEvent(self, e: QtGui.QKeyEvent) -> None:
        # implement something here
        super(ShipmentListView, self).keyPressEvent(e)
