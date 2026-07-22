from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.urls import reverse, NoReverseMatch


class Module(models.Model):
    cle         = models.SlugField(max_length=50, unique=True, verbose_name="Clé")
    nom         = models.CharField(max_length=100, verbose_name="Nom")
    description = models.CharField(max_length=200, blank=True, verbose_name="Description")
    icone       = models.CharField(max_length=100, default='bi-grid', verbose_name="Icône Bootstrap")
    url_name    = models.CharField(max_length=100, verbose_name="Nom d'URL Django")
    ordre       = models.PositiveSmallIntegerField(default=0, verbose_name="Ordre d'affichage")
    actif       = models.BooleanField(default=True, verbose_name="Actif")

    class Meta:
        ordering = ['ordre']
        verbose_name = "Module"
        verbose_name_plural = "Modules"

    def __str__(self):
        return self.nom

    def get_url(self):
        try:
            return reverse(self.url_name)
        except NoReverseMatch:
            return '#'


class UtilisateurManager(BaseUserManager):
    """Manager personnalisé pour le modèle Utilisateur."""

    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError("Le nom d'utilisateur est obligatoire")
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'super_admin')

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(username, password, **extra_fields)


class Utilisateur(AbstractUser):
    """
    Modèle utilisateur personnalisé pour la gestion des rôles.
    Trois rôles : Super Administrateur (accès total, seul à pouvoir supprimer
    un utilisateur ou modifier les paramètres de l'établissement), Manager
    (mêmes droits de gestion que le Super Admin sauf ces deux actions) et
    Utilisateur (accès limité aux modules qui lui sont attribués).
    """
    ROLE_CHOICES = [
        ('super_admin', 'Super Administrateur'),
        ('manager', 'Manager'),
        ('utilisateur', 'Utilisateur'),
    ]

    nom_complet = models.CharField(max_length=200, verbose_name="Nom complet")
    telephone = models.CharField(max_length=20, blank=True, verbose_name="Téléphone")
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='utilisateur',
        verbose_name="Rôle"
    )
    actif = models.BooleanField(default=True, verbose_name="Actif")
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    modules_autorises = models.ManyToManyField(
        'Module',
        blank=True,
        related_name='utilisateurs_autorises',
        verbose_name="Modules autorisés",
    )

    objects = UtilisateurManager()

    EMAIL_FIELD = 'email'
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['nom_complet']

    class Meta:
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"
        ordering = ['nom_complet']

    def __str__(self):
        return f"{self.nom_complet} ({self.get_role_display()})"

    @property
    def is_super_admin(self):
        return self.role == 'super_admin'

    @property
    def is_manager(self):
        return self.role == 'manager'

    @property
    def has_global_access(self):
        """Super Admin et Manager : gestion des utilisateurs, visibilité totale du hub."""
        return self.role in ('super_admin', 'manager')
