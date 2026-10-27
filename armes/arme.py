"""arme.py - Classe de base de toutes les armes (joueur, bots, titans)."""
import random
from ursina import *
import etat as E


class Arme:
    def __init__(self, nom, degats, cadence, chargeur, reserve, portee=120,
                 dispersion=.012, plombs=1, auto=True, recharge=1.4, zoom=None,
                 explosif=None, vue=((.09, .11, .55), (.32, -.28, .7)), recul=.06,
                 pref=20, couleur_trace=color.yellow):
        self.nom, self.degats, self.cadence = nom, degats, cadence
        self.chargeur, self.reserve = chargeur, reserve      # reserve None = infinie
        self.portee, self.dispersion, self.plombs = portee, dispersion, plombs
        self.auto, self.t_recharge, self.zoom = auto, recharge, zoom
        self.explosif, self.vue, self.recul = explosif, vue, recul
        self.pref, self.couleur_trace = pref, couleur_trace   # pref = distance de combat des bots
        self.munitions = chargeur
        self.cool, self.rech = 0.0, 0.0

    # ---- état
    def update(self, dt):
        self.cool -= dt
        if self.rech > 0:
            self.rech -= dt
            if self.rech <= 0:
                self._fin_recharge()

    def pret(self):
        return self.cool <= 0 and self.rech <= 0

    def recharger(self):
        if self.rech > 0 or self.munitions >= self.chargeur:
            return False
        if self.reserve is not None and self.reserve <= 0:
            return False
        self.rech = self.t_recharge
        return True

    def _fin_recharge(self):
        besoin = self.chargeur - self.munitions
        if self.reserve is None:
            self.munitions = self.chargeur
        else:
            pris = min(besoin, self.reserve)
            self.munitions += pris
            self.reserve -= pris

    def ajouter_munitions(self, n):
        if self.reserve is not None:
            self.reserve += int(n)

    # ---- tir
    def tirer(self, owner, origin, d, debut=None, zoomed=False):
        if not self.pret():
            return False
        if self.munitions <= 0:
            self.recharger()
            return False
        self.munitions -= 1
        self.cool = self.cadence
        base = E.norm(d)
        droite = Vec3(base.z, 0, -base.x)
        droite = E.norm(droite) if droite.length() > 1e-6 else Vec3(1, 0, 0)
        haut = E.norm(base.cross(droite))
        sp = self.dispersion * (.08 if zoomed else 1)
        for _ in range(self.plombs):
            dd = base + droite * random.uniform(-sp, sp) + haut * random.uniform(-sp, sp)
            E.hitscan(owner, origin, dd, self.portee, self.degats,
                      explosif=self.explosif, debut=debut, couleur=self.couleur_trace)
        return True
