"""map.py - Construction de la ville : bâtiments accessibles par parkour (caisses
empilées à grimper), couvertures, murs d'enceinte, points de spawn et loot."""
import random
from ursina import *
import etat as E
from map.loot import Loot

PAS = 2.2   # hauteur d'une caisse = hauteur max qu'on peut grimper d'un coup


def batiment(x0, z0, w, d, n):
    """Bâtiment de hauteur 2.2*n + une chaîne de n caisses le long du mur ouest
    pour monter sur le toit (Espace près d'un rebord = grimper)."""
    h = PAS * n
    Entity(model='cube', position=(x0 + w / 2, h / 2, z0 + d / 2), scale=(w, h, d),
           color=color.hsv(random.uniform(190, 230), .12, random.uniform(.35, .55)),
           texture='white_cube', texture_scale=(max(w, d) / 4, h / 4))
    E.ajouter_box(x0, x0 + w, z0, z0 + d, 0, h)
    for k in range(n):
        top = PAS * (k + 1)
        cz = z0 + 2 * k
        Entity(model='cube', position=(x0 - 1, top / 2, cz + 1), scale=(2, top, 2),
               color=color.hsv(28 if k % 2 else 35, .6, .6), texture='white_cube',
               texture_scale=(1, top / 2))
        E.ajouter_box(x0 - 2, x0, cz, cz + 2, 0, top)
    return h


def couverture(x, z, w, d, h):
    Entity(model='cube', position=(x, h / 2, z), scale=(w, h, d), color=color.hsv(20, .5, .4),
           texture='white_cube', texture_scale=(w / 2, h / 2))
    E.ajouter_box(x - w / 2, x + w / 2, z - d / 2, z + d / 2, 0, h)


def construire_map():
    random.seed(3)
    A = E.DEMI_MAP
    # sol
    Entity(model='plane', scale=2 * (A + 40), texture='white_cube', texture_scale=(A + 40, A + 40),
           color=color.hsv(215, .1, .45))
    # murs d'enceinte (invisibles pour le sol, hauts de 40 m)
    for (x, z, w, d) in ((0, A + 1, 2 * A + 4, 2), (0, -A - 1, 2 * A + 4, 2),
                         (A + 1, 0, 2, 2 * A + 4), (-A - 1, 0, 2, 2 * A + 4)):
        Entity(model='cube', position=(x, 20, z), scale=(w, 40, d), color=color.hsv(0, 0, .2))
        E.ajouter_box(x - w / 2, x + w / 2, z - d / 2, z + d / 2, 0, 40)

    # bâtiments sur une grille 4x4 (3 cases laissées vides)
    centres = [-78, -26, 26, 78]
    cases = [(cx, cz) for cx in centres for cz in centres]
    for c in random.sample(cases, 3):
        cases.remove(c)
    toits = []
    for cx, cz in cases:
        n = random.choice((4, 6, 8))
        w = random.uniform(14, 20)
        d = max(random.uniform(16, 24), 2 * n + 2)
        bx, bz = cx + random.uniform(-6, 6), cz + random.uniform(-6, 6)
        h = batiment(bx - w / 2, bz - d / 2, w, d, n)
        toits.append((bx, bz, w, d, h))

    # couvertures au sol
    for _ in range(30):
        p = E.point_libre(3)
        couverture(p.x, p.z, random.uniform(2, 5), random.uniform(1, 2), random.uniform(1.2, 2.4))

    # points de spawn : un par coin + centre
    E.spawns.clear()
    for cx, cz in ((-88, -88), (88, -88), (88, 88), (-88, 88), (0, 0)):
        for _ in range(80):
            x, z = cx + random.uniform(-12, 12), cz + random.uniform(-12, 12)
            if E.hits(x, 0, z, 1.5, 3) is None:
                E.spawns.append(Vec3(x, 0, z))
                break
        else:
            E.spawns.append(Vec3(cx * .5, 0, cz * .5))

    # loot : sur les toits (récompense du parkour) + au sol
    for bx, bz, w, d, h in toits:
        for _ in range(2):
            Loot(Vec3(bx + random.uniform(-w / 3, w / 3), h, bz + random.uniform(-d / 3, d / 3)))
    for _ in range(22):
        Loot(E.point_libre(1.2))
