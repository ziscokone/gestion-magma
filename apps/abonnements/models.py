from datetime import date, timedelta

from django.db import models
from django.db.models import Sum
from django.utils import timezone

from core.models import ModePaiementMixin
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
    Le paiement d'un abonnement peut être fractionné en plusieurs versements
    (voir `PaiementAbonnement`) : il n'y a donc pas de mode de paiement ou de
    statut de paiement figé ici, seulement le prix total dû. Le montant payé,
    le reste à payer et le statut (en attente / partiel / payé) se déduisent
    des versements liés.
    """
    STATUT_PAIEMENT_CHOICES = [
        ('en_attente', 'En attente'),
        ('partiel', 'Partiellement payé'),
        ('paye', 'Payé intégralement'),
    ]

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
    def montant_paye(self):
        return self.paiements.aggregate(total=Sum('montant'))['total'] or 0

    @property
    def montant_restant(self):
        return self.montant - self.montant_paye

    @property
    def statut_paiement(self):
        if self.montant_paye <= 0:
            return 'en_attente'
        if self.montant_paye >= self.montant:
            return 'paye'
        return 'partiel'

    @property
    def statut_paiement_display(self):
        return dict(self.STATUT_PAIEMENT_CHOICES)[self.statut_paiement]

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


class PaiementAbonnement(ModePaiementMixin, models.Model):
    """Un versement (paiement partiel ou total) sur un abonnement."""
    abonnement = models.ForeignKey(Abonnement, on_delete=models.CASCADE, related_name='paiements', verbose_name="Abonnement")
    montant = models.PositiveIntegerField(verbose_name="Montant versé")
    date = models.DateTimeField(default=timezone.now, verbose_name="Date du versement")
    enregistre_par = models.ForeignKey(
        'comptes.Utilisateur', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='paiements_abonnements_enregistres', verbose_name="Enregistré par"
    )

    class Meta:
        verbose_name = "Paiement d'abonnement"
        verbose_name_plural = "Paiements d'abonnement"
        ordering = ['date']

    def __str__(self):
        return f"{self.abonnement} — {format_fcfa(self.montant)} ({self.date:%d/%m/%Y})"

    @property
    def numero_recu(self):
        """Rattaché au numéro de reçu de l'abonnement : MAGMA-...-NNNNN-V{rang}."""
        rang = self.abonnement.paiements.filter(pk__lte=self.pk).count()
        return f"{self.abonnement.numero_recu}-V{rang}"
