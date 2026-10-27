"""zombie.py - Zombies : lents et faibles le jour, rapides et forts la nuit."""
import math
import random
from ursina import *
import etat as E


class Zombie(Entity):
    volatile = True
    est_zombie = True

    def __init__(self, pos):
        super().__init__(position=Vec3(pos.x, 0, pos.z))
        self.r, self.h, self.vivant = .45, 1.9, True
        self.nuit = E.partie.nuit
        self.hp = self.hp_max = 70 if self.nuit else 40
        self.var = random.uniform(.85, 1.15)
        self.cible, self.pense, self.atk, self.flash = None, 0, 0, 0
        self.dest, self.dest_t, self.anim = None, 0, random.uniform(0, 6)
        self.corps = Entity(parent=self, model='cube', scale=(.7, 1.1, .4), y=1.0)
        self.tete = Entity(parent=self, model='cube', scale=(.4, .4, .4), y=1.75)
        self.bras = [Entity(parent=self, model='cube', scale=(.2, .2, .8), position=(x, 1.35, .45))
                     for x in (-.45, .45)]
        self.parts = [self.corps, self.tete] + self.bras
        self.recolorier()
        E.zombies.append(self)

    # ---- stats selon jour/nuit ----------------------------------------------
    @property
    def vitesse(self):
        return (4.6 if E.partie.nuit else 2.0) * self.var

    @property
    def degats(self):
        return 14 if E.partie.nuit else 7

    @property
    def detection(self):
        return 75 if E.partie.nuit else 32

    def recolorier(self):
        col = color.hsv(0, .75, .5) if E.partie.nuit else color.hsv(95, .45, .45)
        for e in self.parts:
            e.color = col
        self.tete.color = color.hsv(20 if E.partie.nuit else 80, .4, .6)
        self.base = col

    def passer_nuit(self):
        """Appelé quand la nuit tombe : zombies plus forts (+75 % PV)."""
        self.hp *= 1.75
        self.hp_max *= 1.75
        self.recolorier()

    # ---- IA --------------------------------------------------------------------
    def trouver_cible(self):
        best, bd = None, self.detection
        for p in E.pilotes:
            if p.vivant and not p.elimine:
                d = math.hypot(p.x - self.x, p.z - self.z)
                if d < bd:
                    best, bd = p, d
        return best

    def avancer(self, dx, dz, dt):
        v = self.vitesse
        nx, nz = self.x + dx * v * dt, self.z + dz * v * dt
        ok = False
        if E.hits(nx, .5, self.z, self.r, self.h - .5) is None:
            self.x, ok = nx, True
        if E.hits(self.x, .5, nz, self.r, self.h - .5) is None:
            self.z, ok = nz, True
        return ok

    def update(self):
        if not E.partie.actif:
            return
        dt = time.dt
        nuit = E.partie.nuit
        self.anim += dt * (9 if nuit else 5)
        self.corps.y = 1.0 + math.sin(self.anim) * .04
        for i, b in enumerate(self.bras):
            b.rotation_x = math.sin(self.anim + i * 3) * (28 if self.atk > .5 else 10)
        self.flash -= dt
        if self.flash > 0:
            self.corps.color = color.white
        else:
            self.corps.color = self.base
        self.atk -= dt
        self.pense -= dt
        if self.pense <= 0:
            self.pense = random.uniform(.25, .45)
            self.cible = self.trouver_cible()
        c = self.cible
        if c is not None and (not c.vivant or c.elimine):
            c = self.cible = None
        if c is not None:
            d = Vec3(c.x - self.x, 0, c.z - self.z)
            dist = d.length()
            if dist > .01:
                dn = d * (1 / dist)
                self.rotation_y = math.degrees(math.atan2(dn.x, dn.z))
                if dist > 1.2:
                    self.avancer(dn.x, dn.z, dt)
            if dist < 1.7 and abs(c.y - self.y) < 2.2 and self.atk <= 0:
                self.atk = .7 if nuit else 1.0
                c.damage(self.degats, self)
        else:
            self.dest_t -= dt
            if self.dest is None or self.dest_t <= 0:
                a = random.uniform(0, 6.28)
                self.dest, self.dest_t = Vec3(math.sin(a), 0, math.cos(a)), random.uniform(2, 5)
            if self.avancer(self.dest.x, self.dest.z, dt * .5):
                self.rotation_y = math.degrees(math.atan2(self.dest.x, self.dest.z))
            else:
                self.dest = None

    # ---- dégâts -------------------------------------------------------------------------
    def damage(self, n, source=None, tete=False):
        if not self.vivant:
            return
        self.hp -= n
        self.flash = .08
        if self.hp <= 0:
            self.vivant = False
            if self in E.zombies:
                E.zombies.remove(self)
            E.boom(self.position + Vec3(0, 1, 0), 2.2, .25, color.red)
            E.partie.mort_zombie(self, source)
            destroy(self)
