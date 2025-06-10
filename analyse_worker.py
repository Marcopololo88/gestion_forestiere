
# Code permettant un calcul en arrière-plan des différentes analyses sans bloquer
# l'affichage de la fenêtre principale

# analyse_worker.py
from PyQt5.QtCore import QObject, pyqtSignal
from .Analyse import (
    calcul_surface_forestiere,
    calcul_surface_friche,
    compter_parcelles_possedees,
    analyse_types_parcelles,
    analyse_types_essences,
    total_plantation,
    calcul_regroupement
)

class AnalyseWorker(QObject):
    finished = pyqtSignal(dict)

    def __init__(self, layer):
        super().__init__()
        self.layer = layer

    def run(self):
        # Exécute les calculs
        surface_forestiere = calcul_surface_forestiere(self.layer)
        surface_friche = calcul_surface_friche(self.layer)
        nb_parcelles = compter_parcelles_possedees(self.layer)
        types_parcelles = analyse_types_parcelles(self.layer)
        types_essences = analyse_types_essences(self.layer)
        total_plants = total_plantation(self.layer)
        regroupement = calcul_regroupement(self.layer)

        results = {
            "surface_forestiere": surface_forestiere,
            "surface_friche": surface_friche,
            "nb_parcelles": nb_parcelles,
            "types_parcelles": types_parcelles,
            "types_essences": types_essences,
            "total_plants": total_plants,
            "regroupement": regroupement
        }

        # Émettre le signal avec les résultats
        self.finished.emit(results)
