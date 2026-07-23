from datetime import date, timedelta

from django.db import models

from core.utils import format_fcfa
from apps.clients.models import Client


class TypeAbonnement(models.Model):
    """
    Types d'abonnement configurables (nom, prix, durée). Pré-rempli avec les 3
    types du cahier des charges, mais modifiable/extensible depuis l'interface
    si les tarifs ou durées changent — sans toucher au code.
    """
    cle = models.SlugField(max_length=50, unique=True, blank=True, null=True, verbose_name="Clé technique")
    nom = models.CharField(max_length=100, verbose_name="Nom")
    prix = models.PositiveIntegerField(verbose_name="Prix (FCFA)")
    duree_jours = models.PositiveIntegerField(default=30, verbose_name="Durée (jours)")
    ordre = models.PositiveSmallIntegerField(default=0, verbose_name="Ordre d'affichage")
    actif = models.BooleanField(default=True, verbose_name="Actif")

    class Meta:
        ordering = ['ordre', 'nom']
        verbose_name = "Type d'abonnement"
        verbose_name_plural = "Types d'abonnement"

    def __str__(self):
        return f"{self.nom} — {format_fcfa(self.prix)} ({self.duree_jours} j)"


class Abonnement(models.Model):
    """
    Souscription payée en une seule fois, en espèces, à la création — pas de
    paiement fractionné ni d'autre mode de paiement pour ce module.
    """

    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='abonnements', verbose_name="Client")
    type_abonnement = models.ForeignKey(
        TypeAbonnement, on_delete=models.PROTECT, related_name='abonnements', verbose_name="Type d'abonnement"
    )
    date_souscription = models.DateTimeField(auto_now_add=True, verbose_name="Date de souscription")
    date_debut = models.DateField(default=date.today, verbose_name="Date de début")
    date_fin = models.DateField(verbose_name="Date d'expiration")
    montant = models.PositiveIntegerField(verbose_name="Montant")
    enregistre_par = models.ForeignKey(
        'comptes.Utilisateur', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='abonnements_enregistres', verbose_name="Enregistré par"
    )
    relance_effectuee = models.BooleanField(default=False, verbose_name="Client contacté")
    date_relance = models.DateTimeField(null=True, blank=True, verbose_name="Date de la relance")

    class Meta:
        verbose_name = "Abonnement"
        verbose_name_plural = "Abonnements"
        ordering = ['-date_debut']

    def __str__(self):
        return f"{self.client.nom_complet} — {self.type_abonnement.nom} ({self.date_debut:%d/%m/%Y})"

    def save(self, *args, **kwargs):
        if not self.montant:
            self.montant = self.type_abonnement.prix
        if not self.date_fin:
            self.date_fin = self.date_debut + timedelta(days=self.type_abonnement.duree_jours)
        super().save(*args, **kwargs)

    @property
    def statut(self):
        return 'actif' if self.date_fin >= date.today() else 'expire'

    @property
    def jours_restants(self):
        return (self.date_fin - date.today()).days

    @property
    def expire_bientot(self):
        return self.statut == 'actif' and 0 <= self.jours_restants <= 7

    def expire_dans_les(self, jours):
        """Pour la page Relances : seuil configurable (7/14/30 jours...)."""
        return self.statut == 'actif' and 0 <= self.jours_restants <= jours

    @property
    def numero_recu(self):
        """Numéro de reçu façon facture : MAGMA-AAAA-MM-NNNNN, séquence qui
        repart à 1 chaque mois (calculé à la volée, pas stocké)."""
        d = self.date_souscription
        rang = Abonnement.objects.filter(
            date_souscription__year=d.year,
            date_souscription__month=d.month,
            pk__lte=self.pk,
        ).count()
        return f"MAGMA-{d.year}-{d.month:02d}-{rang:05d}"
