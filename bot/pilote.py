"""pilote.py - Base commune du joueur et des bots : PV, armure, points, classe,
armes, grenades, appel du Titan, ramassage du loot."""
import math
import random
from ursina import *
import etat as E
from classe import choix_classe as CC
from bot.allie import Titan
from armes.grenade import Grenade
from armes import fusil, smg, sniper, shotgun

FABRIQUES_ARMES = {'AR-15': fusil.creer, 'Kriss Vector': smg.creer,
                   'DRS-50': sniper.creer, 'Pompe': shotgun.creer}


class Pilote(Entity):
    def __init__(self, nom, couleur):
        super().__init__()
        self.nom, self.couleur = nom, couleur
        self.r, self.h = .4, 1.8
        self.vivant = self.elimine = self.attente = False
        self.score = self.score_final = self.kills = 0
        self.t_elim = -1
        self.hp = self.hp_max = 100
        self.armure = 0
        self.mode, self.titan, self.titan_cd, self.titan_hp = 'pilot', None, 0, 0
        self.invuln, self.since_hit, self.cool_tact = 0, 99, 0
        self.classe, self.armes, self.idx = None, [], 0
        self.tactique, self.nb_tactique, self.vitesse_mult = 'frag', 0, 1.0
        E.pilotes.append(self)

    @property
    def arme(self):
        return self.armes[self.idx]

    # ---- cycle de vie ------------------------------------------------------
    def nouvelle_partie(self, classe, pos):
        self.score = self.score_final = self.kills = 0
        self.elimine, self.t_elim = False, -1
        self.titan, self.titan_cd = None, 0
        CC.appliquer(self, classe)
        self.reapparaitre(pos)

    def reapparaitre(self, pos):
        CC.appliquer(self, self.classe)
        self.vivant, self.attente, self.mode = True, False, 'pilot'
        self.position = Vec3(pos.x, 0, pos.z)
        self.invuln, self.since_hit, self.cool_tact = 3, 99, 0
        self.enabled = True
        self.apres_respawn()

    def mourir(self):
        self.vivant = False
        self.avant_mort()

    # hooks surchargés par Player / PiloteIA
    def apres_respawn(self): pass
    def avant_mort(self): pass
    def sur_degats(self, source): pass
    def sur_changement_arme(self): pass

    # ---- dégâts ------------------------------------------------------------
    def damage(self, n, source=None, tete=False):
        if not self.vivant or self.elimine or self.invuln > 0 or not E.partie.actif:
            return
        self.since_hit = 0
        if self.armure > 0:
            a = min(self.armure, n * .6)
            self.armure -= a
            n -= a
        self.hp -= n
        self.sur_degats(source)
        if self.hp <= 0:
            E.partie.mort_pilote(self, source)

    def tick(self, dt):
        """Timers communs : invulnérabilité, régénération, armes, cooldowns."""
        self.invuln = max(0, self.invuln - dt)
        self.since_hit += dt
        self.cool_tact -= dt
        if self.titan_cd > 0:
            self.titan_cd -= dt
        if self.mode == 'pilot' and self.since_hit > 4 and self.hp < self.hp_max:
            self.hp = min(self.hp_max, self.hp + 6 * dt)
        for a in self.armes:
            a.update(dt)

    # ---- équipement --------------------------------------------------------
    def choisir_arme(self, i):
        if 0 <= i < len(self.armes) and i != self.idx:
            self.idx = i
            self.sur_changement_arme()

    def lancer_tactique(self, origin, vitesse):
        if self.nb_tactique <= 0 or self.cool_tact > 0:
            return False
        self.nb_tactique -= 1
        self.cool_tact = 1.0
        Grenade(self, origin, vitesse, self.tactique)
        return True

    def titan_actif(self):
        return self.titan is not None and self.titan.vivant

    def appeler_titan(self):
        """Coûte 10 points. Le Titan tombe du ciel devant le pilote."""
        joueur = self is E.joueur
        if self.mode == 'titan' or self.titan_actif():
            return False
        if self.titan_cd > 0:
            if joueur:
                E.msg(f'Titan pret dans {math.ceil(self.titan_cd)}s')
            return False
        if self.score < E.COUT_TITAN:
            if joueur:
                E.msg(f'Il faut {E.COUT_TITAN} points pour appeler un Titan')
            return False
        base = E.norm(Vec3(self.forward.x, 0, self.forward.z))
        # devant soi d'abord, puis en tournant (évite les murs / bords de map)
        for ang in (0, 35, -35, 70, -70, 110, -110, 180):
            a = math.radians(ang)
            fw = Vec3(base.x * math.cos(a) + base.z * math.sin(a), 0,
                      -base.x * math.sin(a) + base.z * math.cos(a))
            for d in range(14, 60, 4):
                spot = self.position + fw * d
                if abs(spot.x) < E.DEMI_MAP - 6 and abs(spot.z) < E.DEMI_MAP - 6 \
                        and E.hits(spot.x, 0, spot.z, 3.5, 6) is None:
                    self.score -= E.COUT_TITAN
                    self.titan = Titan(self, spot)
                    if joueur:
                        E.msg(f'TITANFALL ! (-{E.COUT_TITAN} pts)')
                    return True
        return False

    def ramasser(self, loot):
        t, texte = loot.type, None
        if t == 'soin':
            if self.hp >= self.hp_max - 1:
                return False
            self.hp = min(self.hp_max, self.hp + 45)
            texte = 'Medikit +45 PV'
        elif t == 'armure':
            if self.armure >= 50:
                return False
            self.armure, texte = 50, 'Armure +50'
        elif t == 'munitions':
            for a in self.armes:
                a.ajouter_munitions(a.chargeur * 2)
            texte = 'Munitions'
        elif t == 'grenade':
            if self.nb_tactique >= 4:
                return False
            self.nb_tactique += 1
            texte = f'+1 {self.tactique}'
        elif t == 'arme':
            n = random.choice([k for k in FABRIQUES_ARMES if k != self.armes[0].nom])
            self.armes[0] = FABRIQUES_ARMES[n]()
            texte = f'Arme : {n}'
            self.sur_changement_arme()
        if self is E.joueur and texte:
            E.msg(texte)
        return True
