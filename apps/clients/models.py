import uuid
from django.db import models
from django.utils import timezone

from core.models import PaiementMixin
from core.utils import format_fcfa


class Client(models.Model):
    SEXE_CHOICES = [
        ('M', 'Masculin'),
        ('F', 'Féminin'),
    ]

    OBJECTIF_CHOICES = [
        ('perte_poids', 'Perte de poids'),
        ('prise_masse', 'Prise de masse musculaire'),
        ('remise_forme', 'Remise en forme / Bien-être'),
        ('preparation_sportive', 'Préparation sportive'),
    ]

    public_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    telephone = models.CharField(max_length=20, unique=True, verbose_name="Téléphone")
    nom_complet = models.CharField(max_length=200, verbose_name="Nom complet")

    sexe = models.CharField(max_length=1, choices=SEXE_CHOICES, blank=True, verbose_name="Sexe")
    date_naissance = models.DateField(null=True, blank=True, verbose_name="Date de naissance")
    objectif = models.CharField(max_length=30, choices=OBJECTIF_CHOICES, blank=True, verbose_name="Objectif sportif")

    taille = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name="Taille (cm)")
    poids = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True, verbose_name="Poids (kg)")
    bassin = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name="Tour de bassin (cm)")

    contact_urgence_nom = models.CharField(max_length=200, blank=True, verbose_name="Contact d'urgence — Nom")
    contact_urgence_telephone = models.CharField(max_length=20, blank=True, verbose_name="Contact d'urgence — Téléphone")
    antecedents_medicaux = models.TextField(blank=True, verbose_name="Antécédents médicaux / contre-indications")
    photo_cni = models.ImageField(upload_to='clients/cni/', blank=True, null=True, verbose_name="Photo de la pièce d'identité (CNI)")

    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Client"
        verbose_name_plural = "Clients"
        ordering = ['nom_complet']

    def __str__(self):
        return f"{self.nom_complet} ({self.telephone})"

    @property
    def nombre_seances(self):
        return self.seances.count()

    @property
    def derniere_seance(self):
        return self.seances.order_by('-date').first()


class TypePrestation(models.Model):
    """
    Types de prestation configurables (nom + prix). Pré-rempli avec les 3 types
    du cahier des charges, mais modifiable/extensible depuis l'interface si les
    tarifs changent — sans toucher au code.
    """
    cle = models.SlugField(max_length=50, unique=True, blank=True, null=True, verbose_name="Clé technique")
    nom = models.CharField(max_length=100, verbose_name="Nom")
    prix = models.PositiveIntegerField(verbose_name="Prix (FCFA)")
    duree_minutes = models.PositiveIntegerField(default=30, verbose_name="Durée (minutes)")
    ordre = models.PositiveSmallIntegerField(default=0, verbose_name="Ordre d'affichage")
    actif = models.BooleanField(default=True, verbose_name="Actif")

    class Meta:
        ordering = ['ordre', 'nom']
        verbose_name = "Type de prestation"
        verbose_name_plural = "Types de prestation"

    def __str__(self):
        return f"{self.nom} — {format_fcfa(self.prix)}"


class Seance(PaiementMixin, models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='seances', verbose_name="Client")
    date = models.DateTimeField(default=timezone.now, verbose_name="Date")
    type_prestation = models.ForeignKey(
        TypePrestation, on_delete=models.PROTECT, related_name='seances', verbose_name="Type de prestation"
    )
    montant = models.PositiveIntegerField(verbose_name="Montant")
    enregistre_par = models.ForeignKey(
        'comptes.Utilisateur', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='seances_enregistrees', verbose_name="Enregistré par"
    )

    class Meta:
        verbose_name = "Séance"
        verbose_name_plural = "Séances"
        ordering = ['-date']

    def __str__(self):
        return f"{self.client.nom_complet} — {self.type_prestation.nom} ({self.date:%d/%m/%Y})"

    def save(self, *args, **kwargs):
        if not self.montant:
            self.montant = self.type_prestation.prix
        super().save(*args, **kwargs)
