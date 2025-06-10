
#Imports
import sys
import os

from qgis.core import (
    QgsVectorLayer,
    QgsFeature,
    QgsSpatialIndex,
    QgsFeatureRequest,
)

from PyQt5.QtWidgets import QFileDialog, QMessageBox
from datetime import datetime
from qgis.PyQt.QtCore import QVariant

from typing import List, Tuple, Dict

from .constantes import TYPE_PARC_LIBELLES

# Statistiques et analyses des éléments forestiers

def calcul_surface_forestiere(layer):
    total_surface_m2 = 0

    for feature in layer.getFeatures():
        possession = feature["Possession"]
        type_parc = feature["typeParc"]
        surface = feature["SURFACE"]
        indice_parc = feature["indice_parc"]

        # Ne pas inclure si indice_parc est défini (non nul, non vide)
        if indice_parc not in (None, "", 0):
            continue

        try:
            surface_val = float(surface)
        except (TypeError, ValueError):
            surface_val = 0

        if possession and type_parc != 1:
            total_surface_m2 += surface_val * 100

    surface_str = convertir_surface_ha(total_surface_m2)
    return surface_str


def calcul_surface_friche(layer):
    total_surface_m2 = 0

    for feature in layer.getFeatures():
        possession = feature["Possession"]
        type_parc = feature["typeParc"]
        surface = feature["SURFACE"]
        indice_parc = feature["indice_parc"]

        # Ne pas inclure si indice_parc est défini (non nul, non vide)
        if indice_parc not in (None, "", 0):
            continue

        try:
            surface_val = float(surface)
        except (TypeError, ValueError):
            surface_val = 0

        if possession and type_parc in (8, 9, 14):
            total_surface_m2 += surface_val * 100

    surface_str = convertir_surface_ha(total_surface_m2)
    return surface_str

def compter_parcelles_possedees(layer):
    """
    Compte les entités dont le champ 'Possession' est True.
    """
    total = 0

    for feature in layer.getFeatures():
        possession = feature["Possession"]

        if possession:
            total += 1

    return total


def analyse_types_parcelles(layer, type_parc_min=2, type_parc_max=14, top_n=5):
    """
    Analyse la répartition des surfaces par type de parcelle (2 à 14),
    affiche les `top_n` types les plus représentés + une catégorie "Autres".
    """

    surfaces_par_type = {}
    total_surface_m2 = 0.0  # float

    for feature in layer.getFeatures():
        type_parc = feature["typeParc"]

        # Conversion explicite de surface en float
        try:
            surface = float(feature["SURFACE"])
        except (TypeError, ValueError):
            surface = 0.0

        if type_parc_min <= type_parc <= type_parc_max:
            total_surface_m2 += surface
            if type_parc in surfaces_par_type:
                surfaces_par_type[type_parc] += surface
            else:
                surfaces_par_type[type_parc] = surface

    if total_surface_m2 == 0:
        return "Aucune donnée disponible"

    # Calcul des pourcentages et tri
    pourcentages = {
        type_parc: (surface / total_surface_m2) * 100
        for type_parc, surface in surfaces_par_type.items()
    }
    sorted_types = sorted(pourcentages.items(), key=lambda x: x[1], reverse=True)

    top_types = sorted_types[:top_n]
    autres = sorted_types[top_n:]

    result_lines = []
    for type_parc, pourcentage in top_types:
        nom_type = TYPE_PARC_LIBELLES.get(type_parc, f"Type {type_parc}")
        result_lines.append(f"{nom_type} : {pourcentage:.1f} %")

    autres_pourcentage = sum(p[1] for p in autres)
    if autres_pourcentage > 0:
        result_lines.append(f"Autres : {autres_pourcentage:.1f} %")

    return "\n".join(result_lines)

def analyse_types_essences(layer, top_n=5):
    """
    Analyse la répartition des surfaces pondérées par type d'essence,
    en utilisant les champs plant1 à plant4 et leurs pourcentages Tx1 à Tx4.
    Affiche les `top_n` types les plus représentés + une catégorie "Autres".
    """

    surfaces_par_essence = {}
    total_surface_m2 = 0.0

    for feature in layer.getFeatures():
        try:
            surface = float(feature["SURFACE"])
        except (TypeError, ValueError):
            surface = 0.0

        for i in range(1, 5):
            nom_essence = feature[f"plant{i}"]
            pourcent = feature[f"Tx{i}"]

            if nom_essence is None or nom_essence == "":
                continue

            try:
                poids = (float(pourcent) / 100.0) * surface
            except (TypeError, ValueError, ZeroDivisionError):
                poids = 0.0

            total_surface_m2 += poids
            surfaces_par_essence[nom_essence] = surfaces_par_essence.get(nom_essence, 0.0) + poids

    if total_surface_m2 == 0:
        return "Aucune donnée disponible"

    # Calcul des pourcentages
    pourcentages = {
        essence: (surface / total_surface_m2) * 100
        for essence, surface in surfaces_par_essence.items()
    }
    sorted_essences = sorted(pourcentages.items(), key=lambda x: x[1], reverse=True)

    top_essences = sorted_essences[:top_n]
    autres = sorted_essences[top_n:]

    result_lines = []
    for essence, pourcentage in top_essences:
        result_lines.append(f"{essence} : {pourcentage:.1f} %")

    autres_pourcentage = sum(p[1] for p in autres)
    if autres_pourcentage > 0:
        result_lines.append(f"Autres : {autres_pourcentage:.1f} %")

    return "\n".join(result_lines)

def convertir_surface_ha(surface_m2):
    """
    Convertit une surface en m² en hectares, ares et centiares.
    Ex: 21789 m² -> '2 ha 17 a 89 ca'
    """
    ha = int(surface_m2) // 10000
    reste = int(surface_m2) % 10000
    ares = reste // 100
    centiares = reste % 100
    return f"{ha} ha {ares} a {centiares} ca"


def total_plantation (layer):

    total_plants = 0

    for feature in layer. getFeatures():
        plants = feature["totalplants"]
        if plants is not None and plants != QVariant():
            total_plants += int(plants)

    return total_plants

def calcul_regroupement(layer):
    """
    Regroupe les entités contiguës dont 'possession' est True,
    retourne les 3 plus grands regroupements en surface totale (champ 'contenance'),
    et affiche pour chaque groupe le numéro de la plus grande parcelle (avec section)
    et la surface totale.
    """

    # Créer un index spatial
    index = QgsSpatialIndex(layer.getFeatures())

    # Mettre en cache toutes les entités ET leur géométrie
    features_dict = {f.id(): (f, f.geometry()) for f in layer.getFeatures()}

    visited = set()
    regroupements = []

    # Boucle principale sur chaque entité non encore visitée
    for fid, (feat, geom) in features_dict.items():
        if fid in visited or not feat['possession']:
            continue

        groupe = []
        to_visit = [fid]

        while to_visit:
            current_fid = to_visit.pop()
            if current_fid in visited:
                continue
            visited.add(current_fid)

            current_feat, current_geom = features_dict[current_fid]

            if not current_feat['possession']:
                continue

            groupe.append(current_feat)

            # Chercher les voisins candidats (bbox intersecte)
            for neighbor_id in index.intersects(current_geom.boundingBox()):
                if neighbor_id not in visited:
                    neighbor_feat, neighbor_geom = features_dict.get(neighbor_id, (None, None))
                    if neighbor_feat and neighbor_geom and neighbor_feat['possession']:
                        # Test topologique touches()
                        if current_geom.touches(neighbor_geom):
                            to_visit.append(neighbor_id)

        # Ajouter le groupe trouvé s'il est non vide
        if groupe:
            regroupements.append(groupe)

    # Trier les groupes par contenance totale décroissante
    regroupements.sort(
        key=lambda grp: sum(f['contenance'] for f in grp if f['contenance'] is not None),
        reverse=True
    )

    # Prendre les 3 plus gros groupes
    top3 = regroupements[:3]

    # Construire le texte de retour
    result_lines = []
    for i, groupe in enumerate(top3, start=1):
        surface_totale = sum(f['contenance'] for f in groupe if f['contenance'] is not None)
        surface_str = convertir_surface_ha(surface_totale)

        # Trouver la parcelle avec la plus grande contenance
        plus_grande_parcelle = max(
            groupe,
            key=lambda f: f['contenance'] if f['contenance'] is not None else 0
        )
        section = plus_grande_parcelle['section']
        numero = plus_grande_parcelle['numero']

        result_lines.append(f"{i} - {section}{numero} = {surface_str}")

    return '\n'.join(result_lines)



def export_to_excel(self):

    # Ajouter le chemin vers dossier local xlsxwriter_lib
    xlsxwriter_path = os.path.join(os.path.dirname(__file__), "xlsxwriter_lib")
    if xlsxwriter_path not in sys.path:
        sys.path.insert(0, xlsxwriter_path)
    print("Début de export_to_excel - contrôle du module xlsxwriter")
    try:
        import xlsxwriter
        print("xlsxwriter est disponible.")
    except ImportError:
        reply = QMessageBox.question(
            None, "Module manquant",
            "Le module 'xlsxwriter' est manquant.\n"
            "Voulez-vous tenter d’installer 'xlsxwriter' depuis le dossier local ?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            try:
                # Tentative de recharger le module après ajout du dossier
                import importlib
                importlib.invalidate_caches()
                xlsxwriter = importlib.import_module("xlsxwriter")
            except ImportError:
                QMessageBox.critical(
                    None, "Installation échouée",
                    "L'installation locale de 'xlsxwriter' a échoué.\n"
                    "L'export est annulé."
                )
                return
        else:
            QMessageBox.information(None, "Export annulé", "Export annulé car 'xlsxwriter' est manquant.")
            return

    layer = self.iface.activeLayer()
    if not layer or not isinstance(layer, QgsVectorLayer):
        QMessageBox.warning(None, "Export", "Veuillez sélectionner une couche valide.")
        return

    # Champs toujours exportés dans la sélection spécifique
    champs_generaux = [
        "section", "numero", "indice_parc","contenance", "SURFACE", "Nous",
         "plant1", "plant2", "plant3", "plant4", "Tx1","Tx2","Tx3","Tx4",
        "annee", "totalplants", "typeParc"
    ]

    # Champs exclus systématiquement (jamais exportés)
    champs_exclus = {"fid", "commune", "prefixe", "arpente", "possession", "created", "updated","nom_Voisin",
                     "adresse_Voisin","mail_Voisin","tel_Voisin"}

    # Récupérer la liste des champs disponibles dans la couche
    available_fields = [field.name() for field in layer.fields()]

    if self.dlg.checkToutExport.isChecked():
        # Exporter tous les champs sauf ceux exclus
        export_fields = [f for f in available_fields if f.lower() not in champs_exclus]

    else:
        export_fields = champs_generaux.copy()

        if self.dlg.checkTravExport.isChecked():
            export_fields += [f"Tvx{i}" for i in range(1, 7)]
            export_fields += [f"dateTvx{i}" for i in range(1, 7)]
            export_fields += [f"remTvx{i}" for i in range(1, 7)]

        if self.dlg.checkTraitExport.isChecked():
            export_fields += [f"Trait{i}" for i in range(1, 7)]
            export_fields += [f"dateTrait{i}" for i in range(1, 7)]
            export_fields += [f"remTrait{i}" for i in range(1, 7)]

        if self.dlg.checkPrevExport.isChecked():
            export_fields += [f"Prev{i}" for i in range(1, 5)]
            export_fields += [f"datePrev{i}" for i in range(1, 5)]
            export_fields += [f"remPrev{i}" for i in range(1, 5)]

    # Supprimer doublons, retirer Possession, vérifier existence
    available_fields = [field.name() for field in layer.fields()]
    export_fields = list(dict.fromkeys(export_fields))  # garde l'ordre, supprime doublons
    export_fields = [f for f in export_fields if f in available_fields and f != "Possession"]

    if not export_fields:
        QMessageBox.warning(None, "Export", "Aucun champ valide sélectionné pour l'export.")
        return

    # Choisir le dossier
    folder = QFileDialog.getExistingDirectory(None, "Choisir un dossier d'export")
    if not folder:
        return

    # Nom du fichier avec date
    date_str = datetime.now().strftime("%Y%m%d")
    filename = f"Export_{date_str}.xlsx"
    output_file = os.path.join(folder, filename)

    # Création du fichier Excel
    workbook = xlsxwriter.Workbook(output_file)
    worksheet = workbook.add_worksheet()

    # Écrire les en-têtes
    for col, field_name in enumerate(export_fields):
        worksheet.write(0, col, field_name)
    # Écrire les données : uniquement celles avec Possession = True
    row = 1
    for feature in layer.getFeatures():
        if not feature["Possession"]:
            continue
        for col, field_name in enumerate(export_fields):
            value = feature[field_name]
            if field_name == "Nous":
                try:
                    key = int(value)
                    libelle = TYPE_PARC_LIBELLES.get(key, str(value))
                except (ValueError, TypeError):
                    libelle = str(value)
                libelle_str = str(libelle).strip()
                clean_value = "" if libelle_str.upper() == "NULL" else libelle_str
                worksheet.write(row, col, clean_value)
            else:
                value_str = str(value).strip() if value is not None else ""
                clean_value = "" if value_str.upper() == "NULL" else value_str
                worksheet.write(row, col, clean_value)
        row += 1

    # Ajustement la largeur des colonnes
    for col, field_name in enumerate(export_fields):
        # Calculer la largeur max entre l'en-tête et les valeurs de la colonne
        max_len = len(field_name)
        for feature in layer.getFeatures():
            if not feature["Possession"]:
                continue
            value = feature[field_name]
            value_str = str(value) if value is not None else ""
            if len(value_str) > max_len:
                max_len = len(value_str)
        # On fixe la largeur avec une marge, par exemple 1.2x la taille max
        worksheet.set_column(col, col, max_len * 1.2)

    workbook.close()
    QMessageBox.information(self.dlg, "Export", f"Export terminé :\n{output_file}")

    # Ouvrir automatiquement le fichier Excel si demandé
    if self.dlg.checkOpenExport.isChecked():
        try:
            os.startfile(output_file)
        except Exception as e:
            QMessageBox.warning(self.dlg, "Erreur",
                                f"Impossible d’ouvrir le fichier automatiquement :\n{str(e)}")

