"""clavier.py - Touches configurables (AZERTY + QWERTY gérés).
Modifie TOUCHES pour changer les contrôles : chaque action = tuple de touches."""
from ursina import held_keys

TOUCHES = {
    'avant':     ('z', 'w'),
    'arriere':   ('s',),
    'gauche':    ('q', 'a'),
    'droite':    ('d',),
    'sprint':    ('left shift',),
    'saut':      ('space',),
    'glisse':    ('left control', 'c'),
    'tir':       ('left mouse',),
    'viser':     ('right mouse',),
    'recharge':  ('r',),
    'titan':     ('f',),
    'interagir': ('e',),
    'tactique':  ('g',),
    'grappin':   ('x',),
    'arme1':     ('1',),
    'arme2':     ('2',),
}


def tenu(action):
    """True si une des touches de l'action est maintenue."""
    return any(held_keys[k] for k in TOUCHES[action])


def axe(plus, moins):
    """Retourne -1, 0 ou 1 selon les deux actions opposées."""
    return float(tenu(plus)) - float(tenu(moins))


def est(key, action):
    """True si l'évènement `key` (de input()) correspond à l'action."""
    if key.endswith(' down'):
        key = key[:-5]
    return key in TOUCHES[action]
