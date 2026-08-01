from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.views import View
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.db.models import Q
from core.mixins import AdminRequiredMixin, SuperAdminRequiredMixin
from .models import Utilisateur, Module
from .forms import UtilisateurForm, UtilisateurUpdateForm


class UtilisateurListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """Liste des utilisateurs — réservée aux administrateurs."""
    model = Utilisateur
    template_name = 'comptes/utilisateur_list.html'
    context_object_name = 'utilisateurs'

    def test_func(self):
        return self.request.user.has_global_access

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            raise PermissionDenied("Vous n'avez pas les droits nécessaires pour accéder à cette page.")
        return super().handle_no_permission()

    def get_queryset(self):
        queryset = Utilisateur.objects.all()
        search = self.request.GET.get('q')
        if search:
            queryset = queryset.filter(
                Q(nom_complet__icontains=search) |
                Q(username__icontains=search) |
                Q(telephone__icontains=search)
            )
        return queryset.order_by('nom_complet')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q', '')
        return context


class UtilisateurCreateView(AdminRequiredMixin, CreateView):
    model = Utilisateur
    form_class = UtilisateurForm
    template_name = 'comptes/utilisateur_form.html'
    success_url = reverse_lazy('comptes:utilisateur_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['current_user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, 'Utilisateur créé avec succès.')
        return super().form_valid(form)


class UtilisateurUpdateView(AdminRequiredMixin, UpdateView):
    """Un Manager ne peut modifier ni la fiche du Super Administrateur (accès
    total, rôle et statut protégés — il ne doit jamais pouvoir se faire
    verrouiller hors du logiciel), ni attribuer ce rôle à qui que ce soit."""
    model = Utilisateur
    form_class = UtilisateurUpdateForm
    template_name = 'comptes/utilisateur_form.html'
    success_url = reverse_lazy('comptes:utilisateur_list')

    def get_object(self, queryset=None):
        utilisateur = super().get_object(queryset)
        if utilisateur.role == 'super_admin' and not self.request.user.is_super_admin:
            raise PermissionDenied("Seul le Super Administrateur peut modifier ce compte.")
        return utilisateur

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['current_user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, 'Utilisateur modifié avec succès.')
        return super().form_valid(form)


class UtilisateurDeleteView(SuperAdminRequiredMixin, DeleteView):
    """Supprimer un utilisateur — réservé au Super Administrateur."""
    model = Utilisateur
    template_name = 'comptes/utilisateur_confirm_delete.html'
    success_url = reverse_lazy('comptes:utilisateur_list')

    def form_valid(self, form):
        messages.success(self.request, 'Utilisateur supprimé avec succès.')
        return super().form_valid(form)


class ModulesUtilisateurView(LoginRequiredMixin, View):
    """Gestion des modules autorisés pour un utilisateur. Réservé aux
    administrateurs — et, comme pour la fiche elle-même, un Manager ne peut
    pas toucher au compte du Super Administrateur."""

    def _check_permission(self, request, cible=None):
        if not request.user.has_global_access:
            raise PermissionDenied
        if cible is not None and cible.role == 'super_admin' and not request.user.is_super_admin:
            raise PermissionDenied("Seul le Super Administrateur peut modifier ce compte.")

    def get(self, request, pk):
        cible = get_object_or_404(Utilisateur, pk=pk)
        self._check_permission(request, cible)
        tous_modules = Module.objects.filter(actif=True).order_by('ordre')
        modules_actifs = set(cible.modules_autorises.values_list('pk', flat=True))
        return render(request, 'comptes/utilisateur_modules.html', {
            'cible': cible,
            'tous_modules': tous_modules,
            'modules_actifs': modules_actifs,
        })

    def post(self, request, pk):
        cible = get_object_or_404(Utilisateur, pk=pk)
        self._check_permission(request, cible)
        selected_ids = request.POST.getlist('modules')
        cible.modules_autorises.set(Module.objects.filter(pk__in=selected_ids))
        messages.success(request, f'Accès aux modules mis à jour pour {cible.nom_complet}.')
        return redirect('comptes:utilisateur_list')
