# create_polygon_dialog_wrapper.py

from PyQt5.QtWidgets import QDialog
from .create_polygon_dialog import Ui_createPolygonDialog

class CreatePolygonDialog(QDialog, Ui_createPolygonDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
