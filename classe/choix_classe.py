"""choix_classe.py - Liste des classes, application du loadout, menu de sélection."""
import random
from ursina import *
from classe.classe_1 import CLASSE as ASSAUT
from classe.classe_2 import CLASSE as TACTIC
from classe.classe_3 import CLASSE as SNIPER
from classe.classe_4 import CLASSE as BRECHE

CLASSES = [ASSAUT, TACTIC, SNIPER, BRECHE]


def aleatoire():
    return random.choice(CLASSES)


def appliquer(p, c):
    """Donne à un pilote (joueur ou bot) l'équipement d'une classe."""
    p.classe = c
    p.hp_max = p.hp = c['hp']
    p.armure = 0
    p.armes = [c['primaire'](), c['secondaire']()]
    p.idx = 0
    p.tactique, p.nb_tactique = c['tactique'], c['nb_tactique']
    p.vitesse_mult = c['vitesse']


class MenuClasse(Entity):
    def __init__(self, on_choix):
        super().__init__(parent=camera.ui)
        self.on_choix = on_choix
        Text(parent=self, text='FALLING LIGHT', origin=(0, 0), y=.40, scale=3.2, color=color.orange)
        Text(parent=self, text='Choisis ta classe (clic ou touches 1-4)', origin=(0, 0), y=.30, scale=1.4)
        for i, c in enumerate(CLASSES):
            x = -.66 + i * .44
            b = Button(parent=self, text=f"{i + 1}\n{c['nom']}", position=(x, .1),
                       scale=(.4, .25), color=color.dark_gray)
            b.on_click = (lambda c=c: self.choisir(c))
            Text(parent=self, text=c['description'], position=(x - .18, -.08), scale=.9)
        Text(parent=self, origin=(0, 0), y=-.30, scale=.9, color=color.light_gray,
             text='ZQSD/WASD bouger | Espace saut / double saut / saut mural / grimper | Shift sprint | Ctrl glisser\n'
                  'Clic tir | Clic droit viser | R recharger | 1-2 / molette arme | G grenade | X grappin\n'
                  'F appeler un Titan (-10 pts) | E embarquer / ejecter | Echap quitter')

    def choisir(self, c):
        self.on_choix(c)

    def input(self, key):
        if key in ('1', '2', '3', '4'):
            self.choisir(CLASSES[int(key) - 1])
