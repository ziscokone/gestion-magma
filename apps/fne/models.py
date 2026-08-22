from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models


class CertificationFNE(models.Model):
    """
    Journal de chaque tentative de certification d'une facture auprès de la
    FNE (DGI Côte d'Ivoire). Ne connaît rien du module appelant (Abonnement,
    Séance...) : la liaison se fait via une relation générique, pour que ce
    module reste réutilisable tel quel par n'importe quel autre modèle
    facturable, dans ce projet ou un autre.
    """
    STATUT_CHOICES = [
        ('succes', 'Certifié'),
        ('echec', 'Échec'),
        ('desactive', 'Non tenté (FNE désactivée)'),
    ]

    content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Type d'objet"
    )
    object_id = models.PositiveIntegerField(null=True, blank=True, verbose_name="Identifiant de l'objet")
    objet_lie = GenericForeignKey('content_type', 'object_id')

    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, verbose_name="Statut")
    payload_envoye = models.JSONField(verbose_name="Données envoyées")

    reference_fne = models.CharField(max_length=100, blank=True, verbose_name="Référence FNE")
    token_verification = models.URLField(
        max_length=500, blank=True,
        verbose_name="Lien de vérification", help_text="URL à encoder en QR code sur le document imprimé."
    )
    balance_sticker = models.IntegerField(null=True, blank=True, verbose_name="Solde de stickers restants")

    erreur_code = models.CharField(max_length=20, blank=True, verbose_name="Code d'erreur")
    erreur_message = models.TextField(blank=True, verbose_name="Message d'erreur")

    date_tentative = models.DateTimeField(auto_now_add=True, verbose_name="Date de la tentative")
    date_derniere_maj = models.DateTimeField(auto_now=True, verbose_name="Dernière mise à jour")

    class Meta:
        verbose_name = "Certification FNE"
        verbose_name_plural = "Certifications FNE"
        ordering = ['-date_tentative']

    def __str__(self):
        return f"{self.get_statut_display()} — {self.reference_fne or 'sans référence'} ({self.date_tentative:%d/%m/%Y %H:%M})"

    @property
    def peut_etre_relancee(self):
        return self.statut in ('echec', 'desactive')
