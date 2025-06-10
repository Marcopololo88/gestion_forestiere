# Fichier de configuration du plugin

from qgis.PyQt.QtWidgets import QDialog, QMessageBox, QProgressDialog, QApplication
from ui_config_dialog import Ui_ConfigDialog
from qgis.core import QgsProject, QgsVectorLayer, QgsField
from PyQt5.QtCore import QVariant, Qt, QCoreApplication
import os

CHAMPS_A_CREER = [
            ("section", "String"),
            ("numero", "String"),
            ("indice_parc", "String"),
            ("contenance", "Integer64"),
            ("arpente", "Integer"),
            ("created", "Date"),
            ("updated", "Date"),
            ("SURFACE", "Real"),
            ("Possession", "Boolean"),
            ("Nous", "String"),
            ("Terrain", "String"),
            ("Acces","String"),
            ("RemTerrain","String"),
            ("nom_Voisin", "String"),
            ("adresse_Voisin", "String"),
            ("tel_Voisin", "String"),
            ("mail_Voisin", "String"),
            ("plant1", "String"),
            ("plant2", "String"),
            ("plant3", "String"),
            ("plant4", "String"),
            ("annee", "Integer"),
            ("totalplants", "Integer"),
            ("Tx1", "Integer"),
            ("Tx2", "Integer"),
            ("Tx3", "Integer"),
            ("Tx4", "Integer"),
            ("Tvx1", "String"),
            ("Tvx2", "String"),
            ("Tvx3", "String"),
            ("Tvx4", "String"),
            ("Tvx5", "String"),
            ("Tvx6", "String"),
            ("Trait1", "String"),
            ("Trait2", "String"),
            ("Trait3", "String"),
            ("Trait4", "String"),
            ("Trait5", "String"),
            ("Trait6", "String"),
            ("dateTvx1", "Date"),
            ("dateTvx2", "Date"),
            ("dateTvx3", "Date"),
            ("dateTvx4", "Date"),
            ("dateTvx5", "Date"),
            ("dateTvx6", "Date"),
            ("remTvx1", "String"),
            ("remTvx2", "String"),
            ("remTvx3", "String"),
            ("remTvx4", "String"),
            ("remTvx5", "String"),
            ("remTvx6", "String"),
            ("dateTrait1", "Date"),
            ("dateTrait2", "Date"),
            ("dateTrait3", "Date"),
            ("dateTrait4", "Date"),
            ("dateTrait5", "Date"),
            ("dateTrait6", "Date"),
            ("remTrait1", "String"),
            ("remTrait2", "String"),
            ("remTrait3", "String"),
            ("remTrait4", "String"),
            ("remTrait5", "String"),
            ("remTrait6", "String"),
            ("Prev1", "String"),
            ("Prev2", "String"),
            ("Prev3", "String"),
            ("Prev4", "String"),
            ("datePrev1", "String"),
            ("datePrev2", "String"),
            ("datePrev3", "String"),
            ("datePrev4", "String"),
            ("remPrev1", "String"),
            ("remPrev2", "String"),
            ("remPrev3", "String"),
            ("remPrev4", "String"),
            ("typeParc", "Integer")
        ]

TYPE_MAPPING = {
    "String": QVariant.String,
    "Integer": QVariant.Int,
    "Integer64": QVariant.LongLong,
    "Real": QVariant.Double,
    "Boolean": QVariant.Bool,
    "Date": QVariant.Date,
}


class ConfigDialog(QDialog):

    def __init__(self, parent=None, iface=None):
        # Assurez-vous que le parent est un QWidget (iface.mainWindow() est un QWidget)
        super().__init__(parent)  # parent est maintenant un QWidget
        self.ui = Ui_ConfigDialog()
        self.ui.setupUi(self)

        # Sauvegarder l'instance de iface
        self.iface = iface  # On assigne iface à l'attribut self.iface
        print(">>> iface :", self.iface)  # Ajoute cette ligne pour vérifier si iface est correctement transmis

        # Connecter les événements des cases à cocher
        self.ui.checkBoxChamps.stateChanged.connect(self.update_confirm_button_state)
        self.ui.checkBoxSymbio.stateChanged.connect(self.update_confirm_button_state)
        self.ui.btnConfirm.clicked.connect(self.confirm_actions)

        # Initialiser layer_signal_connected à False avant toute utilisation
        self.layer_signal_connected = False

        # Mettre à jour immédiatement la ligne de couche
        self.update_line_layer()

        # Connexion de l'événement au changement de couche
        self.iface.currentLayerChanged.connect(self.update_line_layer)

        # Initialiser l'état du bouton à l'ouverture du dialog
        self.update_confirm_button_state()

        # Afficher les champs à créer dans le TextEdit
        self.afficher_champs()

    def closeEvent(self, event):
        # Déconnecter proprement le signal quand la fenêtre se ferme
        if self.iface:
            try:
                self.iface.currentLayerChanged.disconnect(self.update_line_layer)
            except TypeError:
                pass
        super().closeEvent(event)

    def update_line_layer(self):
        """Met à jour le champ lineLayer avec le nom de la couche sélectionnée et vérifie le format"""

        # Vérifier si une couche active existe
        layer = self.iface.activeLayer()
        if layer is None or not isinstance(layer, QgsVectorLayer):
            self.ui.lineLayer.clear()
            return
        # Affiche le nom de la couche active dans le champ lineLayer
        self.ui.lineLayer.setText(layer.name())

    def update_confirm_button_state(self):
        # Active ou désactive le bouton confirmer selon l'état des checkboxes et de la couche sélectionnée
        champs_ok = self.ui.checkBoxChamps.isChecked()
        symbio_ok = self.ui.checkBoxSymbio.isChecked()
        layer_text = self.ui.lineLayer.text()

        layer = self.iface.activeLayer()

        is_gpkg = False
        if isinstance(layer, QgsVectorLayer):
            path = layer.source().split("|")[0]  # Supprimer les métadonnées après le |
            _, ext = os.path.splitext(path)
            is_gpkg = ext.lower() == ".gpkg"

        if champs_ok and symbio_ok and layer_text and is_gpkg:
            self.ui.btnConfirm.setEnabled(True)
        else:
            self.ui.btnConfirm.setEnabled(False)

    def champs_requis_absents(self, layer):
        """Renvoie True s'il manque des champs requis dans la couche"""
        if not layer:
            return True
        noms_existants = {f.name().lower() for f in layer.fields()}
        champs_requis = {"id", "section", "numero", "contenance"}
        return not champs_requis.issubset(noms_existants)

    def confirm_actions(self):
        # Vérifier si les deux cases à cocher sont activées
        if not self.ui.checkBoxChamps.isChecked() and not self.ui.checkBoxSymbio.isChecked():
            QMessageBox.warning(self, "Avertissement", "Veuillez cocher au moins une option.")
            return

        # Vérifier si une couche est sélectionnée
        layer = self.get_selected_layer()
        if not layer:
            QMessageBox.warning(self, "Erreur", "Aucune couche vectorielle sélectionnée.")
            return

        # Vérifier si la couche sélectionnée est affichée dans le champ lineLayer
        if not self.ui.lineLayer.text():
            QMessageBox.warning(self, "Erreur", "Veuillez sélectionner une couche et la renseigner dans le champ.")
            return

        # Afficher un warning uniquement si des champs requis sont absents
        if self.ui.checkBoxChamps.isChecked() and self.champs_requis_absents(layer):
            QMessageBox.warning(
                self,
                "Attention",
                "⚠️ Un des champs 'id', 'section', 'numero' et 'contenance' n'existe pas dans la couche.",
                QMessageBox.Ok
            )

        # Demander confirmation avant de continuer
        reply = QMessageBox.question(
            self,
            "Confirmation",
            "Voulez-vous vraiment continuer ?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            # Si les cases à cocher sont activées, effectuer les actions correspondantes
            if self.ui.checkBoxChamps.isChecked():
                self.create_fields_table(layer)

            if self.ui.checkBoxSymbio.isChecked():
                self.create_style_layer(layer)

            # Fermer la boîte de dialogue après confirmation et traitement
            self.accept()

    def get_selected_layer(self):
        # Renvoie la couche vectorielle active, ou None sinon
        layer = self.iface.activeLayer()
        if isinstance(layer, QgsVectorLayer):
            return layer
        return None

    def create_fields_table(self, layer):
        # Création des champs manquants dans la table attributaire de la couche
        if not layer:
            QMessageBox.warning(self, "Avertissement", "Aucune couche sélectionnée.")
            return

        # Met à jour le champ lineLayer avec le nom de la couche
        self.ui.lineLayer.setText(layer.name())

        noms_existants = {f.name() for f in layer.fields()}
        try:
            # Prépare la liste des nouveaux champs à ajouter
            champs_manquants = [
                QgsField(nom, TYPE_MAPPING[typ])
                for nom, typ in CHAMPS_A_CREER
                if nom not in noms_existants
            ]
        except KeyError as e:
            QMessageBox.critical(self, "Erreur", f"Type de champ non reconnu : {e}")
            return

        if not champs_manquants:
            QMessageBox.information(self, "Information", "Tous les champs sont déjà présents.")
            return

        # Affiche une boîte de progression pendant la création des champs
        progress = QProgressDialog("Création des champs en cours...", "", 0, 0, self)
        progress.setWindowTitle("Traitement en cours")
        progress.setWindowModality(Qt.WindowModal)
        progress.show()
        QApplication.processEvents()  # Forcer l'affichage immédiat

        # Démarre la modification de la couche
        layer.startEditing()
        success = layer.dataProvider().addAttributes(champs_manquants)
        if success:
            layer.updateFields()

            # Copier les valeurs du champ 'contenance' vers le champ 'SURFACE'
            if "contenance" in noms_existants and "SURFACE" in {f.name() for f in layer.fields()}:
                idx_contenance = layer.fields().indexFromName("contenance")
                idx_surface = layer.fields().indexFromName("SURFACE")

                for feat in layer.getFeatures():
                    val_contenance = feat[idx_contenance]
                    if val_contenance is not None and val_contenance != '':
                        try:
                            val_contenance_float = float(val_contenance)
                            val_surface = val_contenance_float / 100.0
                            layer.changeAttributeValue(feat.id(), idx_surface, val_surface)
                        except Exception as e:
                            print(f"Erreur conversion contenance: {e}")

            layer.commitChanges()
            QMessageBox.information(self, "Succès", "Champs créés avec succès.")
        else:
            layer.rollBack()
            QMessageBox.warning(self, "Erreur", "Échec lors de la création des champs.")

        progress.close()

    def create_style_layer(self, layer):
        qml_path = os.path.join(os.path.dirname(__file__), "styleplugin.qml")
        if os.path.exists(qml_path):
            layer.loadNamedStyle(qml_path)
            layer.triggerRepaint()
            QMessageBox.information(self, "Style appliqué", "Le style a été appliqué.")
        else:
            QMessageBox.warning(self, "Erreur", f"Le fichier de style n'a pas été trouvé : {qml_path}")

    def afficher_champs(self):
        # Affiche la liste des champs dans le QTextEdit avec formatage
        texte = ""
        for nom, typ in CHAMPS_A_CREER:
            texte += f"- {nom} : {typ}\n"
        self.ui.textEditChamps.setPlainText(texte)
