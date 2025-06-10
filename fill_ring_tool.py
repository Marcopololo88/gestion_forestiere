from qgis.PyQt.QtCore import pyqtSignal, QObject, Qt
from qgis.gui import QgsMapToolEdit, QgsRubberBand
from qgis.core import (
    QgsWkbTypes,
    QgsGeometry,
    QgsPointXY,
    QgsFeature,
    QgsProject,
    QgsFeatureRequest,
)
from qgis.PyQt.QtGui import QCursor,QPixmap

import os

from .infos_polygon import InfosPolygonManager
from .create_polygon_dialog import Ui_createPolygonDialog
from qgis.PyQt.QtWidgets import QDialog

class FillRingTool(QgsMapToolEdit, QObject):
    ring_created = pyqtSignal(QgsGeometry)  # Signal émis à la fin du dessin, avec la géométrie du trou

    def __init__(self, canvas, layer, callback=None):
        super().__init__(canvas)  # Appelle le constructeur de QgsMapToolEdit avec canvas
        self.canvas = canvas
        self.layer = layer
        self.callback = callback

        self.points = []
        self.rubber_band = QgsRubberBand(self.canvas, QgsWkbTypes.PolygonGeometry)
        self.rubber_band.setColor(Qt.red)
        self.rubber_band.setWidth(2)



        if self.callback:
            self.ring_created.connect(self.callback)

    def activate(self):
        super().activate()

        plugin_dir = os.path.dirname(__file__)
        cursor_path = os.path.join(plugin_dir, "icons", "cursor_ringfill.png")
        if os.path.exists(cursor_path):
            pixmap = QPixmap(cursor_path)
            cursor = QCursor(pixmap, 16, 16)  # (hotspot_x, hotspot_y)
            self.canvas.setCursor(cursor)
        else:
            print("❌ Curseur personnalisé non trouvé :", cursor_path)

    def deactivate(self):
        super().deactivate()
        self.canvas.unsetCursor()

    def canvasPressEvent(self, event):
        point = self.toMapCoordinates(event.pos())

        if event.button() == Qt.LeftButton:
            # Ajouter un point
            self.points.append(point)
            self.rubber_band.addPoint(point, True)
            self.rubber_band.show()

        elif event.button() == Qt.RightButton:
            # Terminer le polygone sur clic droit
            self.finish_polygon()

    def canvasMoveEvent(self, event):
        # Afficher le point temporaire pendant le mouvement (optionnel)
        if self.points:
            point = self.toMapCoordinates(event.pos())
            self.rubber_band.movePoint(point)

    def canvasReleaseEvent(self, event):
        # Rien à faire au relâchement, on valide au double-clic

        pass

    def keyPressEvent(self, event):
        # Valider le polygone au double-clic ou touche Entrée
        key = event.key()
        if key == Qt.Key_Return or key == Qt.Key_Enter:
            self.finish_polygon()
        elif key == Qt.Key_Escape:
            self.cancel()

    def finish_polygon(self):
        if len(self.points) < 3:
            self.cancel()
            return

        self.rubber_band.closePoints()
        ring_geom = QgsGeometry.fromPolygonXY([self.points])

        # Trouver la parcelle mère
        parent_feature = None
        for f in self.layer.getFeatures():
            if f.geometry().contains(ring_geom.centroid().asPoint()):
                parent_feature = f
                break

        if not parent_feature:

            self.cancel()
            return

        parent_geom = parent_feature.geometry()

        print("Type géométrie mère:", parent_geom.type())  # 2 = polygone
        print("Type géométrie mère WKB:", parent_geom.wkbType())
        print("Est multipolygone ? :", parent_geom.isMultipart())

        if parent_geom.isMultipart():
            # Cas multipolygone : on modifie le premier polygone trouvé contenant le point
            multi_poly = parent_geom.asMultiPolygon()
            if not multi_poly:
                print("❌ Géométrie multipolygone invalide.")
                self.cancel()
                return

            # Trouver quel polygone contient le centroid du trou
            hole_point = ring_geom.centroid().asPoint()
            poly_index = None
            for i, poly in enumerate(multi_poly):
                # poly est une liste : [anneau extérieur, trous...]
                exterior_ring = poly[0]
                exterior_geom = QgsGeometry.fromPolygonXY([exterior_ring])
                if exterior_geom.contains(hole_point):
                    poly_index = i
                    break

            if poly_index is None:
                print("❌ Aucun polygone dans le multipolygone ne contient le trou.")
                self.cancel()
                return

            # Ajouter le trou aux anneaux intérieurs de ce polygone
            multi_poly[poly_index].append(self.points)

            # Créer la nouvelle géométrie multipolygone modifiée
            new_geom = QgsGeometry.fromMultiPolygonXY(multi_poly)
        else:
            # Cas polygone simple
            if not parent_geom.addRing(self.points):
                print("❌ Échec de l'ajout du trou à la géométrie simple.")
                self.cancel()
                return
            new_geom = parent_geom

        if not self.layer.isEditable():
            self.layer.startEditing()

        print(f"ℹ️ Mise à jour géométrie mère, feature id {parent_feature.id()}")
        res = self.layer.changeGeometry(parent_feature.id(), new_geom)

        if res:
            print("✅ Géométrie mère mise à jour dans la couche (changeGeometry réussi)")
        else:
            print("❌ Échec de la mise à jour géométrie mère dans la couche")
            self.cancel()
            return

        self.layer.updateExtents()
        self.layer.triggerRepaint()

        if self.layer.isEditable():
            print("ℹ️ Commit des modifications")
            success_commit = self.layer.commitChanges()
            if success_commit:
                print("✅ Commit réussi")
            else:
                print("❌ Échec du commit")

        # Ajouter entité trou
        new_feat = QgsFeature(self.layer.fields())
        new_feat.setGeometry(ring_geom)
        success, added_features = self.layer.dataProvider().addFeatures([new_feat])

        if not success or not added_features:
            print("❌ Échec de l'ajout de l'entité trou.")
            self.cancel()
            return
        else:
            print("✅ Entité trou ajoutée à la couche")

        fid = added_features[0].id()
        print(f"ℹ️ Fid de l'entité trou créée : {fid}")

        inserted_feature = next(self.layer.getFeatures(QgsFeatureRequest(fid)))

        # 🎯 Créer et afficher la boîte de dialogue
        from .create_polygon_dialog import Ui_createPolygonDialog
        from .infos_polygon import InfosPolygonManager
        from qgis.PyQt.QtWidgets import QDialog

        dialog = QDialog()
        ui = Ui_createPolygonDialog()
        ui.setupUi(dialog)

        manager = InfosPolygonManager(ui,dialog)
        manager.open_dialog_from_geometry(inserted_feature.geometry(), self.layer, fid)

        print("💬 Ouverture du formulaire avec fid :", fid)
        dialog.exec_()

        # Nettoyage
        self.points = []
        self.rubber_band.reset(QgsWkbTypes.PolygonGeometry)

    def cancel(self):
        print("⛔ Annulation du dessin (Esc)")
        self.points = []
        self.rubber_band.reset(QgsWkbTypes.PolygonGeometry)
        self.canvas.refresh()  # Facultatif mais utile pour forcer le rafraîchissement

