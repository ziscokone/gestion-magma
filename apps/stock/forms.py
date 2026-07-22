from django import forms

from core.forms import NomUniqueMixin

from .models import CategorieProduit, Fournisseur, Produit, MouvementStock


class CategorieProduitForm(NomUniqueMixin, forms.ModelForm):
    class Meta:
        model = CategorieProduit
        fields = ['nom', 'actif']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'actif': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class FournisseurForm(forms.ModelForm):
    class Meta:
        model = Fournisseur
        fields = ['nom', 'telephone', 'adresse', 'actif']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'telephone': forms.TextInput(attrs={'class': 'form-control'}),
            'adresse': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'actif': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ProduitForm(forms.ModelForm):
    class Meta:
        model = Produit
        fields = ['nom', 'categorie', 'unite', 'prix_achat', 'prix_vente', 'seuil_alerte', 'actif']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'categorie': forms.Select(attrs={'class': 'form-select'}),
            'unite': forms.Select(attrs={'class': 'form-select'}),
            'prix_achat': forms.NumberInput(attrs={'class': 'form-control'}),
            'prix_vente': forms.NumberInput(attrs={'class': 'form-control'}),
            'seuil_alerte': forms.NumberInput(attrs={'class': 'form-control'}),
            'actif': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['categorie'].queryset = CategorieProduit.objects.filter(actif=True)


class ProduitChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.nom


class FournisseurChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.nom


class ApprovisionnementForm(forms.Form):
    """Entrée de stock — achat auprès d'un fournisseur."""
    produit = ProduitChoiceField(
        queryset=Produit.objects.filter(actif=True),
        label="Produit",
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_produit'}),
    )
    fournisseur = FournisseurChoiceField(
        queryset=Fournisseur.objects.filter(actif=True),
        required=False,
        label="Fournisseur",
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_fournisseur'}),
    )
    quantite = forms.IntegerField(
        min_value=1,
        label="Quantité achetée",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'id': 'id_quantite'}),
    )
    prix_unitaire = forms.IntegerField(
        min_value=0,
        label="Prix d'achat unitaire (FCFA)",
        help_text="Prérempli avec le prix catalogue du produit — modifiable si le fournisseur a changé son tarif.",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'id': 'id_prix_unitaire'}),
    )
    date_peremption = forms.DateField(
        required=False,
        label="Date de péremption",
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
    )
    mode_paiement = forms.ChoiceField(
        choices=MouvementStock.MODE_PAIEMENT_CHOICES,
        label="Mode de paiement",
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_mode_paiement'}),
    )
    operateur_mobile_money = forms.ChoiceField(
        choices=MouvementStock.OPERATEUR_MOBILE_MONEY_CHOICES,
        required=False,
        label="Opérateur Mobile Money",
    )

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('mode_paiement') == 'mobile_money' and not cleaned_data.get('operateur_mobile_money'):
            self.add_error('operateur_mobile_money', "Précisez l'opérateur Mobile Money.")
        return cleaned_data


class VenteForm(forms.Form):
    """
    Vente au client — panier pouvant regrouper plusieurs produits.
    `produit`/`quantite`/`prix_unitaire` ne servent qu'au sélecteur de
    produit à ajouter au panier (widget géré en JS) ; le contenu réel du
    panier est soumis à part (`lignes_json`, cf. VenteCreateView) et validé
    côté vue plutôt que sur ces champs.
    """
    produit = ProduitChoiceField(
        queryset=Produit.objects.filter(actif=True),
        label="Produit",
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_produit'}),
    )
    quantite = forms.IntegerField(
        min_value=1,
        label="Quantité",
        widget=forms.NumberInput(attrs={'class': 'form-control text-center', 'id': 'id_quantite'}),
    )
    prix_unitaire = forms.IntegerField(
        min_value=0,
        label="Prix de vente unitaire (FCFA)",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'id': 'id_prix_unitaire'}),
    )
    mode_paiement = forms.ChoiceField(
        choices=MouvementStock.MODE_PAIEMENT_CHOICES,
        label="Mode de paiement",
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_mode_paiement'}),
    )
    operateur_mobile_money = forms.ChoiceField(
        choices=MouvementStock.OPERATEUR_MOBILE_MONEY_CHOICES,
        required=False,
        label="Opérateur Mobile Money",
    )

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('mode_paiement') == 'mobile_money' and not cleaned_data.get('operateur_mobile_money'):
            self.add_error('operateur_mobile_money', "Précisez l'opérateur Mobile Money.")
        return cleaned_data


class AjustementForm(forms.Form):
    """Sortie de stock hors vente (casse/perte, usage interne) — aucune transaction financière."""
    produit = ProduitChoiceField(
        queryset=Produit.objects.filter(actif=True),
        label="Produit",
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_produit'}),
    )
    quantite = forms.IntegerField(
        min_value=1,
        label="Quantité",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'id': 'id_quantite'}),
    )
    motif = forms.ChoiceField(
        choices=[c for c in MouvementStock.MOTIF_SORTIE_CHOICES if c[0] != 'vente'],
        label="Motif",
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    def clean(self):
        cleaned_data = super().clean()
        produit = cleaned_data.get('produit')
        quantite = cleaned_data.get('quantite')
        if produit and quantite and quantite > produit.stock_actuel:
            self.add_error(
                'quantite',
                f"Stock insuffisant : il ne reste que {produit.stock_actuel} {produit.get_unite_display().lower()}(s) en stock."
            )
        return cleaned_data
