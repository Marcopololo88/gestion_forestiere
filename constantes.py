


# constantes.py
TYPE_PARC_LIBELLES = {
    1: "Pré",
    2: "Semis (jusque 2m)",
    3: "Gaulis (2 à 6m)",
    4: "Jeune futaie (diam 11 à 25)",
    5: "Futaie adulte (diam > 25)",
    6: "Vieille Futaie",
    7: "Futaie Irrégulière",
    8: "Taillis",
    9: "Friche bouleaux",
    10: "Régénération naturelle",
    11: "Vente en cours",
    12: "Achat en cours",
    13: "Echanges",
    14: "Friche Feuillus",
    15: "Perchis (diam 6 à 10)"
}

# 🔥 Nouveau : dictionnaire qui décrit le nombre de combobox par onglet - Variables globales
SAISIE_COMBO_COUNTS = {
    "plant": 4,
    "Tvx": 6,
    "Trait": 6,
    "Prev": 4,
}

# 🔧 Paramètres pour remplir les combos de saisie (prefix, nom du combo, index de colonne)
SAISIE_COMBO_SETTINGS = [
    ("plant","comboPlant",0),
    ("Tvx", "comboTvx", 1),
    ("Trait", "comboTrait", 2),
    ("Prev", "comboPrev", 1),
]