"""titan.py - Canon XO-16 du Titan : tir explosif, munitions infinies."""
from ursina import color
from armes.arme import Arme


def creer():
    return Arme('Canon XO-16', degats=0, cadence=.35, chargeur=10 ** 6, reserve=None,
                portee=150, dispersion=0, auto=True, recharge=0, explosif=(4, 90),
                vue=((.5, .45, 1.6), (.9, -.9, 1.4)), recul=.12, pref=35,
                couleur_trace=color.orange)
