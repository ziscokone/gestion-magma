from datetime import date

from django.db import models
from django.db.models import Sum
from django.utils import timezone

from core.models import ModePaiementMixin
from core.utils import format_fcfa


class Fournisseur(models.Model):
    nom = models.CharField(max_length=200, verbose_name="Nom")
    telephone = models.CharField(max_length=20, blank=True, verbose_name="Téléphone")
    adresse = models.TextField(blank=True, verbose_name="Adresse")
    actif = models.BooleanField(default=True, verbose_name="Actif")
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['nom']
        verbose_name = "Fournisseur"
        verbose_name_plural = "Fournisseurs"

    def __str__(self):
        return self.nom

    @property
    def nombre_achats(self):
        return self.mouvements.filter(type_mouvement='entree').count()

    @property
    def montant_total_achats(self):
        # `montant` est une property (quantité × prix), pas un champ stocké :
        # on ne peut pas l'agréger en SQL, on calcule donc en Python.
        return sum(m.montant for m in self.mouvements.filter(type_mouvement='entree'))


class CategorieProduit(models.Model):
    """Catégories de produits configurables (Boissons, Compléments...)."""
    cle = models.SlugField(max_length=50, unique=True, blank=True, null=True, verbose_name="Clé technique")
    nom = models.CharField(max_length=100, verbose_name="Nom")
    actif = models.BooleanField(default=True, verbose_name="Actif")

    class Meta:
        ordering = ['nom']
        verbose_name = "Catégorie de produit"
        verbose_name_plural = "Catégories de produit"

    def __str__(self):
        return self.nom


class Produit(models.Model):
    """
    Produits configurables (nom, catégorie, prix, seuil d'alerte). Le stock
    restant se calcule à partir de l'historique des mouvements — jamais
    stocké en dur, pour ne jamais se désynchroniser de la réalité.
    """
    UNITE_CHOICES = [
        ('piece', 'Pièce'),
        ('carton', 'Carton'),
        ('litre', 'Litre'),
        ('kg', 'Kilogramme'),
    ]

    nom = models.CharField(max_length=200, verbose_name="Nom du produit")
    categorie = models.ForeignKey(
        CategorieProduit, on_delete=models.PROTECT, related_name='produits', verbose_name="Catégorie"
    )
    unite = models.CharField(max_length=20, choices=UNITE_CHOICES, default='piece', verbose_name="Unité")
    prix_achat = models.PositiveIntegerField(verbose_name="Prix d'achat (FCFA)")
    prix_vente = models.PositiveIntegerField(null=True, blank=True, verbose_name="Prix de vente (FCFA)")
    seuil_alerte = models.PositiveIntegerField(default=5, verbose_name="Seuil d'alerte (stock minimum)")
    actif = models.BooleanField(default=True, verbose_name="Actif")
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['nom']
        verbose_name = "Produit"
        verbose_name_plural = "Produits"

    def __str__(self):
        return self.nom

    @property
    def stock_actuel(self):
        entrees = self.mouvements.filter(type_mouvement='entree').aggregate(total=Sum('quantite'))['total'] or 0
        sorties = self.mouvements.filter(type_mouvement='sortie').aggregate(total=Sum('quantite'))['total'] or 0
        return entrees - sorties

    @property
    def stock_faible(self):
        return self.stock_actuel <= self.seuil_alerte

    @property
    def valeur_stock(self):
        return self.stock_actuel * self.prix_achat


class Vente(ModePaiementMixin, models.Model):
    """
    Ticket de vente pouvant regrouper plusieurs produits (panier) — chaque
    produit du panier crée sa propre ligne `MouvementStock` (sortie, motif
    vente) rattachée à cette vente, pour ne rien changer à la façon dont le
    stock est décompté ligne par ligne.
    """
    date = models.DateTimeField(default=timezone.now, verbose_name="Date de la vente")
    enregistre_par = models.ForeignKey(
        'comptes.Utilisateur', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='ventes_enregistrees', verbose_name="Enregistré par"
    )

    class Meta:
        ordering = ['-date']
        verbose_name = "Vente"
        verbose_name_plural = "Ventes"

    def __str__(self):
        return f"Vente {self.numero_vente} — {format_fcfa(self.montant_total)}"

    @property
    def montant_total(self):
        return sum(ligne.montant for ligne in self.lignes.all())

    @property
    def numero_vente(self):
        """Numéro de ticket façon reçu : VTE-AAAA-MM-NNNNN, séquence qui
        repart à 1 chaque mois (calculé à la volée, pas stocké)."""
        rang = Vente.objects.filter(
            date__year=self.date.year, date__month=self.date.month, pk__lte=self.pk,
        ).count()
        return f"VTE-{self.date.year}-{self.date.month:02d}-{rang:05d}"


class MouvementStock(ModePaiementMixin, models.Model):
    TYPE_MOUVEMENT_CHOICES = [
        ('entree', 'Entrée'),
        ('sortie', 'Sortie'),
    ]

    MOTIF_SORTIE_CHOICES = [
        ('vente', 'Vente au client'),
        ('perte', 'Casse / Perte'),
        ('usage_interne', 'Usage interne'),
    ]

    produit = models.ForeignKey(Produit, on_delete=models.PROTECT, related_name='mouvements', verbose_name="Produit")
    type_mouvement = models.CharField(max_length=10, choices=TYPE_MOUVEMENT_CHOICES, verbose_name="Type de mouvement")
    quantite = models.PositiveIntegerField(verbose_name="Quantité")
    date = models.DateTimeField(default=timezone.now, verbose_name="Date du mouvement")
    prix_unitaire = models.PositiveIntegerField(verbose_name="Prix unitaire (FCFA)")
    fournisseur = models.ForeignKey(
        Fournisseur, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='mouvements', verbose_name="Fournisseur"
    )
    motif = models.CharField(max_length=20, choices=MOTIF_SORTIE_CHOICES, blank=True, verbose_name="Motif de sortie")
    date_peremption = models.DateField(null=True, blank=True, verbose_name="Date de péremption")
    vente = models.ForeignKey(
        Vente, on_delete=models.CASCADE, null=True, blank=True,
        related_name='lignes', verbose_name="Vente (panier)"
    )
    enregistre_par = models.ForeignKey(
        'comptes.Utilisateur', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='mouvements_stock_enregistres', verbose_name="Enregistré par"
    )

    class Meta:
        ordering = ['-date']
        verbose_name = "Mouvement de stock"
        verbose_name_plural = "Mouvements de stock"

    def __str__(self):
        return f"{self.get_type_mouvement_display()} — {self.produit.nom} ({self.quantite})"

    def save(self, *args, **kwargs):
        if not self.prix_unitaire:
            if self.type_mouvement == 'sortie' and self.motif == 'vente' and self.produit.prix_vente:
                self.prix_unitaire = self.produit.prix_vente
            else:
                self.prix_unitaire = self.produit.prix_achat
        super().save(*args, **kwargs)

    @property
    def montant(self):
        return self.quantite * self.prix_unitaire

    @property
    def est_perime(self):
        if self.date_peremption:
            return self.date_peremption < date.today()
        return False

    @property
    def expire_bientot(self):
        if self.date_peremption and not self.est_perime:
            return (self.date_peremption - date.today()).days <= 7
        return False
