from datetime import date

from django import forms

from core.forms import NomUniqueMixin
from core.models import ModePaiementMixin
from core.utils import format_fcfa
from apps.clients.models import Client
from .models import Abonnement, PaiementAbonnement, TypeAbonnement


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
    montant_verse = forms.IntegerField(
        required=False, min_value=0,
        label="Montant versé aujourd'hui",
        help_text="Laisser vide ou 0 si le client ne paie rien pour l'instant.",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'id': 'id_montant_verse'}),
    )
    mode_paiement = forms.ChoiceField(
        choices=ModePaiementMixin.MODE_PAIEMENT_CHOICES,
        required=False,
        label="Mode de paiement du versement",
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_mode_paiement'}),
    )
    operateur_mobile_money = forms.ChoiceField(
        choices=ModePaiementMixin.OPERATEUR_MOBILE_MONEY_CHOICES,
        required=False,
        label="Opérateur Mobile Money",
    )

    def clean(self):
        cleaned_data = super().clean()
        telephone = cleaned_data.get('telephone')
        nom_complet = cleaned_data.get('nom_complet')
        if telephone and not Client.objects.filter(telephone=telephone).exists() and not nom_complet:
            self.add_error('nom_complet', "Ce numéro est nouveau : le nom complet du client est obligatoire.")

        montant_verse = cleaned_data.get('montant_verse') or 0
        type_abonnement = cleaned_data.get('type_abonnement')

        if montant_verse > 0:
            if not cleaned_data.get('mode_paiement'):
                self.add_error('mode_paiement', "Précisez le mode de paiement du versement.")
            elif cleaned_data.get('mode_paiement') == 'mobile_money' and not cleaned_data.get('operateur_mobile_money'):
                self.add_error('operateur_mobile_money', "Précisez l'opérateur Mobile Money.")

            if type_abonnement and montant_verse > type_abonnement.prix:
                self.add_error(
                    'montant_verse',
                    f"Le montant versé ne peut pas dépasser le prix de l'abonnement ({format_fcfa(type_abonnement.prix)})."
                )
        return cleaned_data


class PaiementAbonnementForm(forms.Form):
    montant = forms.IntegerField(
        min_value=1,
        label="Montant versé",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'id': 'id_paiement_montant'}),
    )
    mode_paiement = forms.ChoiceField(
        choices=ModePaiementMixin.MODE_PAIEMENT_CHOICES,
        label="Mode de paiement",
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_paiement_mode'}),
    )
    operateur_mobile_money = forms.ChoiceField(
        choices=ModePaiementMixin.OPERATEUR_MOBILE_MONEY_CHOICES,
        required=False,
        label="Opérateur Mobile Money",
    )

    def __init__(self, *args, abonnement=None, **kwargs):
        self.abonnement = abonnement
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        montant = cleaned_data.get('montant')

        if cleaned_data.get('mode_paiement') == 'mobile_money' and not cleaned_data.get('operateur_mobile_money'):
            self.add_error('operateur_mobile_money', "Précisez l'opérateur Mobile Money.")

        if montant and self.abonnement is not None:
            reste = self.abonnement.montant_restant
            if montant > reste:
                self.add_error(
                    'montant',
                    f"Ce montant dépasse le reste à payer ({format_fcfa(reste)}). "
                    f"L'abonnement ne peut pas être payé au-delà de son prix."
                )
        return cleaned_data
