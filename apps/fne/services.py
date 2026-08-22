"""
Point d'entrée public du module FNE. C'est la seule chose que les autres
apps (Abonnement, ou une future app de facturation) doivent connaître :
elles construisent un payload conforme au contrat de l'API FNE, et appellent
`certifier_facture`. Tout le reste (auth, appel HTTP, journalisation) est
géré ici.

Une panne ou une indisponibilité de la plateforme FNE ne doit jamais
empêcher l'enregistrement d'une vente côté application : la certification
est toujours "best effort" et journalisée, jamais bloquante.
"""

from django.conf import settings
from django.contrib.contenttypes.models import ContentType

from .client import FneAPIError, certifier_vente
from .models import CertificationFNE


def _kwargs_objet_lie(objet_lie):
    if objet_lie is None:
        return {}
    return {
        'content_type': ContentType.objects.get_for_model(objet_lie),
        'object_id': objet_lie.pk,
    }


def certifier_facture(payload, objet_lie=None):
    """
    Tente de certifier `payload` (dict conforme au contrat FNE) auprès de la
    DGI et enregistre le résultat dans le journal. `objet_lie` est l'instance
    (Abonnement, Séance...) à laquelle rattacher la tentative — optionnel.

    Retourne toujours une instance de `CertificationFNE` (jamais d'exception
    remontée à l'appelant).
    """
    if not settings.FNE_ACTIF:
        return CertificationFNE.objects.create(
            statut='desactive',
            payload_envoye=payload,
            **_kwargs_objet_lie(objet_lie),
        )

    try:
        reponse = certifier_vente(payload)
    except FneAPIError as exc:
        return CertificationFNE.objects.create(
            statut='echec',
            payload_envoye=payload,
            erreur_code=str(exc.status_code or ''),
            erreur_message=str(exc),
            **_kwargs_objet_lie(objet_lie),
        )

    return CertificationFNE.objects.create(
        statut='succes',
        payload_envoye=payload,
        reference_fne=reponse.get('reference', ''),
        token_verification=reponse.get('token', ''),
        balance_sticker=reponse.get('balance_sticker'),
        **_kwargs_objet_lie(objet_lie),
    )


def derniere_certification(objet):
    """Dernière tentative de certification connue pour `objet` (Abonnement,
    Séance...), ou None si aucune n'a encore été faite. Point de lecture
    générique utilisé par les autres apps pour savoir si un document peut
    afficher le vrai sticker FNE ou doit rester sur la mention de repli."""
    return CertificationFNE.objects.filter(
        content_type=ContentType.objects.get_for_model(objet),
        object_id=objet.pk,
    ).order_by('-date_tentative').first()


def relancer_certification(certification):
    """Relance une tentative en échec (ou jamais tentée car FNE désactivée)
    avec le même payload que la première fois, en conservant l'objet lié."""
    objet_lie = certification.objet_lie
    return certifier_facture(certification.payload_envoye, objet_lie=objet_lie)
