from django.db import models


class ModePaiementMixin(models.Model):
    """
    Mode de paiement d'une transaction unitaire (une séance, un versement
    d'abonnement...) : espèces / Mobile Money (avec opérateur + couleur de
    badge) / autre. Ne porte pas de statut — une transaction enregistrée est
    par définition reçue ; le statut global (payé/partiel/en attente) se
    calcule au niveau de l'objet parent (ex: Abonnement) à partir de la somme
    de ses transactions.
    """

    MODE_PAIEMENT_CHOICES = [
        ('especes', 'Espèces'),
        ('mobile_money', 'Mobile Money'),
        ('autre', 'Autre'),
    ]

    OPERATEUR_MOBILE_MONEY_CHOICES = [
        ('wave', 'Wave'),
        ('mtn', 'MTN'),
        ('moov', 'Moov'),
        ('orange', 'Orange'),
    ]

    OPERATEUR_COULEURS = {
        'wave': '#00CED1',
        'orange': '#FF6600',
        'mtn': '#FFCC00',
        'moov': '#003366',
    }

    mode_paiement = models.CharField(max_length=20, choices=MODE_PAIEMENT_CHOICES, default='especes', verbose_name="Mode de paiement")
    operateur_mobile_money = models.CharField(
        max_length=20, choices=OPERATEUR_MOBILE_MONEY_CHOICES, blank=True, verbose_name="Opérateur Mobile Money"
    )

    class Meta:
        abstract = True

    @property
    def operateur_couleur(self):
        return self.OPERATEUR_COULEURS.get(self.operateur_mobile_money, '#6c757d')

    @property
    def mode_paiement_affiche(self):
        if self.mode_paiement == 'mobile_money' and self.operateur_mobile_money:
            return f"Mobile Money ({self.get_operateur_mobile_money_display()})"
        return self.get_mode_paiement_display()


class PaiementMixin(ModePaiementMixin):
    """
    Pour une transaction payée en une seule fois (ex: une séance) : mode de
    paiement + statut binaire payé/en attente. Pour un paiement pouvant être
    fractionné en plusieurs versements (ex: un abonnement), utiliser
    `ModePaiementMixin` directement sur le modèle de versement et calculer le
    statut global à partir de la somme des versements plutôt que d'hériter
    de ce mixin.
    """

    STATUT_PAIEMENT_CHOICES = [
        ('paye', 'Payé'),
        ('en_attente', 'En attente'),
    ]

    statut_paiement = models.CharField(max_length=20, choices=STATUT_PAIEMENT_CHOICES, default='en_attente', verbose_name="Statut du paiement")

    class Meta:
        abstract = True
