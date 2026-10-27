"""hud.py - Interface : chrono, jour/nuit, scores, PV, munitions, Titan, messages."""
from ursina import *
import etat as E


class HUD(Entity):
    def __init__(self):
        super().__init__()
        self.nuit = Entity(parent=camera.ui, model='quad', scale=(4, 2), z=2, color=Color(0, 0, .06, 0))
        self.hurt = Entity(parent=camera.ui, model='quad', scale=(4, 2), z=2, color=Color(1, 0, 0, 0))
        self.cross = Entity(parent=camera.ui, model='quad', scale=.008)
        self.t_timer = Text('', origin=(0, 0), position=(0, .46), scale=2)
        self.t_phase = Text('', origin=(0, 0), position=(0, .41), scale=1.1)
        self.t_score = Text('', position=(-.88, .47), scale=1.1)
        self.t_feed = Text('', origin=(.5, .5), position=(.88, .47), scale=1.0, color=color.yellow)
        self.t_titan = Text('', origin=(0, 0), position=(0, .35), scale=1.2, color=color.orange)
        self.t_hp = Text('', position=(-.88, -.40), scale=1.6, color=color.lime)
        self.t_ammo = Text('', origin=(.5, .5), position=(.88, -.38), scale=1.6)
        self.t_info = Text('', origin=(.5, .5), position=(.88, -.44), scale=1.0, color=color.light_gray)
        self.banner = Text('', origin=(0, 0), y=.27, scale=2.6, color=color.orange)
        self.t_etat = Text('', origin=(0, 0), y=.12, scale=2, color=color.white)
        Text('ZQSD bouger | Espace saut/grimper | Shift sprint | Ctrl glisser | X grappin | G grenade | '
             'F Titan | E embarquer',
             origin=(0, 0), y=-.485, scale=.7, color=color.gray)
        self.hurt_a, self.hitm, self.ban_t, self.acc = 0, 0, 0, 0
        self.feed, self.ancien = [], ''

    # ---- évènements ------------------------------------------------------------
    def degats(self):
        self.hurt_a = .4

    def touche(self, tete=False):
        self.hitm = .12 if not tete else .25

    def msg(self, texte, ttl=5):
        self.feed.append([texte, ttl])
        self.feed = self.feed[-6:]

    def banniere(self, texte, duree=3):
        self.banner.text, self.ban_t = texte, duree

    # ---- boucle --------------------------------------------------------------------
    def update(self):
        dt = time.dt
        self.hurt_a = max(0, self.hurt_a - dt * .8)
        self.hurt.color = Color(1, 0, 0, self.hurt_a)
        self.hitm -= dt
        self.cross.color = color.red if self.hitm > 0 else color.white
        j = E.joueur
        self.cross.scale = .004 if (j is not None and j.zoom) else .008
        if self.ban_t > 0:
            self.ban_t -= dt
            if self.ban_t <= 0:
                self.banner.text = ''
        for m in self.feed:
            m[1] -= dt
        self.feed = [m for m in self.feed if m[1] > 0]
        self.acc += dt
        if self.acc < .1:
            return
        self.acc = 0
        self.rafraichir()

    def rafraichir(self):
        P, p = E.partie, E.joueur
        if P is None or p is None:
            return
        self.t_feed.text = '\n'.join(m[0] for m in self.feed)
        if not P.en_cours:
            for t in (self.t_timer, self.t_phase, self.t_score, self.t_titan, self.t_hp, self.t_ammo,
                      self.t_info, self.t_etat):
                t.text = ''
            return
        reste = max(0, E.DUREE_PARTIE - P.t)
        self.t_timer.text = f'{int(reste // 60):02d}:{int(reste % 60):02d}'
        self.t_phase.text = 'NUIT - zombies enrages' if P.nuit else \
            f'JOUR - la nuit tombe dans {int(max(0, E.DUREE_JOUR - P.t))}s'
        lignes = []
        for q in sorted(E.pilotes, key=lambda q: -q.score):
            etat = 'ELIM' if q.elimine else ('...' if not q.vivant else '')
            lignes.append(f"{'> ' if q is p else '  '}{q.nom}  {int(q.score)} pts  {etat}")
        self.t_score.text = '\n'.join(lignes) + f'\nZombies : {len(E.zombies)}'

        if p.elimine and not P.fini:
            self.t_etat.text = 'ELIMINE - spectateur\n[R] relancer une partie'
        elif P.fini:
            self.t_etat.text = P.resultat + '\n[R] rejouer'
        elif not p.vivant:
            self.t_etat.text = f'MORT - reapparition... (-{E.COUT_RESPAWN} pts)'
        else:
            self.t_etat.text = ''

        a = p.arme_active() if p.armes else None
        if p.mode == 'titan':
            self.t_titan.text = '[E] EJECTION'
            self.t_hp.text = f'TITAN {int(p.titan_hp)}'
        else:
            t = p.titan
            if t is None or not t.vivant:
                if p.titan_cd > 0:
                    self.t_titan.text = f'TITAN PRET DANS {int(p.titan_cd) + 1}s'
                elif p.score >= E.COUT_TITAN:
                    self.t_titan.text = f'[F] APPELER LE TITAN (-{E.COUT_TITAN} pts)'
                else:
                    self.t_titan.text = f'TITAN : {E.COUT_TITAN} pts requis'
            elif t.state == 'falling':
                self.t_titan.text = 'TITANFALL EN COURS...'
            elif distance(p.position, t.position) < 8:
                self.t_titan.text = '[E] EMBARQUER'
            else:
                self.t_titan.text = 'TON TITAN T\'ATTEND'
            self.t_hp.text = f'PV {int(p.hp)}   ARM {int(p.armure)}'
        if a is not None:
            if a.rech > 0:
                self.t_ammo.text = f'{a.nom}  RECHARGEMENT...'
            elif a.reserve is None:
                self.t_ammo.text = a.nom
            else:
                self.t_ammo.text = f'{a.nom}  {a.munitions} / {a.reserve}'
        self.t_info.text = f'{p.nb_tactique}x {p.tactique}' if p.mode == 'pilot' else ''
