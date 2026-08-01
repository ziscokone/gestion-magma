from datetime import date

from django import forms

from core.forms import NomUniqueMixin
from apps.clients.models import Client
from .models import Abonnement, TypeAbonnement


class TypeAbonnementChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.nom


class TypeAbonnementForm(NomUniqueMixin, forms.ModelForm):
    class Meta:
        model = TypeAbonnement
        fields = ['nom', 'prix', 'duree_jours', 'actif']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'prix': forms.NumberInput(attrs={'class': 'form-control'}),
            'duree_jours': forms.NumberInput(attrs={'class': 'form-control'}),
            'actif': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class AbonnementForm(forms.Form):
    telephone = forms.CharField(
        max_length=20,
        label="Téléphone du client",
        widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'id_telephone', 'autocomplete': 'off'}),
    )
    nom_complet = forms.CharField(
        max_length=200,
        required=False,
        label="Nom complet",
        widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'id_nom_complet'}),
    )
    type_abonnement = TypeAbonnementChoiceField(
        queryset=TypeAbonnement.objects.filter(actif=True),
        label="Type d'abonnement",
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_type_abonnement'}),
    )
    date_debut = forms.DateField(
        initial=date.today,
        label="Date de début",
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
    )
    mode_paiement = forms.ChoiceField(
        choices=Abonnement.MODE_PAIEMENT_CHOICES,
        label="Mode de paiement",
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_mode_paiement'}),
    )
    operateur_mobile_money = forms.ChoiceField(
        choices=Abonnement.OPERATEUR_MOBILE_MONEY_CHOICES,
        required=False,
        label="Opérateur Mobile Money",
    )

    def clean(self):
        cleaned_data = super().clean()
        telephone = cleaned_data.get('telephone')
        nom_complet = cleaned_data.get('nom_complet')
        if telephone and not Client.objects.filter(telephone=telephone).exists() and not nom_complet:
            self.add_error('nom_complet', "Ce numéro est nouveau : le nom complet du client est obligatoire.")
        if cleaned_data.get('mode_paiement') == 'mobile_money' and not cleaned_data.get('operateur_mobile_money'):
            self.add_error('operateur_mobile_money', "Précisez l'opérateur Mobile Money.")
        return cleaned_data
