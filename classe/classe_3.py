"""classe_3.py - SNIPER : DRS-50 + 2 fumigènes. Clic droit = lunette."""
from armes import sniper, pistolet

CLASSE = dict(nom='SNIPER', description='DRS-50 (lunette)\n2 fumigenes\nLongue portee',
              primaire=sniper.creer, secondaire=pistolet.creer,
              tactique='fumigene', nb_tactique=2, hp=85, vitesse=1.0)
