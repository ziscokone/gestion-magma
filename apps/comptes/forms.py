from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
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
        if current_user is not None and not current_user.is_super_admin:
            # Un Manager ne doit même pas voir qu'il pourrait attribuer ce
            # rôle — seul le Super Administrateur peut créer un autre
            # Super Administrateur.
            self.fields['role'].choices = [c for c in self.fields['role'].choices if c[0] != 'super_admin']


class UtilisateurUpdateForm(forms.ModelForm):
    """Modification d'un utilisateur existant — le mot de passe est optionnel :
    laissé vide, il reste inchangé ; renseigné, il remplace l'ancien."""
    password1 = forms.CharField(
        label="Nouveau mot de passe", required=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'new-password'}),
        help_text="Laisser vide pour conserver le mot de passe actuel.",
    )
    password2 = forms.CharField(
        label="Confirmation du nouveau mot de passe", required=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'new-password'}),
    )

    class Meta:
        model = Utilisateur
        fields = ['nom_complet', 'telephone', 'role', 'actif']
        widgets = {
            'nom_complet': forms.TextInput(attrs={'class': 'form-control'}),
            'telephone': forms.TextInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
            'actif': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, current_user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_user = current_user
        if current_user is not None and not current_user.is_super_admin:
            # Même restriction qu'à la création : un Manager ne doit ni voir
            # ni pouvoir attribuer le rôle Super Administrateur.
            self.fields['role'].choices = [c for c in self.fields['role'].choices if c[0] != 'super_admin']

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        if password1 or password2:
            if password1 != password2:
                self.add_error('password2', "Les deux mots de passe ne correspondent pas.")
            else:
                try:
                    validate_password(password1, self.instance)
                except ValidationError as erreur:
                    self.add_error('password1', erreur)
        return cleaned_data

    def save(self, commit=True):
        utilisateur = super().save(commit=False)
        password1 = self.cleaned_data.get('password1')
        if password1:
            utilisateur.set_password(password1)
        if commit:
            utilisateur.save()
        return utilisateur
