from django import forms
from .models import Etablissement


class EtablissementForm(forms.ModelForm):
    class Meta:
        model = Etablissement
        fields = ['nom', 'logo', 'slogan', 'adresse', 'telephone', 'email', 'solde_initial_caisse']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'logo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'slogan': forms.TextInput(attrs={'class': 'form-control'}),
            'adresse': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'telephone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'solde_initial_caisse': forms.NumberInput(attrs={'class': 'form-control'}),
        }
