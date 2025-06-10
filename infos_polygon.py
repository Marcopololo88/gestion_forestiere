from qgis.PyQt.QtWidgets import QDialog, QMessageBox
from .create_polygon_dialog import Ui_createPolygonDialog

from qgis.core import (
    QgsProject,
    QgsFeatureRequest,
    QgsGeometry,
    Qgis,
    QgsVectorLayer,
    QgsMessageLog,
    QgsWkbTypes,
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
)
from qgis.utils import iface


class InfosPolygonManager:
    def __init__(self, ui, dialog):
        self.ui = ui
        self.dialog = dialog  # Ce sera maintenant un CreatePolygonDialog
        self.layer = None

        # Connexions pour activer/désactiver le bouton en fonction des champs obligatoires
        self.ui.lineSection.textChanged.connect(self.update_validate_button_state)
        self.ui.lineNumero.textChanged.connect(self.update_validate_button_state)
        self.ui.lineIndice.textChanged.connect(self.update_validate_button_state)

        # Connexion du bouton de validation
        self.ui.btnValidatePol.clicked.connect(self.save_polygon_info)

        # Initialisation de l’état du bouton
        self.update_validate_button_state()

        # Initialisation des attributs liés aux champs de l'entité parente
        self.section = None
        self.numero = None
        self.commune = None
        self.prefixe = None
        self.indice_parc = ''

    def set_parent_fields(self, parent_feature):
        # Cette méthode remplit les attributs à partir de la feature parent
        self.section = parent_feature['section']
        self.numero = parent_feature['numero']
        self.commune = parent_feature['commune']
        self.prefixe = parent_feature['prefixe']
        self.indice_parc = parent_feature['indice_parc'] if 'indice_parc' in parent_feature.fields().names() and \
                                                            parent_feature['indice_parc'] else ''

    def connect_to_layer(self, layer=None):
        """Connexion au signal d’ajout de géométrie et suppression du formulaire natif."""
        QgsMessageLog.logMessage("connect_to_layer appelée", "gestion_forestiere", Qgis.Info)

        self.layer = layer or iface.activeLayer()
        if not self.layer or not isinstance(self.layer, QgsVectorLayer):
            QgsMessageLog.logMessage("Aucune couche polygonale active", "gestion_forestiere", Qgis.Warning)
            return

        # Vérifier que la géométrie est polygonale
        if self.layer.geometryType() != QgsWkbTypes.PolygonGeometry:
            QgsMessageLog.logMessage("La couche active n'est pas polygonale", "gestion_forestiere", Qgis.Warning)
            return

        # Supprimer le formulaire natif QGIS (empêcher ouverture auto)
        try:
            config = self.layer.editFormConfig()
            config.setSuppressForm(True)  # Cacher le formulaire natif
            self.layer.setEditFormConfig(config)  # Re-appliquer la config à la couche
            QgsMessageLog.logMessage("[InfosPolygonManager] Formulaire natif désactivé", "gestion_forestiere", Qgis.Info)
        except Exception as e:
            QgsMessageLog.logMessage(f"Erreur setSuppressForm: {e}", "gestion_forestiere", level=Qgis.Warning)

        # Connecter le signal featureAdded pour intercepter la création
        try:
            self.layer.featureAdded.connect(self.on_feature_added)
            QgsMessageLog.logMessage("Signal featureAdded connecté", "gestion_forestiere", Qgis.Info)
        except Exception as e:
            QgsMessageLog.logMessage(f"Erreur connexion featureAdded: {e}", "gestion_forestiere", level=Qgis.Warning)

    def disconnect_from_layer(self):
        """Déconnecte le signal pour éviter les fuites mémoire."""
        if self.layer:
            try:
                self.layer.featureAdded.disconnect(self.on_feature_added)
                QgsMessageLog.logMessage("Signal featureAdded déconnecté", "gestion_forestiere", Qgis.Info)
            except Exception:
                pass
            self.layer = None

    def on_feature_added(self, fid):
        """Handler appelé automatiquement quand un polygone est ajouté."""
        QgsMessageLog.logMessage(f"Feature ajoutée avec ID {fid}", "gestion_forestiere", Qgis.Info)

        # Récupérer la feature ajoutée
        feat = None
        for f in self.layer.getFeatures(QgsFeatureRequest(fid)):
            feat = f
            break
        if not feat:
            QgsMessageLog.logMessage(f"Feature {fid} introuvable", "gestion_forestiere", Qgis.Warning)
            return

        # Ouvrir la fenêtre avec la géométrie de la feature ajoutée
        self.open_dialog_from_geometry(feat.geometry(), self.layer, fid)

    def open_dialog_from_geometry(self, geom, layer, fid_enfant):
        self.layer = layer

        if not layer or not isinstance(layer, QgsVectorLayer):
            return

        if layer.geometryType() != QgsWkbTypes.PolygonGeometry:
            return

        # Trouver la géométrie contenant le nouveau polygone (i.e. la parcelle mère)
        parent_feature = None
        min_distance = float('inf')

        for f in layer.getFeatures():
            if f.id() == fid_enfant:
                continue
            if f.geometry().intersects(geom):
                dist = f.geometry().distance(geom.centroid())
                if dist < min_distance:
                    min_distance = dist
                    parent_feature = f

        if not parent_feature:
            QgsMessageLog.logMessage("❌ Aucun parent trouvé pour le trou", "gestion_forestiere", Qgis.Warning)
            return


        QgsMessageLog.logMessage(
            f"Parent trouvé: section={self.section}, numero={self.numero}, commune={self.commune}, "
            f"prefixe={self.prefixe}, indice_parc={self.indice_parc}",
            "coord_click",
            Qgis.Info
        )

        # Extraction des champs
        self.section = parent_feature['section']
        self.numero = parent_feature['numero']
        self.commune = parent_feature['commune']
        self.prefixe = parent_feature['prefixe']
        self.indice_parc = parent_feature['indice_parc'] if 'indice_parc' in parent_feature.fields().names() and \
                                                            parent_feature['indice_parc'] else ''

        # Formatage uniquement pour l’ID
        numero_id = str(self.numero).zfill(4)  # Ajoute des zéros à gauche uniquement pour l’ID

        # Construction de l’ID unique avec "0" si section a une seule lettre
        section_str = str(self.section)
        zero = "0" if len(section_str) == 1 else ""
        parc_id = f"{self.commune}{self.prefixe}{zero}{self.section}{numero_id}{self.indice_parc}"

        # Calcul de surface en ares avec reprojection vers un CRS métrique
        surface_ares = 0.0
        try:
            crs_metre = QgsCoordinateReferenceSystem("EPSG:2154")
            transformer = QgsCoordinateTransform(layer.crs(), crs_metre, QgsProject.instance())
            geom_proj = QgsGeometry(geom)
            geom_proj.transform(transformer)
            surface_m2 = geom_proj.area()
            surface_ares = round(surface_m2 / 100, 2)
            self.surface_m2 = surface_m2  # On mémorise la valeur en m² pour la réutiliser
        except Exception as e:
            QgsMessageLog.logMessage(f"⚠️ Erreur lors du calcul de surface : {e}", "gestion_forestiere", Qgis.Warning)

        # Remplissage du formulaire
        self.ui.lineSection.setText(str(self.section))
        self.ui.lineSection.setReadOnly(True)
        self.ui.lineNumero.setText(str(self.numero))
        self.ui.lineNumero.setReadOnly(True)
        self.ui.lineId.setText(str(parc_id))
        self.ui.lineId.setReadOnly(True)
        self.ui.lineLayerName.setText(self.layer.name())
        self.ui.lineSurface.setText(f"{surface_ares:.2f} ares")
        self.ui.lineFid.setText(str(fid_enfant))
        self.ui.lineFid.setReadOnly(True)

    # Masque le bouton tant que les champs ne sont pas renseignés
    def update_validate_button_state(self):
        section = self.ui.lineSection.text().strip()
        numero = self.ui.lineNumero.text().strip()
        indice = self.ui.lineIndice.text().strip()
        enable = bool(indice)
        self.ui.btnValidatePol.setEnabled(enable)

    def save_polygon_info(self):
        section = self.ui.lineSection.text().strip()
        numero = self.ui.lineNumero.text().strip()
        indice = self.ui.lineIndice.text().strip()
        possession = self.ui.checkBoxProp.isChecked()

        # Vérification des champs obligatoires
        if not section:
            QMessageBox.warning(self.dialog, "Erreur", "Le champ 'Section' est obligatoire.")
            return

        if not numero:
            QMessageBox.warning(self.dialog, "Erreur", "Le champ 'Numéro' est obligatoire.")
            return

        if not indice:
            QMessageBox.warning(self.dialog, "Erreur", "Le champ 'Indice' est obligatoire.")
            return

        # Reconstruire parc_id ici avec la valeur actuelle de indice (et numéro formaté si besoin)
        numero_id = str(self.numero).zfill(4)  # ou adapte selon ta logique de padding
        # Construire l'ID complet
        zero = "0" if len(self.section) == 1 else ""
        parc_id = f"{self.commune}{self.prefixe}{zero}{self.section}{numero_id}{indice}"

        # Enregistrement
        self.update_feature_attributes(self.section, self.numero, indice, parc_id, possession)

        QMessageBox.information(self.dialog, "Succès", "Les informations ont été sauvegardées.")
        self.dialog.accept()  # Ferme la boîte de dialogue

    def update_feature_attributes(self, section, numero, indice, parc_id, possession):
        """Met à jour les attributs de l'entité avec les valeurs saisies."""
        try:
            fid = int(self.ui.lineFid.text())
        except ValueError:
            QMessageBox.warning(self.dialog, "Erreur", "Fid invalide.")
            return

        if not self.layer or not self.layer.isEditable():
            self.layer.startEditing()

        feature_request = QgsFeatureRequest(fid)
        feature = next(self.layer.getFeatures(feature_request), None)

        if feature is None:
            QMessageBox.warning(self.dialog, "Erreur", f"Entité {fid} introuvable.")
            return

        # Mise à jour des champs
        feature['section'] = section
        feature['numero'] = numero
        feature['indice_parc'] = indice
        feature['id'] = parc_id
        feature['Possession'] = possession
        if 'contenance' in self.layer.fields().names():
            feature['contenance'] = round(self.surface_m2, 0)
        if 'SURFACE' in self.layer.fields().names():
            surface_ares = round(self.surface_m2 / 100, 2)
            feature['SURFACE'] = surface_ares

        # Appliquer les modifications
        self.layer.updateFeature(feature)
        self.layer.triggerRepaint()
