"""grenade.py - Grenade à fragmentation et fumigène (+ nuage de fumée)."""
from ursina import *
import etat as E


class Fumee(Entity):
    volatile = True

    def __init__(self, pos, rayon=6, duree=12):
        super().__init__(model='sphere', position=Vec3(pos.x, max(pos.y, .5), pos.z),
                         scale=rayon * 2, color=Color(.8, .8, .8, .78), double_sided=True)
        self.rayon, self.vie = rayon, duree
        E.fumees.append(self)

    def update(self):
        self.vie -= time.dt
        if self.vie <= 0:
            if self in E.fumees:
                E.fumees.remove(self)
            destroy(self)


class Grenade(Entity):
    volatile = True

    def __init__(self, owner, pos, vel, type='frag'):
        super().__init__(model='sphere', scale=.28, position=Vec3(pos.x, pos.y, pos.z),
                         color=color.dark_gray if type == 'frag' else color.light_gray)
        self.owner, self.v, self.type, self.fuse = owner, Vec3(vel.x, vel.y, vel.z), type, 2.4

    def update(self):
        if not E.partie.actif:
            return
        dt = time.dt
        self.fuse -= dt
        self.v.y -= 22 * dt
        p = self.position
        nx = p.x + self.v.x * dt
        if E.hits(nx, p.y - .12, p.z, .12, .24) is None:
            p.x = nx
        else:
            self.v.x *= -.4
        nz = p.z + self.v.z * dt
        if E.hits(p.x, p.y - .12, nz, .12, .24) is None:
            p.z = nz
        else:
            self.v.z *= -.4
        ny = p.y + self.v.y * dt
        top = E.hits(p.x, ny - .12, p.z, .12, .24)
        if ny <= .12 or (top is not None and self.v.y < 0):
            p.y = (top if top is not None else 0) + .12
            self.v.y = abs(self.v.y) * .35 if abs(self.v.y) > 2 else 0
            self.v.x *= .75
            self.v.z *= .75
        elif top is not None:
            self.v.y = 0
            p.y = ny
        else:
            p.y = ny
        self.position = p
        if self.fuse <= 0:
            self.detoner()

    def detoner(self):
        if self.type == 'frag':
            E.explode(self.position, 6, 110, self.owner)
        else:
            Fumee(self.position)
        destroy(self)
