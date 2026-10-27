"""partie.py - Règles du match : chrono 10 min, jour/nuit, points, mort définitive
ou respawn à 50 points, fin de partie, zombies qui réapparaissent."""
import colorsys
import math
import random
from ursina import *
import etat as E
from classe import choix_classe as CC
from bot.pilote import Pilote
from bot.zombie import Zombie
from map.loot import Loot, reset_loots


def _hsv(h, s, v):
    return colorsys.hsv_to_rgb(h / 360, s, v)


def _mix(a, b, k):
    return tuple(a[i] + (b[i] - a[i]) * k for i in range(3))


CIEL_JOUR, CIEL_NUIT = (1, 1, 1), (.10, .12, .28)
BRUME_JOUR, BRUME_NUIT = _hsv(215, .25, .85), (.03, .04, .09)


class Partie(Entity):
    def __init__(self, ciel):
        super().__init__()
        self.ciel = ciel
        self.en_cours = self.fini = self.nuit = False
        self.t, self.taches, self.t_detect = 0.0, [], None
        self.resultat, self.k_prev = '', -1

    @property
    def actif(self):
        return self.en_cours and not self.fini

    # ---- planification -------------------------------------------------------
    def plus_tard(self, delai, fn):
        self.taches.append([self.t + delai, fn])

    # ---- menu / démarrage ---------------------------------------------------------
    def ouvrir_menu(self):
        self.en_cours = self.fini = False
        E.menu.enabled = True
        mouse.locked = False
        mouse.visible = True
        E.hud.banniere('')

    def demarrer(self, classe):
        for e in list(scene.entities):
            if getattr(e, 'volatile', False):
                destroy(e)
        E.zombies.clear()
        E.titans.clear()
        E.fumees.clear()
        self.taches, self.t, self.t_detect = [], 0.0, None
        self.nuit, self.fini, self.resultat, self.k_prev = False, False, '', -1
        reset_loots()
        self.en_cours = True
        spawns = E.spawns[:]
        random.shuffle(spawns)
        for i, p in enumerate(E.pilotes):
            p.nouvelle_partie(classe if p is E.joueur else CC.aleatoire(), spawns[i % len(spawns)])
        for _ in range(E.NB_ZOMBIES):
            self.spawn_zombie()
        E.menu.enabled = False
        mouse.locked = True
        E.hud.banniere('SURVIS 10 MINUTES', 3)
        E.msg('Tue des zombies (+1), vole les points des pilotes')

    # ---- zombies -----------------------------------------------------------------------
    def spawn_zombie(self):
        vivants = [p for p in E.pilotes if p.vivant]
        Zombie(E.point_libre(.6, vivants, 30))

    def mort_zombie(self, z, source=None):
        k = E.proprietaire(source)
        if isinstance(k, Pilote):
            k.score += 1
            k.kills += 1
        if self.actif:
            self.plus_tard(E.DELAI_RESPAWN_ZOMBIE, self.spawn_zombie)
            if random.random() < .12:
                Loot(z.position, None, True)

    # ---- pilotes -------------------------------------------------------------------------
    def mort_pilote(self, v, source=None):
        if not v.vivant or v.elimine:
            return
        k = E.proprietaire(source)
        if not isinstance(k, Pilote) or k is v:
            k = None
        v.score_final = v.score
        v.mourir()
        Loot(v.position, random.choice(('soin', 'munitions', 'arme')), True)
        qui = k.nom if k else 'les zombies'
        if v.score >= E.COUT_RESPAWN:
            # 50 points payés : pas de mort définitive. Le tueur prend le reste.
            v.score -= E.COUT_RESPAWN
            if k:
                k.score += v.score
                k.kills += 1
            v.score, v.attente = 0, True
            E.msg(f'{v.nom} tue par {qui} (-{E.COUT_RESPAWN} pts, respawn)')
            self.plus_tard(3, lambda v=v: self.reapparaitre(v))
        else:
            v.elimine, v.t_elim = True, self.t
            if k:
                k.score += v.score
                k.kills += 1
            v.score = 0
            E.msg(f'{v.nom} ELIMINE par {qui}')
            if v.titan_actif():
                v.titan.detruire(False)
            if v is E.joueur:
                E.hud.banniere('ELIMINE', 4)

    def reapparaitre(self, v):
        if not self.actif or v.elimine:
            return
        v.reapparaitre(E.spawn_loin())

    # ---- fin de partie ----------------------------------------------------------------------
    def verifier_fin(self):
        restants = [p for p in E.pilotes if not p.elimine]
        if len(restants) <= 1:
            if self.t_detect is None:
                self.t_detect = self.t
            elif self.t - self.t_detect >= .5:
                if restants:
                    self.finir(restants[0], 'Dernier survivant')
                else:
                    # les deux derniers sont morts en même temps : le plus de points gagne
                    cands = [p for p in E.pilotes if p.t_elim >= self.t_detect - .1] or E.pilotes
                    self.finir(max(cands, key=lambda p: p.score_final), 'Mort simultanee : plus de points')
        elif self.t >= E.DUREE_PARTIE:
            self.finir(max(restants, key=lambda p: p.score), 'Temps ecoule : plus de points')

    def finir(self, gagnant, raison):
        self.fini = True
        mouse.locked = False
        mouse.visible = True
        if gagnant is E.joueur:
            self.resultat = f'VICTOIRE !  ({raison})'
        else:
            self.resultat = f'{gagnant.nom} GAGNE  ({raison})'
        E.hud.banniere('FIN DE PARTIE', 5)

    # ---- entrées -----------------------------------------------------------------------------------
    def input(self, key):
        if key == 'escape':
            application.quit()
        if key == 'r' and self.en_cours and (self.fini or E.joueur.elimine):
            self.ouvrir_menu()

    # ---- boucle -----------------------------------------------------------------------------------------
    def update(self):
        if not self.en_cours:
            return
        if not self.fini:
            dt = time.dt
            self.t += dt
            for tache in [x for x in self.taches if x[0] <= self.t]:
                self.taches.remove(tache)
                tache[1]()
            if not self.nuit and self.t >= E.DUREE_JOUR:
                self.nuit = True
                for z in E.zombies:
                    z.passer_nuit()
                E.hud.banniere('LA NUIT TOMBE', 4)
                E.msg('Les zombies sont plus forts et plus rapides !')
            self.verifier_fin()
        # ciel / brume / obscurité : transition de 20 s après 5 min
        k = max(0.0, min(1.0, (self.t - E.DUREE_JOUR) / 20))
        if abs(k - self.k_prev) > .002:
            self.k_prev = k
            self.ciel.color = Color(*_mix(CIEL_JOUR, CIEL_NUIT, k), 1)
            scene.fog_color = Color(*_mix(BRUME_JOUR, BRUME_NUIT, k), 1)
            E.hud.nuit.color = Color(0, 0, .06, .42 * k)
