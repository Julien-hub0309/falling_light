"""classe_4.py - BRECHE : fusil à pompe + grenade + fumigène. Résistant, lent."""
from armes import shotgun, pistolet

CLASSE = dict(nom='BRECHE', description='Fusil a pompe\nResistant (120 PV)\nLent (-8%)',
              primaire=shotgun.creer, secondaire=pistolet.creer,
              tactique='frag', nb_tactique=3, hp=120, vitesse=.92)
