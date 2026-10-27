"""allie.py - Le Titan : tombe du ciel, puis combat en mode auto ("allié" du pilote)
quand le pilote n'est pas à bord. Le joueur peut embarquer/éjecter."""
import math
import random
from ursina import *
import etat as E
from armes import titan as arme_titan


class TitanAuto:
    """IA du Titan quand il n'est pas piloté : suit son pilote et tire sur les ennemis."""

    def __init__(self, titan):
        self.t = titan
        self.arme = arme_titan.creer()
        self.arme.cadence = 1.1
        self.cible, self.vu, self.pense = None, False, 0

    def tete(self):
        return self.t.position + Vec3(0, 5.2, 0)

    def chercher(self):
        t, best, bs = self.t, None, 1e9
        for c in E.toutes_cibles():
            if c is t or c is t.owner:
                continue
            d = math.hypot(c.x - t.x, c.z - t.z)
            lim = 55 if not getattr(c, 'est_zombie', False) else 40
            if d > lim:
                continue
            score = d * (.7 if hasattr(c, 'classe') else 1)
            if score < bs and E.visible(self.tete(), Vec3(c.x, c.y + c.h * .55, c.z)):
                best, bs = c, score
        return best

    def bouger(self, dx, dz, v, dt):
        t = self.t
        nx, nz = t.x + dx * v * dt, t.z + dz * v * dt
        if E.hits(nx, .5, t.z, 1.6, 5.5) is None:
            t.x = nx
        if E.hits(t.x, .5, nz, 1.6, 5.5) is None:
            t.z = nz

    def update(self, dt):
        t, o = self.t, self.t.owner
        self.arme.update(dt)
        self.pense -= dt
        if self.pense <= 0:
            self.pense = .4
            self.cible = self.chercher()
        c = self.cible
        if c is not None and not (getattr(c, 'vivant', False)):
            c = self.cible = None
        if c is not None:
            d = Vec3(c.x - t.x, 0, c.z - t.z)
            dist = d.length()
            dn = Vec3(t.forward.x, 0, t.forward.z)
            if dist > .1:
                dn = d * (1 / dist)
                t.rotation_y = math.degrees(math.atan2(dn.x, dn.z))
                if dist > 32:
                    self.bouger(dn.x, dn.z, 5, dt)
            cp = Vec3(c.x, c.y + c.h * .55, c.z)
            if self.arme.pret():
                org = self.tete()
                if E.visible(org, cp):
                    jit = Vec3(random.uniform(-1, 1), random.uniform(-.5, .5), random.uniform(-1, 1)) * dist * .03
                    self.arme.tirer(t, org, cp - org + jit, debut=org + dn * 2)
        elif o.vivant and not o.elimine:
            d = Vec3(o.x - t.x, 0, o.z - t.z)
            dist = d.length()
            if dist > 14:
                dn = d * (1 / dist)
                t.rotation_y = math.degrees(math.atan2(dn.x, dn.z))
                self.bouger(dn.x, dn.z, 6, dt)


class Titan(Entity):
    volatile = True
    est_titan = True

    def __init__(self, owner, spot):
        super().__init__(position=Vec3(spot.x, 70, spot.z))
        c = color.hsv(210, .15, .35)
        for sc, pos, col in (((1.2, 3.2, 1.2), (-.9, 1.6, 0), c), ((1.2, 3.2, 1.2), (.9, 1.6, 0), c),
                             ((3.4, 2.6, 2.2), (0, 4.5, 0), c), ((1, .7, .8), (0, 6.2, .2), color.hsv(20, .9, .9)),
                             ((.8, .8, 3), (-2.2, 4.2, 1), c), ((.8, .8, 3), (2.2, 4.2, 1), c)):
            Entity(parent=self, model='cube', color=col, scale=sc, position=pos)
        self.marker = Entity(model='plane', scale=7, position=(spot.x, .06, spot.z), color=Color(1, .4, 0, .6))
        self.owner, self.state, self.vy = owner, 'falling', 0
        self.hp = self.hp_max = 400
        self.r, self.h, self.vivant = 1.6, 6, True
        self.ia = TitanAuto(self)
        E.titans.append(self)

    def update(self):
        if not E.partie.actif:
            return
        dt = time.dt
        if self.state == 'falling':
            self.vy += 25 * dt
            self.y -= self.vy * dt
            if self.y <= 0:
                self.y, self.state = 0, 'ready'
                destroy(self.marker)
                E.boom(self.position + Vec3(0, .5, 0), 16, .5, color.white)
                E.explode(self.position, 9, 300, self, ignore=(self.owner,))
        elif self.state == 'ready':
            self.ia.update(dt)

    # ---- pilotage par le joueur
    def embarquer(self):
        self.state = 'embarque'
        self.enabled = False

    def debarquer(self, pos, hp):
        self.hp = hp
        self.position = Vec3(pos.x, 0, pos.z)
        self.state, self.enabled = 'ready', True

    def damage(self, n, source=None, tete=False):
        if self.state != 'ready' or not self.vivant:
            return
        self.hp -= n * .7
        if self.hp <= 0:
            self.detruire()

    def detruire(self, explose=True):
        if not self.vivant:
            return
        self.vivant = False
        if self in E.titans:
            E.titans.remove(self)
        if explose:
            E.boom(self.position + Vec3(0, 3, 0), 16, .5)
            E.explode(self.position, 10, 250, self, ignore=(self.owner,))
        o = self.owner
        if o.titan is self:
            o.titan, o.titan_cd = None, 25
        if self.state == 'falling':
            destroy(self.marker)
        destroy(self)
