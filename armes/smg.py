"""smg.py - Kriss Vector (classe Tactic)."""
from armes.arme import Arme


def creer():
    return Arme('Kriss Vector', degats=9, cadence=.055, chargeur=33, reserve=165,
                portee=90, dispersion=.03, auto=True, recharge=1.3,
                vue=((.1, .12, .45), (.3, -.27, .6)), recul=.04, pref=12)
