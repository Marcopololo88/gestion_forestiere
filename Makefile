# Makefile pour compiler les fichiers .ui et .qrc
# Plugin Gestion Forestière

# Variables
PYUIC = pyuic5
PYRCC = pyrcc5

# Fichiers sources
UI_FILES = ui_config_dialog.ui coord_click_dialog_base.ui create_polygon_dialog.ui
QRC_FILE = resources.qrc

# Cibles correspondantes
UI_PY_FILES = ui_config_dialog.py coord_click_dialog_base.py create_polygon_dialog.py
QRC_PY_FILE = resources_rc.py

# Cible par défaut
all: $(UI_PY_FILES) $(QRC_PY_FILE)

# Règle pour ui_config_dialog.ui
ui_config_dialog.py: ui_config_dialog.ui
	$(PYUIC) -o $@ $<

# Règle pour coord_click_dialog_base.ui
coord_click_dialog_base.py: coord_click_dialog_base.ui
	$(PYUIC) -o $@ $<

# Règle pour create_polygon_dialog.ui
create_polygon_dialog.py: create_polygon_dialog.ui
	$(PYUIC) -o $@ $<

# Règle pour resources.qrc
$(QRC_PY_FILE): $(QRC_FILE)
	$(PYRCC) -o $@ $<

# Nettoyage
clean:
	rm -f $(UI_PY_FILES) $(QRC_PY_FILE)
