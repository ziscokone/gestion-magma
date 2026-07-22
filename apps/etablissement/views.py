from django.views.generic import UpdateView
from django.urls import reverse_lazy
from django.contrib import messages
from core.mixins import SuperAdminRequiredMixin
from .models import Etablissement
from .forms import EtablissementForm


class ParametresView(SuperAdminRequiredMixin, UpdateView):
    """Réglages de l'établissement — réservé au Super Administrateur."""
    model = Etablissement
    form_class = EtablissementForm
    template_name = 'etablissement/parametres.html'
    success_url = reverse_lazy('etablissement:parametres')

    def get_object(self, queryset=None):
        instance = Etablissement.get_instance()
        if instance is None:
            instance = Etablissement.objects.create()
        return instance

    def form_valid(self, form):
        messages.success(self.request, 'Paramètres mis à jour avec succès.')
        return super().form_valid(form)
