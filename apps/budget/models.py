from django.db import models
from django.db.models import Sum
from django.urls import reverse
from django.utils import timezone

from core.models import ModePaiementMixin
from core.utils import format_fcfa


class CategorieCharge(models.Model):
    """Sous-catégories configurables pour les charges manuelles (Loyer, Électricité, Salaire...)."""
    nom = models.CharField(max_length=100, verbose_name="Nom")
    actif = models.BooleanField(default=True, verbose_name="Actif")

    class Meta:
        ordering = ['nom']
        verbose_name = "Catégorie de charge"
        verbose_name_plural = "Catégories de charge"

    def __str__(self):
        return self.nom


class OperationBudget(ModePaiementMixin, models.Model):
    """
    Journal des mouvements d'argent. Les catégories liées aux autres modules
    (recette séance/abonnement, achat/vente produit) sont générées
    automatiquement par des signaux (voir `apps/budget/signals.py`) — elles
    ne doivent jamais être ressaisies à la main, pour rester la seule source
    de vérité cohérente avec les séances/abonnements/stock. Seules les
    catégories charge/salaire/autre sont saisies manuellement.
    """
    TYPE_OPERATION_CHOICES = [
        ('entree', "Entrée d'argent"),
        ('sortie', "Sortie d'argent"),
    ]

    CATEGORIE_CHOICES = [
        ('recette_seance', 'Recette séance'),
        ('recette_abonnement', 'Recette abonnement'),
        ('achat_produit', 'Achat produit'),
        ('vente_produit', 'Vente produit'),
        ('charge', 'Charge'),
        ('salaire', 'Salaire'),
        ('autre', 'Autre'),
    ]

    CATEGORIES_MANUELLES = ('charge', 'salaire', 'autre')

    date = models.DateTimeField(default=timezone.now, verbose_name="Date de l'opération")
    type_operation = models.CharField(max_length=10, choices=TYPE_OPERATION_CHOICES, verbose_name="Type d'opération")
    categorie = models.CharField(max_length=30, choices=CATEGORIE_CHOICES, verbose_name="Catégorie")
    categorie_charge = models.ForeignKey(
        CategorieCharge, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='operations', verbose_name="Catégorie de charge"
    )
    montant = models.PositiveIntegerField(verbose_name="Montant")
    description = models.CharField(max_length=255, blank=True, verbose_name="Description")

    # Liens vers la source, uniquement renseignés pour les entrées automatiques
    seance = models.ForeignKey(
        'clients.Seance', on_delete=models.CASCADE, null=True, blank=True,
        related_name='operations_budget'
    )
    paiement_abonnement = models.ForeignKey(
        'abonnements.PaiementAbonnement', on_delete=models.CASCADE, null=True, blank=True,
        related_name='operations_budget'
    )
    mouvement_stock = models.ForeignKey(
        'stock.MouvementStock', on_delete=models.CASCADE, null=True, blank=True,
        related_name='operations_budget'
    )
    vente = models.ForeignKey(
        'stock.Vente', on_delete=models.CASCADE, null=True, blank=True,
        related_name='operations_budget'
    )

    enregistre_par = models.ForeignKey(
        'comptes.Utilisateur', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='operations_budget_enregistrees', verbose_name="Enregistré par"
    )

    class Meta:
        ordering = ['-date']
        verbose_name = "Opération budgétaire"
        verbose_name_plural = "Opérations budgétaires"

    def __str__(self):
        return f"{self.get_type_operation_display()} — {self.get_categorie_display()} ({format_fcfa(self.montant)})"

    @property
    def est_automatique(self):
        return bool(self.seance_id or self.paiement_abonnement_id or self.mouvement_stock_id or self.vente_id)

    @property
    def lien_source(self):
        if self.seance_id:
            return reverse('clients:client_detail', kwargs={'public_id': self.seance.client.public_id})
        if self.paiement_abonnement_id:
            return reverse('abonnements:abonnement_detail', kwargs={'pk': self.paiement_abonnement.abonnement_id})
        if self.vente_id:
            return reverse('stock:vente_confirmation', kwargs={'pk': self.vente_id})
        if self.mouvement_stock_id:
            return reverse('stock:produit_detail', kwargs={'pk': self.mouvement_stock.produit_id})
        return None

    @classmethod
    def solde_caisse(cls):
        from apps.etablissement.models import Etablissement
        etablissement = Etablissement.get_instance()
        solde_initial = etablissement.solde_initial_caisse if etablissement else 0
        entrees = cls.objects.filter(type_operation='entree').aggregate(total=Sum('montant'))['total'] or 0
        sorties = cls.objects.filter(type_operation='sortie').aggregate(total=Sum('montant'))['total'] or 0
        return solde_initial + entrees - sorties
