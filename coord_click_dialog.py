# coord_click_dialog.py
#Fichier intermédiaire entre le fichier ui convertit (coord_click_dialog_base.py) et gestion forestiere.py

from PyQt5.QtWidgets import QDialog
from .coord_click_dialog_base import Ui_CoordClickDialogBase

class CoordClickDialog(QDialog, Ui_CoordClickDialogBase):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
