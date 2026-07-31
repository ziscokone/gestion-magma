from django.views.generic import UpdateView
from django.urls import reverse_lazy
from django.contrib import messages
from core.mixins import AdminRequiredMixin, SuperAdminRequiredMixin
from .models import Etablissement
from .forms import EtablissementForm, MessagesWhatsAppForm


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


class MessagesWhatsAppView(AdminRequiredMixin, UpdateView):
    """Gabarits des messages WhatsApp (carte de membre, relance) — librement
    modifiables, avec des variables substituées automatiquement à l'envoi."""
    model = Etablissement
    form_class = MessagesWhatsAppForm
    template_name = 'etablissement/messages_whatsapp.html'
    success_url = reverse_lazy('etablissement:messages_whatsapp')

    def get_object(self, queryset=None):
        instance = Etablissement.get_instance()
        if instance is None:
            instance = Etablissement.objects.create()
        return instance

    def form_valid(self, form):
        messages.success(self.request, 'Messages WhatsApp mis à jour avec succès.')
        return super().form_valid(form)
