"""ennemie.py - Pilotes IA rivaux (les 4 autres joueurs de la partie).
Ils chassent les zombies et les pilotes, ramassent le loot, lancent des grenades
et appellent un Titan (qui combat en mode auto pour eux)."""
import math
import random
from ursina import *
import etat as E
from bot.pilote import Pilote


class PiloteIA(Pilote):
    def __init__(self, nom, col):
        super().__init__(nom, col)
        self.parts = []

        def cube(**kw):
            e = Entity(parent=self, model='cube', **kw)
            self.parts.append((e, e.color))
            return e

        self.torse = cube(color=col, scale=(.7, .9, .4), y=1.15)
        cube(color=color.hsv(0, 0, .2), scale=(.6, .7, .35), y=.35)
        cube(color=color.hsv(25, .4, .8), scale=(.38, .38, .38), y=1.8)
        cube(color=color.hsv(0, 0, .12), scale=(.1, .12, .75), position=(.35, 1.25, .5))
        self.col = col
        self.cible, self.vu, self.dest = None, False, None
        self.pense, self.flash, self.react = 0, 0, 0
        self.strafe, self.strafe_t, self.bloque, self.regen_mun = 1, 0, 0, 0
        self.enabled = False

    # ---- hooks -------------------------------------------------------------
    def apres_respawn(self):
        self.cible, self.dest, self.bloque = None, None, 0

    def avant_mort(self):
        self.enabled = False

    def sur_degats(self, source):
        self.flash = .08
        # riposte : cibler l'agresseur s'il est un pilote
        p = E.proprietaire(source)
        if isinstance(p, Pilote) and p is not self and p.vivant:
            self.cible, self.react = p, .3

    # ---- perception ------------------------------------------------------------
    def oeil(self):
        return self.position + Vec3(0, 1.6, 0)

    def penser(self):
        oeil = self.oeil()
        cands = []
        for c in E.toutes_cibles():
            if c is self or c is self.titan:
                continue
            d = math.hypot(c.x - self.x, c.z - self.z)
            if getattr(c, 'est_zombie', False):
                lim, w = 26, 1.0
            elif getattr(c, 'est_titan', False):
                lim, w = 55, 1.3
            else:
                lim, w = 65, .6
            if d < lim:
                cands.append((d * w, c))
        cands.sort(key=lambda t: t[0])
        self.cible, self.vu = None, False
        for _, c in cands[:3]:
            if E.visible(oeil, Vec3(c.x, c.y + c.h * .6, c.z)):
                if self.cible is not c and self.react <= 0:
                    self.react = random.uniform(.25, .6)
                self.cible, self.vu = c, True
                break

        if self.cible is None:
            self.choisir_destination()
        else:
            self.actions_combat()

    def choisir_destination(self):
        if self.dest is not None and self.bloque < 1.2:
            return
        self.bloque = 0
        besoin = None
        if self.hp < self.hp_max * .55:
            besoin = 'soin'
        elif self.arme.reserve is not None and self.arme.reserve + self.arme.munitions < self.arme.chargeur:
            besoin = 'munitions'
        best, bd = None, 120 if besoin else 55
        for l in E.loots:
            if l.actif and l.y < 2 and (besoin is None or l.type == besoin):
                d = math.hypot(l.x - self.x, l.z - self.z)
                if d < bd:
                    best, bd = l, d
        if best is not None and (besoin or random.random() < .6):
            self.dest = Vec3(best.x, 0, best.z)
        else:
            self.dest = E.point_libre(1.0)

    def actions_combat(self):
        c = self.cible
        dist = math.hypot(c.x - self.x, c.z - self.z)
        est_pilote = isinstance(c, Pilote)
        if est_pilote and dist < 55 and self.score >= E.COUT_TITAN \
                and not self.titan_actif() and self.titan_cd <= 0 and random.random() < .35:
            self.appeler_titan()
        if self.nb_tactique > 0 and 8 < dist < 28 and random.random() < .15:
            d = Vec3(c.x - self.x, 0, c.z - self.z)
            dn = E.norm(d)
            v = min(26, dist * 1.6)
            self.lancer_tactique(self.oeil(), dn * v + Vec3(0, 6, 0))

    # ---- mouvement ---------------------------------------------------------------
    def bouger(self, dt):
        c = self.cible
        mv, face = Vec3(0, 0, 0), None
        if c is not None:
            d = Vec3(c.x - self.x, 0, c.z - self.z)
            dist = d.length()
            if dist > .01:
                dn = d * (1 / dist)
                face = dn
                pref = self.arme.pref
                fwd = 1 if dist > pref * 1.25 else (-.7 if dist < pref * .55 else 0)
                mv = dn * fwd + Vec3(dn.z, 0, -dn.x) * self.strafe * .7
        elif self.dest is not None:
            d = Vec3(self.dest.x - self.x, 0, self.dest.z - self.z)
            dist = d.length()
            if dist < 1.5:
                self.dest = None
            else:
                mv = face = d * (1 / dist)
        if mv.length() > 0:
            sp = 6.5 * self.vitesse_mult
            nx, nz = self.x + mv.x * sp * dt, self.z + mv.z * sp * dt
            moved = False
            if E.hits(nx, .5, self.z, self.r, self.h - .5) is None:
                self.x, moved = nx, True
            if E.hits(self.x, .5, nz, self.r, self.h - .5) is None:
                self.z, moved = nz, True
            self.bloque = 0 if moved else self.bloque + dt
            if self.bloque > 1.2:
                self.dest, self.strafe = None, -self.strafe
        if face is not None:
            self.rotation_y = math.degrees(math.atan2(face.x, face.z))

    # ---- tir ---------------------------------------------------------------------------
    def tirer_sur_cible(self, dt):
        a = self.arme
        if a.munitions <= 0 and (a.reserve is None or a.reserve <= 0) and len(self.armes) > 1:
            self.idx = 1 - self.idx
            return
        if a.munitions <= 0:
            a.recharger()
        c = self.cible
        if c is None or not self.vu or self.react > 0:
            return
        oeil = self.oeil()
        cp = Vec3(c.x, c.y + c.h * .6, c.z)
        dist = distance(oeil, cp)
        if dist > a.portee * .85 or not a.pret() or a.munitions <= 0:
            return
        err = .03 + dist * .0012
        jit = Vec3(random.uniform(-1, 1), random.uniform(-.6, .6), random.uniform(-1, 1)) * dist * err
        fw = E.norm(Vec3(cp.x - oeil.x, 0, cp.z - oeil.z))
        a.tirer(self, oeil, cp - oeil + jit, debut=oeil + fw * .6)

    # ---- boucle -----------------------------------------------------------------------------
    def update(self):
        P = E.partie
        if not P.actif or not self.vivant:
            return
        dt = time.dt
        self.tick(dt)
        self.react -= dt
        self.flash -= dt
        self.torse.color = color.white if self.flash > 0 else self.col
        self.strafe_t -= dt
        if self.strafe_t <= 0:
            self.strafe_t, self.strafe = random.uniform(1.2, 2.5), random.choice((-1, 1))
        self.regen_mun += dt
        if self.regen_mun > 25:
            self.regen_mun = 0
            for a in self.armes:
                a.ajouter_munitions(a.chargeur)
        self.pense -= dt
        if self.pense <= 0:
            self.pense = random.uniform(.3, .5)
            self.penser()
        if self.cible is not None and not getattr(self.cible, 'vivant', False):
            self.cible, self.vu = None, False
        self.bouger(dt)
        self.tirer_sur_cible(dt)
