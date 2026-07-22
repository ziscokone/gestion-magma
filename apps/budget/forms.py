from django import forms

from core.forms import NomUniqueMixin

from .models import CategorieCharge, OperationBudget


class CategorieChargeForm(NomUniqueMixin, forms.ModelForm):
    class Meta:
        model = CategorieCharge
        fields = ['nom', 'actif']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'actif': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class CategorieChargeChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.nom


CATEGORIES_MANUELLES_CHOICES = [
    c for c in OperationBudget.CATEGORIE_CHOICES if c[0] in OperationBudget.CATEGORIES_MANUELLES
]


class OperationBudgetForm(forms.Form):
    """Saisie manuelle — réservée aux catégories charge/salaire/autre (les
    recettes séance/abonnement et achats/ventes produit sont automatiques)."""

    type_operation = forms.ChoiceField(
        choices=OperationBudget.TYPE_OPERATION_CHOICES,
        label="Type d'opération",
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_type_operation'}),
    )
    categorie = forms.ChoiceField(
        choices=CATEGORIES_MANUELLES_CHOICES,
        label="Catégorie",
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_categorie'}),
    )
    categorie_charge = CategorieChargeChoiceField(
        queryset=CategorieCharge.objects.filter(actif=True),
        required=False,
        label="Sous-catégorie de charge",
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    montant = forms.IntegerField(
        min_value=1,
        label="Montant",
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
    )
    mode_paiement = forms.ChoiceField(
        choices=OperationBudget.MODE_PAIEMENT_CHOICES,
        label="Mode de paiement",
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_mode_paiement'}),
    )
    operateur_mobile_money = forms.ChoiceField(
        choices=OperationBudget.OPERATEUR_MOBILE_MONEY_CHOICES,
        required=False,
        label="Opérateur Mobile Money",
    )
    description = forms.CharField(
        required=False,
        label="Description",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': "Ex: Loyer juillet, Salaire coach Jean..."}),
    )

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('categorie') == 'charge' and not cleaned_data.get('categorie_charge'):
            self.add_error('categorie_charge', "Précisez la sous-catégorie de charge.")
        if cleaned_data.get('mode_paiement') == 'mobile_money' and not cleaned_data.get('operateur_mobile_money'):
            self.add_error('operateur_mobile_money', "Précisez l'opérateur Mobile Money.")
        return cleaned_data
