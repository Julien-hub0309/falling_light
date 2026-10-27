# FALLING LIGHT - FPS Titanfall x Dying Light (Python + Ursina)
# Installation :  pip install ursina
# Lancement    :  python titanfall.py
from ursina import *
import etat as E
from map.map import construire_map
from bot.joueur import Player
from bot.ennemie import PiloteIA
from HUD.hud import HUD
from partie import Partie
from classe.choix_classe import MenuClasse

app = Ursina(title='FALLING LIGHT')
window.exit_button.visible = False
E.ciel = Sky()
scene.fog_color = color.hsv(215, .25, .85)
scene.fog_density = (40, 260)
mouse.locked = False

construire_map()                      # bâtiments, couvertures, spawns, loot
E.joueur = Player()                   # pilote 1 : toi
for nom, col in (('Alpha', color.red), ('Bravo', color.orange),
                 ('Charlie', color.violet), ('Delta', color.green)):
    PiloteIA(nom, col)                # pilotes 2 à 5 : bots rivaux
E.hud = HUD()
E.partie = Partie(E.ciel)
E.menu = MenuClasse(E.partie.demarrer)
E.partie.ouvrir_menu()

app.run()
