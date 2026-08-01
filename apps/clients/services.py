"""Logique partagée entre la page « Répartition par zone » du module Clients
et le widget de synthèse du Tableau de bord — un seul calcul de la géométrie
du donut, pour ne jamais la dupliquer (ni ses bugs)."""
import math

from django.db.models import Count

from .models import Client, Quartier

PALETTE = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#e87ba4', '#008300']
COULEUR_AUTRES = '#4a3aa7'
COULEUR_SANS_ZONE = '#c3c2b7'


def repartition_clients_par_zone(max_parts=6, rayon=60, ecart_px=2):
    """Répartition des clients par quartier, avec la géométrie du donut SVG
    (stroke-dasharray/offset) déjà calculée pour le rayon demandé. Au-delà de
    `max_parts` quartiers peuplés, les plus petits sont regroupés dans une
    part « Autres »."""
    circonference = 2 * math.pi * rayon
    total_clients = Client.objects.count()
    zones = list(
        Quartier.objects.annotate(nb_clients=Count('clients'))
        .filter(nb_clients__gt=0)
        .order_by('-nb_clients', 'nom')  # tri secondaire par nom : classement stable en cas d'égalité
    )
    nb_sans_zone = Client.objects.filter(quartier__isnull=True).count()
    zone_dominante = zones[0] if zones else None

    for i, zone in enumerate(zones):
        zone.pourcentage = round(zone.nb_clients * 100 / total_clients, 1) if total_clients else 0
        zone.couleur = PALETTE[i] if i < max_parts else COULEUR_AUTRES

    # Parts du donut : les N plus grosses zones individuellement, le reste
    # regroupé, puis les clients sans quartier — toujours en dernier.
    parts = []
    for i, zone in enumerate(zones[:max_parts]):
        parts.append({'nom': zone.nom, 'nb_clients': zone.nb_clients, 'couleur': PALETTE[i]})

    reste = zones[max_parts:]
    if reste:
        parts.append({
            'nom': f"Autres ({len(reste)} quartier{'s' if len(reste) > 1 else ''})",
            'nb_clients': sum(z.nb_clients for z in reste),
            'couleur': COULEUR_AUTRES,
        })
    if nb_sans_zone:
        parts.append({'nom': 'Sans quartier renseigné', 'nb_clients': nb_sans_zone, 'couleur': COULEUR_SANS_ZONE})

    cumul_len = 0.0
    for i, part in enumerate(parts):
        part['pourcentage'] = round(part['nb_clients'] * 100 / total_clients, 1) if total_clients else 0
        longueur = circonference * part['nb_clients'] / total_clients if total_clients else 0
        # Chaînes déjà formatées (jamais des float) : un template Django en
        # locale fr affiche les décimales avec une virgule, ce qui casse la
        # syntaxe SVG (`stroke-dasharray="45,12 …"` devient deux nombres au
        # lieu d'un seul 45.12).
        part['dash_len'] = f"{max(longueur - ecart_px, 0):.2f}"
        part['dash_offset'] = f"{-cumul_len:.2f}"
        part['index'] = i
        cumul_len += longueur

    return {
        'zones': zones,
        'parts': parts,
        'reste': reste,
        'zone_dominante': zone_dominante,
        'total_clients': total_clients,
        'nb_sans_zone': nb_sans_zone,
        'rayon': rayon,
        'circonference': f"{circonference:.2f}",
    }
