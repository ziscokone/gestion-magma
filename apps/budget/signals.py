"""
Génération automatique des opérations budgétaires à partir des autres
modules — jamais de ressaisie manuelle pour ces catégories, afin de garder
une seule source de vérité cohérente.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.clients.models import Seance
from apps.abonnements.models import PaiementAbonnement
from apps.stock.models import MouvementStock
from .models import OperationBudget


@receiver(post_save, sender=Seance)
def creer_recette_seance(sender, instance, **kwargs):
    if instance.statut_paiement != 'paye':
        return
    if OperationBudget.objects.filter(seance=instance).exists():
        return
    OperationBudget.objects.create(
        type_operation='entree',
        categorie='recette_seance',
        montant=instance.montant,
        mode_paiement=instance.mode_paiement,
        operateur_mobile_money=instance.operateur_mobile_money,
        seance=instance,
        enregistre_par=instance.enregistre_par,
    )


@receiver(post_save, sender=PaiementAbonnement)
def creer_recette_abonnement(sender, instance, created, **kwargs):
    if not created:
        return
    OperationBudget.objects.create(
        type_operation='entree',
        categorie='recette_abonnement',
        montant=instance.montant,
        mode_paiement=instance.mode_paiement,
        operateur_mobile_money=instance.operateur_mobile_money,
        paiement_abonnement=instance,
        enregistre_par=instance.enregistre_par,
    )


@receiver(post_save, sender=MouvementStock)
def creer_operation_stock(sender, instance, created, **kwargs):
    if not created:
        return
    if instance.type_mouvement == 'entree':
        OperationBudget.objects.create(
            type_operation='sortie',
            categorie='achat_produit',
            montant=instance.montant,
            mode_paiement=instance.mode_paiement,
            operateur_mobile_money=instance.operateur_mobile_money,
            mouvement_stock=instance,
            enregistre_par=instance.enregistre_par,
        )
    elif instance.type_mouvement == 'sortie' and instance.motif == 'vente' and not instance.vente_id:
        # Ventes rattachées à un panier (`vente_id` renseigné) : une seule
        # opération budgétaire est créée pour le panier entier, directement
        # dans la vue (voir apps/stock/views.py::VenteCreateView), pas ici.
        OperationBudget.objects.create(
            type_operation='entree',
            categorie='vente_produit',
            montant=instance.montant,
            mode_paiement=instance.mode_paiement,
            operateur_mobile_money=instance.operateur_mobile_money,
            mouvement_stock=instance,
            enregistre_par=instance.enregistre_par,
        )
