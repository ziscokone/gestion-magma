from django import forms


class NomUniqueMixin:
    """À mixer dans un ModelForm ayant un champ `nom` : empêche la création
    de doublons insensibles à la casse (« Loyer » / « loyer » / « LOYER »)
    sur les petites entités configurables (types, catégories)."""

    def clean_nom(self):
        nom = self.cleaned_data['nom'].strip()
        qs = self._meta.model.objects.filter(nom__iexact=nom)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        existant = qs.first()
        if existant:
            raise forms.ValidationError(f"« {existant.nom} » existe déjà.")
        return nom
