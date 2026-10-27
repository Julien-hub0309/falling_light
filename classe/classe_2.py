"""classe_2.py - TACTIC : Kriss Vector + 2 grenades. Rapide, fragile."""
from armes import smg, pistolet

CLASSE = dict(nom='TACTIC', description='Kriss Vector\n2 grenades\nRapide (+10%)',
              primaire=smg.creer, secondaire=pistolet.creer,
              tactique='frag', nb_tactique=2, hp=90, vitesse=1.1)
