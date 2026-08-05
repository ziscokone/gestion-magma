from django.core.validators import RegexValidator
from django.db import models

from core.indicatifs import CHOIX_INDICATIFS_PAYS
from core.utils import assombrir_couleur, hex_vers_rgb

_VALIDATEUR_HEX = RegexValidator(
    regex=r'^#[0-9A-Fa-f]{6}$',
    message="Couleur au format hexadécimal, ex : #386745",
)

MESSAGE_PARTAGE_CARTE_DEFAUT = (
    "Bonjour {client}, voici votre carte de membre {etablissement} "
    "({type_abonnement}, valable jusqu'au {date_expiration}) :\n"
    "{lien_carte}"
)

MESSAGE_RELANCE_DEFAUT = (
    "Bonjour {client}, votre {type_abonnement} chez {etablissement} expire le {date_expiration} "
    "({jours_restants} jour(s) restant(s)). Pensez à le renouveler pour ne pas perdre l'accès à la salle !"
)


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
    indicatif_pays_defaut = models.CharField(
        max_length=6, default='+225', choices=CHOIX_INDICATIFS_PAYS,
        verbose_name="Indicatif pays par défaut (partage WhatsApp)",
        help_text="Utilisé pour composer le numéro complet des clients lors du partage WhatsApp, "
                   "sauf si un client a un indicatif différent renseigné sur sa fiche."
    )
    couleur_principale = models.CharField(
        max_length=7, default='#386745', validators=[_VALIDATEUR_HEX],
        verbose_name="Couleur principale",
        help_text="Utilisée pour la navigation, les boutons et les en-têtes de document (PDF)."
    )
    couleur_secondaire = models.CharField(
        max_length=7, default='#FDF7E5', validators=[_VALIDATEUR_HEX],
        verbose_name="Couleur secondaire",
        help_text="Utilisée pour le texte sur fond de couleur principale (ex : slogan)."
    )
    couleur_accent = models.CharField(
        max_length=7, default='#F46722', validators=[_VALIDATEUR_HEX],
        verbose_name="Couleur d'accent (survol)",
        help_text="Utilisée au survol des menus et des boutons."
    )
    solde_initial_caisse = models.PositiveIntegerField(
        default=0, verbose_name="Solde de caisse initial (FCFA)",
        help_text="Montant déjà en caisse au moment où vous commencez à utiliser le logiciel."
    )
    message_partage_carte = models.TextField(
        default=MESSAGE_PARTAGE_CARTE_DEFAUT, verbose_name="Message de partage de la carte de membre",
        help_text="Variables disponibles : {client}, {etablissement}, {type_abonnement}, {date_expiration}, {lien_carte}."
    )
    message_relance = models.TextField(
        default=MESSAGE_RELANCE_DEFAUT, verbose_name="Message de relance avant expiration",
        help_text="Variables disponibles : {client}, {etablissement}, {type_abonnement}, {date_expiration}, {jours_restants}."
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

    @property
    def couleur_principale_foncee(self):
        """État :hover/:active de la couleur principale — dérivé, pas de champ dédié."""
        return assombrir_couleur(self.couleur_principale)

    @property
    def couleur_principale_rgb(self):
        """'R,G,B' pour composer des rgba() CSS (dégradés, halos) à partir de la couleur principale."""
        return '{},{},{}'.format(*hex_vers_rgb(self.couleur_principale))

    @property
    def couleur_accent_foncee(self):
        """État :hover des boutons déjà en couleur d'accent (ex : bouton "Nouvel abonnement")."""
        return assombrir_couleur(self.couleur_accent)

    @property
    def couleur_accent_rgb(self):
        """'R,G,B' pour composer des rgba() CSS (ex : survol de lignes de tableau) à partir de la couleur d'accent."""
        return '{},{},{}'.format(*hex_vers_rgb(self.couleur_accent))
