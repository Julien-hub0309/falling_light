"""classe_1.py - ASSAUT : AR-15 + 2 grenades. Polyvalent."""
from armes import fusil, pistolet

CLASSE = dict(nom='ASSAUT', description='AR-15\n2 grenades\nPolyvalent',
              primaire=fusil.creer, secondaire=pistolet.creer,
              tactique='frag', nb_tactique=2, hp=100, vitesse=1.0)
