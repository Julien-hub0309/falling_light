"""etat.py - État partagé du jeu + utilitaires physiques.
Tous les modules font `import etat as E` (évite les imports circulaires).
Contient : règles du cahier des charges, collisions AABB, rayons, explosions."""
import math
import random
from ursina import *

# ---- Règles du cahier des charges ---------------------------------------
DUREE_PARTIE = 600        # 10 min
DUREE_JOUR = 300          # la nuit tombe après 5 min
NB_PILOTES = 5
NB_ZOMBIES = 30
COUT_TITAN = 10           # points dépensés pour appeler un Titan
COUT_RESPAWN = 50         # points pour éviter la mort définitive
DELAI_RESPAWN_ZOMBIE = 4
DEMI_MAP = 108
CELL = 12                 # taille d'une case de la grille de collision

# ---- Registres partagés --------------------------------------------------
boxes, grille = [], {}
pilotes, zombies, titans, loots, fumees, spawns = [], [], [], [], [], []
partie = joueur = hud = ciel = menu = None


# ---- Petits outils -------------------------------------------------------
def norm(v):
    l = v.length()
    return v * (1.0 / l) if l > 1e-9 else Vec3(0, 0, 1)


def proprietaire(src):
    """Un Titan appartient à un pilote : les points vont au pilote."""
    return getattr(src, 'owner', src)


def msg(texte):
    if hud is not None:
        hud.msg(texte)


# ---- Monde : boîtes AABB (x0, x1, z0, z1, y0, y1) -------------------------
def ajouter_box(x0, x1, z0, z1, y0, y1):
    b = (x0, x1, z0, z1, y0, y1)
    boxes.append(b)
    for i in range(int(x0 // CELL), int(x1 // CELL) + 1):
        for j in range(int(z0 // CELL), int(z1 // CELL) + 1):
            grille.setdefault((i, j), []).append(b)
    return b


def hits(x, y, z, r, h):
    """Retourne le haut (y1) de la boîte la plus haute touchée par un cylindre
    (centre x,z ; rayon r ; du pied y à y+h), ou None."""
    best = None
    for i in range(int((x - r) // CELL), int((x + r) // CELL) + 1):
        for j in range(int((z - r) // CELL), int((z + r) // CELL) + 1):
            for (x0, x1, z0, z1, y0, y1) in grille.get((i, j), ()):
                if x + r > x0 and x - r < x1 and z + r > z0 and z - r < z1 \
                        and y < y1 and y + h > y0:
                    if best is None or y1 > best:
                        best = y1
    return best


def _ray_box(o, d, b):
    x0, x1, z0, z1, y0, y1 = b
    tmin, tmax = 0.0, 1e9
    for oo, dd, lo, hi in ((o.x, d.x, x0, x1), (o.y, d.y, y0, y1), (o.z, d.z, z0, z1)):
        if abs(dd) < 1e-9:
            if oo < lo or oo > hi:
                return None
        else:
            t1, t2 = (lo - oo) / dd, (hi - oo) / dd
            if t1 > t2:
                t1, t2 = t2, t1
            tmin, tmax = max(tmin, t1), min(tmax, t2)
            if tmin > tmax:
                return None
    return tmin


def ray_world(o, d, portee):
    """Distance au premier obstacle (sol ou bâtiment) sur le rayon, max `portee`."""
    best = portee
    if d.y < -1e-6:
        t = -o.y / d.y
        if 0 < t < best:
            best = t
    for b in boxes:
        t = _ray_box(o, d, b)
        if t is not None and t < best:
            best = t
    return best


def ray_cyl(o, d, cx, cz, cy, r, h):
    """Intersection rayon / cylindre vertical. Retourne la distance ou None."""
    ox, oz = o.x - cx, o.z - cz
    a = d.x * d.x + d.z * d.z
    if a < 1e-8:
        return None
    b = 2 * (ox * d.x + oz * d.z)
    c = ox * ox + oz * oz - r * r
    disc = b * b - 4 * a * c
    if disc < 0:
        return None
    s = math.sqrt(disc)
    t = (-b - s) / (2 * a)
    if t < 0:
        t = (-b + s) / (2 * a)
        if t < 0:
            return None
    y = o.y + d.y * t
    return t if cy <= y <= cy + h else None


def _dist_seg(a, b, c):
    ab = b - a
    l2 = ab.dot(ab)
    if l2 < 1e-9:
        return (c - a).length()
    t = max(0.0, min(1.0, (c - a).dot(ab) / l2))
    return (c - (a + ab * t)).length()


def visible(a, b):
    """Ligne de vue entre deux points (bâtiments + fumigènes)."""
    d = b - a
    l = d.length()
    if l < .1:
        return True
    d = d * (1.0 / l)
    if ray_world(a, d, l) < l - .3:
        return False
    for f in fumees:
        if _dist_seg(a, b, f.position) < f.rayon * .9:
            return False
    return True


# ---- Cibles / dégâts -------------------------------------------------------
def toutes_cibles():
    return ([p for p in pilotes if p.vivant and not p.elimine]
            + list(zombies)
            + [t for t in titans if t.vivant and t.state == 'ready'])


def trace(a, b, col=color.yellow, ep=.04, dur=.05):
    l = distance(a, b)
    if l < .5:
        return
    t = Entity(model='cube', color=col, scale=(ep, ep, l), position=(a + b) * .5)
    t.look_at(b)
    destroy(t, delay=dur)


def boom(pos, taille, dur=.35, col=color.orange):
    e = Entity(model='sphere', position=pos, scale=.2, color=Color(col[0], col[1], col[2], .85))
    e.animate_scale(Vec3(taille, taille, taille), duration=dur)
    e.animate_color(Color(col[0], col[1], col[2], 0), duration=dur + .15)
    destroy(e, delay=dur + .2)


def explode(pos, rayon, degats, source=None, ignore=()):
    prop = proprietaire(source)
    for c in toutes_cibles():
        if c is source or c in ignore:
            continue
        centre = Vec3(c.x, c.y + c.h * .5, c.z)
        dd = max(0.0, distance(centre, pos) - c.r)
        if dd < rayon:
            n = degats * max(.25, 1 - dd / rayon)
            if c is prop:
                n *= .5
            c.damage(n, source)
    boom(pos, rayon * 1.6, .3)


def hitscan(owner, origin, d, portee, degats, explosif=None, debut=None,
            couleur=color.yellow):
    """Tir instantané : touche le premier pilote/zombie/titan ou mur.
    Retourne (point_final, cible, tete)."""
    d = norm(d)
    amis = {owner, proprietaire(owner)}
    for a in list(amis):
        t = getattr(a, 'titan', None)
        if t is not None:
            amis.add(t)
    tm = ray_world(origin, d, portee)
    cible = None
    for c in toutes_cibles():
        if c in amis:
            continue
        t = ray_cyl(origin, d, c.x, c.z, c.y, c.r, c.h)
        if t is not None and t < tm:
            tm, cible = t, c
    fin = origin + d * tm
    tete = False
    if cible is not None:
        gros = getattr(cible, 'est_titan', False) or getattr(cible, 'mode', 'pilot') == 'titan'
        tete = (not gros) and fin.y > cible.y + cible.h * .8
        if degats > 0:
            cible.damage(degats * (1.5 if tete else 1), owner, tete)
        if hud is not None and proprietaire(owner) is joueur:
            hud.touche(tete)
    if explosif and (cible is not None or tm < portee - 1e-3):
        explode(fin - d * .15, explosif[0], explosif[1], owner)
    trace(debut if debut is not None else origin, fin, couleur)
    return fin, cible, tete


# ---- Placement ----------------------------------------------------------------
def point_libre(rayon=1.0, loin_de=(), dmin=0, essais=80):
    for _ in range(essais):
        x = random.uniform(-DEMI_MAP + 6, DEMI_MAP - 6)
        z = random.uniform(-DEMI_MAP + 6, DEMI_MAP - 6)
        if hits(x, 0, z, rayon, 3) is not None:
            continue
        if all(math.hypot(x - p.x, z - p.z) >= dmin for p in loin_de):
            return Vec3(x, 0, z)
    return Vec3(0, 0, 0)


def spawn_loin():
    """Point de spawn le plus éloigné des pilotes vivants."""
    best, bd = spawns[0], -1
    for s in spawns:
        d = min([math.hypot(s.x - p.x, s.z - p.z) for p in pilotes if p.vivant] or [999])
        if d > bd:
            best, bd = s, d
    return best
