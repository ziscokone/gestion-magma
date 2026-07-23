def format_fcfa(value):
    """Formate un montant en FCFA avec séparateur de milliers : 15000 -> '15 000 FCFA'.
    Utilisé à la fois par le filtre de template `fcfa` et par le code Python
    (messages d'erreur, __str__, PDF) pour ne pas dupliquer la logique."""
    if value is None or value == '':
        return value
    try:
        value = int(round(float(value)))
    except (TypeError, ValueError):
        return value
    formatted = f"{value:,}".replace(',', ' ')
    return f"{formatted} FCFA"


def format_duree(minutes):
    """Formate une durée en minutes de façon lisible : 90 -> '1h30', 60 -> '1h', 20 -> '20 min'."""
    if minutes is None or minutes == '':
        return minutes
    try:
        minutes = int(minutes)
    except (TypeError, ValueError):
        return minutes
    heures, reste = divmod(minutes, 60)
    if heures and reste:
        return f"{heures}h{reste:02d}"
    if heures:
        return f"{heures}h"
    return f"{reste} min"


_UNITES = ['', 'un', 'deux', 'trois', 'quatre', 'cinq', 'six', 'sept', 'huit', 'neuf']
_DIX_A_DIX_NEUF = ['dix', 'onze', 'douze', 'treize', 'quatorze', 'quinze', 'seize',
                   'dix-sept', 'dix-huit', 'dix-neuf']
_DIZAINES = ['', '', 'vingt', 'trente', 'quarante', 'cinquante', 'soixante', 'soixante',
             'quatre-vingt', 'quatre-vingt']


def _centaine_en_lettres(n, suivi_dun_mot=False):
    """Convertit un nombre de 0 à 999 en toutes lettres (sans le pluriel de mille/million).
    `suivi_dun_mot` : True si ce bloc est immédiatement suivi de « mille »/« million »/
    « milliard » — dans ce cas « cent » et « quatre-vingts » perdent leur 's'
    (« deux cent mille », pas « deux cents mille »)."""
    if n == 0:
        return ''

    mots = []
    centaine, reste = divmod(n, 100)
    if centaine:
        prefixe = f"{_UNITES[centaine]} " if centaine > 1 else ''
        pluriel_cent = centaine > 1 and reste == 0 and not suivi_dun_mot
        mots.append(f"{prefixe}cent" + ('s' if pluriel_cent else ''))

    if reste:
        if reste < 10:
            mots.append(_UNITES[reste])
        elif reste < 20:
            mots.append(_DIX_A_DIX_NEUF[reste - 10])
        else:
            dizaine, unite = divmod(reste, 10)
            base = _DIZAINES[dizaine]
            if dizaine in (7, 9):
                if unite == 0:
                    mots.append(f"{base}-dix")
                elif unite == 1 and dizaine == 7:
                    mots.append(f"{base} et onze")
                else:
                    mots.append(f"{base}-{_DIX_A_DIX_NEUF[unite]}")
            elif unite == 0:
                mots.append(base + ('s' if dizaine == 8 and not suivi_dun_mot else ''))
            elif unite == 1 and dizaine != 8:
                mots.append(f"{base} et un")
            else:
                mots.append(f"{base}-{_UNITES[unite]}")

    return ' '.join(mots)


def montant_en_lettres(valeur):
    """Convertit un montant FCFA en toutes lettres françaises : 25000 -> 'vingt-cinq mille francs CFA'.
    Utilisé sur les reçus PDF (mention légale « arrêté à la somme de »)."""
    try:
        n = int(round(float(valeur)))
    except (TypeError, ValueError):
        return ''

    if n == 0:
        return 'zéro franc CFA'

    negatif = n < 0
    n = abs(n)

    milliards, reste = divmod(n, 1_000_000_000)
    millions, reste = divmod(reste, 1_000_000)
    milliers, unites = divmod(reste, 1000)

    parties = []
    if milliards:
        parties.append(f"{_centaine_en_lettres(milliards, suivi_dun_mot=True)} milliard" + ('s' if milliards > 1 else ''))
    if millions:
        parties.append(f"{_centaine_en_lettres(millions, suivi_dun_mot=True)} million" + ('s' if millions > 1 else ''))
    if milliers:
        parties.append('mille' if milliers == 1 else f"{_centaine_en_lettres(milliers, suivi_dun_mot=True)} mille")
    if unites:
        parties.append(_centaine_en_lettres(unites))

    texte = ' '.join(parties)
    if negatif:
        texte = f"moins {texte}"
    return texte + (' franc CFA' if n == 1 else ' francs CFA')
