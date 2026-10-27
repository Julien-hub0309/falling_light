"""shotgun.py - Fusil à pompe (classe Brèche)."""
from armes.arme import Arme


def creer():
    return Arme('Pompe', degats=9, plombs=8, cadence=.85, chargeur=6, reserve=30,
                portee=40, dispersion=.07, auto=False, recharge=2.0,
                vue=((.1, .12, .6), (.32, -.28, .7)), recul=.15, pref=8)
