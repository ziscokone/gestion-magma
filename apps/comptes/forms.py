from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Utilisateur


class UtilisateurForm(UserCreationForm):
    class Meta:
        model = Utilisateur
        fields = ['username', 'nom_complet', 'telephone', 'role', 'actif']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'nom_complet': forms.TextInput(attrs={'class': 'form-control'}),
            'telephone': forms.TextInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
            'actif': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, current_user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_user = current_user
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})


class UtilisateurUpdateForm(forms.ModelForm):
    class Meta:
        model = Utilisateur
        fields = ['nom_complet', 'telephone', 'role', 'actif']
        widgets = {
            'nom_complet': forms.TextInput(attrs={'class': 'form-control'}),
            'telephone': forms.TextInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
            'actif': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
