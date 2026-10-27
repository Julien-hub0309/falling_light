"""pistolet.py - Arme secondaire commune à toutes les classes."""
from armes.arme import Arme


def creer():
    return Arme('Pistolet', degats=17, cadence=.2, chargeur=12, reserve=60, portee=80,
                dispersion=.012, auto=False, recharge=1.0,
                vue=((.07, .09, .35), (.3, -.25, .55)), recul=.05, pref=14)
