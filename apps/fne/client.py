"""
Client HTTP pour l'API de certification FNE (DGI Côte d'Ivoire).

Ne dépend d'aucun modèle métier de ce projet — uniquement de la config
(FNE_BASE_URL, FNE_API_KEY) et de la bibliothèque `requests`. C'est cette
indépendance qui permet de copier ce module tel quel dans un autre projet
Django (ex: une autre application de gestion) sans rien y adapter.
"""

import requests
from django.conf import settings

TIMEOUT_DEFAUT = 15


class FneAPIError(Exception):
    """Levée pour toute réponse d'erreur de l'API FNE (400/401/500...) ou en
    cas d'échec réseau (timeout, DNS, connexion refusée...)."""

    def __init__(self, message, status_code=None):
        self.status_code = status_code
        super().__init__(message)


def _headers():
    return {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': f'Bearer {settings.FNE_API_KEY}',
    }


def _appeler(methode, chemin, payload=None, timeout=TIMEOUT_DEFAUT):
    url = f"{settings.FNE_BASE_URL.rstrip('/')}{chemin}"
    try:
        reponse = requests.request(methode, url, json=payload, headers=_headers(), timeout=timeout)
    except requests.RequestException as exc:
        raise FneAPIError(f"Impossible de joindre la plateforme FNE : {exc}") from exc

    try:
        corps = reponse.json()
    except ValueError:
        corps = {}

    if not reponse.ok:
        message = corps.get('message', f"Erreur HTTP {reponse.status_code}")
        raise FneAPIError(message, status_code=reponse.status_code)

    return corps


def certifier_vente(payload, timeout=TIMEOUT_DEFAUT):
    """Certification d'une facture de vente ou d'un bordereau d'achat.
    POST {base_url}/external/invoices/sign"""
    return _appeler('POST', '/external/invoices/sign', payload, timeout)


def certifier_avoir(invoice_id, payload, timeout=TIMEOUT_DEFAUT):
    """Certification d'une facture d'avoir, liée à une facture déjà certifiée.
    POST {base_url}/external/invoices/{id}/refund"""
    return _appeler('POST', f'/external/invoices/{invoice_id}/refund', payload, timeout)
