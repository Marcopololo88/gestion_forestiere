# Gestion parcelles forestières

## Description

**Gestion parcelles forestières** est un plugin pour QGIS permettant de gérer efficacement des parcelles forestières, les essences d'arbres, les travaux, traitements passés ou prévus, ainsi que des statistiques associées.

Il propose une interface simple pour la saisie des informations et l'analyse graphique.

## Fonctionnalités principales

- Gestion des parcelles cadastrales forestières
- Suivi des essences d'arbres
- Suivi des travaux réalisés et des traitements appliqués
- Suivi des travaux et traitements prévisionnels
- Coloration automatique des parcelles selon les essences
- Exportation des données au format Excel
- Analyse statistique simple des surfaces et types
- Gestion des voisins (coordonnées)
- Configuration assistée pour la création des champs et application des styles nécessaires
- Outil avancé de création de polygones enfants via la fonction *Fill Ring* personnalisée

## Installation

1. Télécharger le plugin (fichier ZIP) ou le récupérer depuis le dépôt QGIS officiel.
2. Dans QGIS, ouvrir le menu **Extensions > Installer depuis un fichier ZIP**.
3. Sélectionner le fichier ZIP du plugin.
4. Activer l'extension depuis le gestionnaire d'extensions.

## Prérequis

Le plugin nécessite qu'une couche cadastrale au format **Geopackage** soit chargée dans le projet QGIS.

Cette couche doit comporter les champs suivants :

- `id`
- `section`
- `numero`
- `contenance`

Ces champs sont utilisés par le plugin pour l'affichage et la gestion des parcelles.

## Configuration

Avant utilisation, il est recommandé de passer par l'onglet **Configuration** du plugin pour :

- Créer les champs nécessaires si besoin
- Appliquer un style de symbologie pré-défini (`styleplugin.qml`)

## Fichiers d'aide

Le plugin est fourni avec deux fichiers d'aide :

- `docs/help.pdf` → Manuel d'utilisation du plugin
- `docs/Lire_avant.pdf` → Informations importantes avant la première utilisation

## Dépendances

Le plugin embarque la bibliothèque `xlsxwriter` (version intégrée dans le dossier `xlsxwriter_lib`) pour l'export Excel. Aucune installation manuelle supplémentaire n'est requise.

## Compatibilité

- QGIS ≥ 3.0
- Python ≥ 3.7

## Auteur

**Marc Grosjean**  
📧 marc.grosjean@wanadoo.fr

## Licence

Ce plugin est distribué sous la licence **GNU General Public License v2 (GPL v3)**.

---

© 2025 Marc Grosjean. Tous droits réservés.
