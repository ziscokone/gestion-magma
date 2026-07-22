from django.db import models


class Etablissement(models.Model):
    """
    Modèle représentant la salle de sport (nom, logo, coordonnées).
    Une seule instance de ce modèle devrait exister (singleton).
    """
    nom = models.CharField(max_length=200, verbose_name="Nom de l'établissement", default="MAGMA")
    logo = models.ImageField(upload_to='logos/', blank=True, null=True, verbose_name="Logo")
    slogan = models.CharField(max_length=200, blank=True, verbose_name="Slogan")
    adresse = models.TextField(blank=True, verbose_name="Adresse")
    telephone = models.CharField(max_length=20, blank=True, verbose_name="Téléphone")
    email = models.EmailField(blank=True, verbose_name="Email")
    solde_initial_caisse = models.PositiveIntegerField(
        default=0, verbose_name="Solde de caisse initial (FCFA)",
        help_text="Montant déjà en caisse au moment où vous commencez à utiliser le logiciel."
    )

    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Établissement"
        verbose_name_plural = "Établissement"

    def __str__(self):
        return self.nom

    def save(self, *args, **kwargs):
        """Assure qu'il n'y a qu'une seule instance d'Etablissement."""
        if not self.pk and Etablissement.objects.exists():
            existing = Etablissement.objects.first()
            self.pk = existing.pk
        super().save(*args, **kwargs)

    @classmethod
    def get_instance(cls):
        return cls.objects.first()
