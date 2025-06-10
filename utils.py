# utils.py

from qgis.PyQt.QtWidgets import QComboBox

from qgis.core import (
    Qgis,
    QgsMessageLog,
    QgsProject,
    QgsLinePatternFillSymbolLayer,
    QgsRenderContext,
    QgsRectangle,
    QgsSymbol,
    QgsFillSymbol,
    QgsSymbolLayer,
    QgsVectorLayer,
)

from PyQt5.QtCore import QVariant, QDate

from PyQt5.QtWidgets import QTableWidgetItem, QTableWidget, QMessageBox

from PyQt5.QtGui import QColor

from qgis.utils import iface

import csv
import os

#-------------Fonctions utilitaires

# Fonction gèrant la sélection de la coucha active ainsi que le controle d'existance des champs
def get_valid_active_layer(dlg):
    """
    Retourne la couche vectorielle active si elle est valide et contient les champs requis.
    Affiche un message d'erreur sinon.
    """
    layer = iface.activeLayer()
    if not layer or not isinstance(layer, QgsVectorLayer):
        QMessageBox.warning(dlg, "Erreur", "Aucune couche vectorielle active.")
        return None

    expected_fields = {"id", "section","numero", "SURFACE", "typeParc", "totalplants"}
    layer_fields = set(field.name() for field in layer.fields())

    if not expected_fields.issubset(layer_fields):
        QMessageBox.critical(
            dlg,
            "Erreur",
            "La couche active ne contient pas tous les champs \n nécessaires à l'utilisation du plugin"
        )
        return None

    return layer

def get_valid_active_layer_start(dlg):
    """
    Retourne la couche vectorielle active si elle est valide et contient les champs requis.
    Affiche un message d'erreur sinon.
    """
    layer = iface.activeLayer()
    if not layer or not isinstance(layer, QgsVectorLayer):
        QMessageBox.warning(dlg, "Erreur", "Aucune couche vectorielle active.")
        return None

    expected_fields = {"id", "section","numero", "SURFACE", "typeParc", "totalplants"}
    layer_fields = set(field.name() for field in layer.fields())

    if not expected_fields.issubset(layer_fields):
        QMessageBox.critical(
            dlg,
            "Erreur",
            "La couche sélectionnée n'est pas compatible avec le plugin. \n "
            "Sélectionnez une couche valide \n"
            "et relancez le plugin"
        )
        return None

    return layer

# Evite d'afficher les valeurs nulles
def safe_set_text(line_edit, value):
    if value is None or str(value).upper() in ("NULL", "NONE"):
        line_edit.setText("")
    else:
        line_edit.setText(str(value))

def safe_set_date(date_edit, value):
    if date_edit is None:
        return
    if value in (None, "", "NULL"):
        # Mettre un texte vide à l'affichage
        date_edit.clear()
    else:
        if isinstance(value, QDate):
            date_edit.setDate(value)
        else:
            try:
                y, m, d = map(int, str(value).split("-"))
                date_edit.setDate(QDate(y, m, d))
            except Exception as e:
                print(f"❌ Impossible de parser la date: {value} ({e})")
                date_edit.clear()



# Sauvegarde de la table des données

def save_table_to_csv(table_widget: QTableWidget, csv_path: str):
    try:
        with open(csv_path, "w", newline='', encoding='utf-8') as file:
            writer = csv.writer(file)

            for row in range(table_widget.rowCount()):
                row_data = []
                for col in range(table_widget.columnCount()):
                    item = table_widget.item(row, col)
                    row_data.append(item.text() if item else "")
                writer.writerow(row_data)

        print(f"✅ Données sauvegardées dans : {csv_path}")

    except Exception as e:
        print(f"❌ Erreur lors de la sauvegarde : {e}")

# Chargement de la table des données

def load_table_from_csv(table_widget, file_path):
    """Charge les données d’un fichier CSV dans le QTableWidget (ajoute des lignes si besoin)."""
    if not os.path.exists(file_path):
        return  # Pas de fichier → rien à charger

    with open(file_path, mode='r', newline='', encoding='utf-8') as file:
        reader = csv.reader(file)
        for row_index, row_data in enumerate(reader):
            if row_index >= table_widget.rowCount():
                table_widget.insertRow(table_widget.rowCount())  # Ajoute une ligne si nécessaire
            for col_index, value in enumerate(row_data):
                if col_index < table_widget.columnCount():
                    item = QTableWidgetItem(value)
                    table_widget.setItem(row_index, col_index, item)


#def refresh_combos_from_table(self):
#    """Met à jour les comboboxs en fonction des données de la table."""

    # Extraire les données de la table (par exemple, colonne 0 et 1)
#    data = extract_table_values(self.dlg.tableWidgetData, [0, 1])  # Liste des colonnes d'intérêt

    # Extraire les valeurs uniques pour chaque colonne
 #   unique_data = unique_values_per_column(data)

    # Par exemple, mettre à jour un combobox avec les valeurs uniques de la première colonne
#    if unique_data and unique_data[0]:
#        self.dlg.comboBox.clear()  # Vider le combobox avant d'ajouter les nouvelles valeurs
#        self.dlg.comboBox.addItems(unique_data[0])  # Ajouter les valeurs uniques à la première colonne


def extract_table_values(table_widget, col_indices):
    """
    Extrait pour chaque ligne de table_widget les valeurs des colonnes
    listées dans col_indices, et renvoie une liste de listes.
    """
    data = []
    for row in range(table_widget.rowCount()):
        row_vals = []
        for col in col_indices:
            item = table_widget.item(row, col)
            row_vals.append(item.text() if item else "")
        data.append(row_vals)
    return data

def unique_values_per_column(data):
    """
    À partir d'une liste de lignes (listes de colonnes),
    renvoie pour chaque colonne une liste triée de valeurs uniques.
    """
    if not data:
        return []
    num_cols = len(data[0])
    uniques = [set() for _ in range(num_cols)]
    for row_vals in data:
        for idx, val in enumerate(row_vals):
            uniques[idx].add(val)
    return [sorted(col_set) for col_set in uniques]

def format_date(value):
    """
    Formate un objet QDate ou datetime.date en chaîne 'dd/MM/yyyy'.
    Retourne '???' si la valeur est vide ou invalide.
    """
    if hasattr(value, 'toString'):
        return value.toString("dd/MM/yyyy")  # QDate
    elif hasattr(value, 'strftime'):
        return value.strftime("%d/%m/%Y")    # datetime.date
    else:
        return "???"

def safe_str(value):
    """Convertit une valeur pour affichage dans Qt : vide si None/NULL."""
    if value is None or str(value).upper() in ("NULL", "NONE"):
        return ""
    return str(value)

def get_fill_color_from_layer(layer, field_value):
    """
    Retourne la couleur de remplissage principale pour un symbole dans une couche QGIS.
    """
    if not layer or not isinstance(layer, QgsVectorLayer):
        return None

    renderer = layer.renderer()
    if renderer and renderer.type() == "categorizedSymbol":
        for cat in renderer.categories():
            if str(cat.value()) == str(field_value):
                symbol = cat.symbol()
                # Essaie de récupérer la couleur du premier symbole de remplissage
                for i in range(symbol.symbolLayerCount()):
                    sym_layer = symbol.symbolLayer(i)
                    if hasattr(sym_layer, "fillColor"):
                        return sym_layer.fillColor().name()
                    elif hasattr(sym_layer, "color"):
                        return sym_layer.color().name()
                # Fallback
                return symbol.color().name()
    return None



# Différentes méthodes de Messages d'erreurs et d'avertissement

def log_debug(message, plugin_name="CoordClick"):
    """Log un message d'information."""
    QgsMessageLog.logMessage(message, plugin_name, Qgis.Info)

def log_warning(message, plugin_name="CoordClick"):
    """Log un message d'avertissement."""
    QgsMessageLog.logMessage(message, plugin_name, Qgis.Warning)

def log_error(message, plugin_name="CoordClick"):
    """Log un message d'erreur."""
    QgsMessageLog.logMessage(message, plugin_name, Qgis.Critical)

def show_success_bar(iface, title, message):
    """Affiche un message de succès dans la barre d'info."""
    iface.messageBar().pushSuccess(title, message)

def show_warning_bar(iface, title, message):
    """Affiche un message d'avertissement dans la barre d'info."""
    iface.messageBar().pushWarning(title, message)

def show_error_bar(iface, title, message):
    """Affiche un message d'erreur dans la barre d'info."""
    iface.messageBar().pushCritical(title, message)

