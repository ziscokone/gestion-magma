from django import forms

from core.forms import NomUniqueMixin

from .models import Client, Seance, TypePrestation


class TypePrestationChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.nom


class TypePrestationForm(NomUniqueMixin, forms.ModelForm):
    class Meta:
        model = TypePrestation
        fields = ['nom', 'prix', 'duree_minutes', 'actif']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'prix': forms.NumberInput(attrs={'class': 'form-control'}),
            'duree_minutes': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'placeholder': 'minutes'}),
            'actif': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = [
            'nom_complet', 'telephone', 'photo_cni',
            'sexe', 'date_naissance', 'objectif',
            'taille', 'poids', 'bassin',
            'contact_urgence_nom', 'contact_urgence_telephone',
            'antecedents_medicaux',
        ]
        widgets = {
            'nom_complet': forms.TextInput(attrs={'class': 'form-control'}),
            'telephone': forms.TextInput(attrs={'class': 'form-control'}),
            'photo_cni': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'sexe': forms.Select(attrs={'class': 'form-select'}),
            'date_naissance': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'objectif': forms.Select(attrs={'class': 'form-select'}),
            'taille': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'placeholder': 'cm'}),
            'poids': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'step': '0.1', 'placeholder': 'kg'}),
            'bassin': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'placeholder': 'cm'}),
            'contact_urgence_nom': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_urgence_telephone': forms.TextInput(attrs={'class': 'form-control'}),
            'antecedents_medicaux': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class SeanceForm(forms.Form):
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
    type_prestation = TypePrestationChoiceField(
        queryset=TypePrestation.objects.filter(actif=True),
        label="Type de prestation",
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_type_prestation'}),
    )
    mode_paiement = forms.ChoiceField(
        choices=Seance.MODE_PAIEMENT_CHOICES,
        label="Mode de paiement",
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_mode_paiement'}),
    )
    operateur_mobile_money = forms.ChoiceField(
        choices=Seance.OPERATEUR_MOBILE_MONEY_CHOICES,
        required=False,
        label="Opérateur Mobile Money",
    )
    statut_paiement = forms.ChoiceField(
        choices=Seance.STATUT_PAIEMENT_CHOICES,
        label="Statut du paiement",
        widget=forms.Select(attrs={'class': 'form-select'}),
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
