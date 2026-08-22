"""
Construction du payload FNE (DGI) à partir d'un `Abonnement`. Cette
correspondance est spécifique au module Abonnements — le module `apps.fne`
lui-même ne connaît rien de ce mapping, il reçoit juste le dict déjà prêt.
"""

import re

from django.conf import settings

MODE_PAIEMENT_VERS_FNE = {
    'especes': 'cash',
    'mobile_money': 'mobile-money',
    'cheque': 'check',
}


def _email_client(client):
    """FNE exige un email par article — pour un client sans adresse
    renseignée, on en fabrique une factice à partir du téléphone plutôt que
    de bloquer la certification pour un champ non pertinent pour une salle
    de sport."""
    if client.email:
        return client.email
    telephone_normalise = re.sub(r'\D', '', client.telephone)
    return f"{telephone_normalise}@sansemail.magma.ci"


def construire_payload_vente(abonnement):
    """Payload conforme au contrat `POST /external/invoices/sign` de la FNE
    pour la vente d'un abonnement — un seul article, template B2C (clientèle
    particulière), pas de TVA distincte tant que le régime fiscal réel de
    l'établissement n'a pas été confirmé (voir `settings.FNE_TAXE_CODE`)."""
    client = abonnement.client
    return {
        'invoiceType': 'sale',
        'paymentMethod': MODE_PAIEMENT_VERS_FNE.get(abonnement.mode_paiement, 'cash'),
        'template': 'B2C',
        'isRne': False,
        'clientCompanyName': client.nom_complet,
        'clientPhone': client.telephone,
        'clientEmail': _email_client(client),
        'pointOfSale': settings.FNE_POINT_OF_SALE,
        'establishment': settings.FNE_ETABLISSEMENT,
        'foreignCurrency': '',
        'foreignCurrencyRate': 0,
        'items': [
            {
                'description': abonnement.type_abonnement.nom,
                'quantity': 1,
                'amount': abonnement.montant,
                'taxes': [settings.FNE_TAXE_CODE],
            },
        ],
    }
