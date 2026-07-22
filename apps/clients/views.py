from datetime import date

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.db.models.deletion import ProtectedError
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import ListView, DetailView, UpdateView, CreateView, DeleteView

from core.mixins import AdminRequiredMixin
from apps.abonnements.models import Abonnement
from .forms import SeanceForm, ClientForm, TypePrestationForm
from .models import Client, Seance, TypePrestation


class SeanceListView(LoginRequiredMixin, ListView):
    """Journal des séances — page d'accueil du module Clients & Séances."""
    model = Seance
    template_name = 'clients/seance_list.html'
    context_object_name = 'seances'
    paginate_by = 15

    def get_queryset(self):
        queryset = Seance.objects.select_related('client', 'type_prestation').all()
        jour = self.request.GET.get('date')
        if jour:
            queryset = queryset.filter(date__date=jour)
        else:
            queryset = queryset.filter(date__date=date.today())
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['date_filtre'] = self.request.GET.get('date', date.today().isoformat())
        context['recette_jour'] = self.get_queryset().aggregate(total=Sum('montant'))['total'] or 0
        return context


class SeanceCreateView(LoginRequiredMixin, View):
    template_name = 'clients/seance_form.html'

    def _prix_par_type(self):
        return {str(tp.pk): tp.prix for tp in TypePrestation.objects.filter(actif=True)}

    def get(self, request):
        return render(request, self.template_name, {'form': SeanceForm(), 'prix_par_type': self._prix_par_type()})

    def post(self, request):
        form = SeanceForm(request.POST)
        if form.is_valid():
            telephone = form.cleaned_data['telephone']
            nom_complet = form.cleaned_data['nom_complet']
            client, _ = Client.objects.get_or_create(
                telephone=telephone,
                defaults={'nom_complet': nom_complet}
            )
            type_prestation = form.cleaned_data['type_prestation']
            Seance.objects.create(
                client=client,
                type_prestation=type_prestation,
                mode_paiement=form.cleaned_data['mode_paiement'],
                operateur_mobile_money=form.cleaned_data['operateur_mobile_money'],
                statut_paiement=form.cleaned_data['statut_paiement'],
                montant=type_prestation.prix,
                enregistre_par=request.user,
            )
            messages.success(request, f'Séance enregistrée pour {client.nom_complet}.')
            return redirect('clients:seance_list')
        return render(request, self.template_name, {'form': form, 'prix_par_type': self._prix_par_type()})


def rechercher_client(request):
    """Recherche exacte d'un client par téléphone, pour l'auto-remplissage du formulaire."""
    telephone = request.GET.get('telephone', '').strip()
    client = Client.objects.filter(telephone=telephone).first()
    if client:
        return JsonResponse({'found': True, 'nom_complet': client.nom_complet})
    return JsonResponse({'found': False})


def suggerer_clients(request):
    """Suggestions de clients (nom ou téléphone) pendant la saisie, dès 3 caractères."""
    q = request.GET.get('q', '').strip()
    if len(q) < 3:
        return JsonResponse({'resultats': []})
    clients = Client.objects.filter(
        Q(telephone__icontains=q) | Q(nom_complet__icontains=q)
    )[:6]
    resultats = [{'telephone': c.telephone, 'nom_complet': c.nom_complet} for c in clients]
    return JsonResponse({'resultats': resultats})


class ClientListView(LoginRequiredMixin, ListView):
    model = Client
    template_name = 'clients/client_list.html'
    context_object_name = 'clients'
    paginate_by = 15

    def get_queryset(self):
        queryset = Client.objects.all()
        search = self.request.GET.get('q')
        if search:
            queryset = queryset.filter(
                Q(nom_complet__icontains=search) | Q(telephone__icontains=search)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q', '')
        return context


class ClientDetailView(LoginRequiredMixin, DetailView):
    model = Client
    template_name = 'clients/client_detail.html'
    context_object_name = 'client'
    slug_field = 'public_id'
    slug_url_kwarg = 'public_id'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        client = self.object
        seances_qs = client.seances.select_related('type_prestation').all()

        paginator = Paginator(seances_qs, 10)
        page_number = self.request.GET.get('page', 1)
        context['seances'] = paginator.get_page(page_number)

        context['nb_seances'] = seances_qs.count()
        context['montant_total'] = seances_qs.aggregate(total=Sum('montant'))['total'] or 0
        context['derniere_seance'] = seances_qs.order_by('-date').first()

        abonnements_qs = client.abonnements.select_related('type_abonnement').all()
        abo_paginator = Paginator(abonnements_qs, 10)
        abo_page_number = self.request.GET.get('page_abo', 1)
        context['abonnements'] = abo_paginator.get_page(abo_page_number)
        context['abonnement_actif'] = abonnements_qs.filter(date_fin__gte=date.today()).order_by('-date_fin').first()

        return context


class ClientUpdateView(LoginRequiredMixin, UpdateView):
    """Compléter / corriger la fiche d'un client."""
    model = Client
    form_class = ClientForm
    template_name = 'clients/client_form.html'
    slug_field = 'public_id'
    slug_url_kwarg = 'public_id'

    def get_success_url(self):
        return reverse_lazy('clients:client_detail', kwargs={'public_id': self.object.public_id})

    def form_valid(self, form):
        messages.success(self.request, 'Fiche client mise à jour avec succès.')
        return super().form_valid(form)


class TypePrestationListView(AdminRequiredMixin, ListView):
    """Configuration des types de prestation (nom, prix) — Super Admin / Manager."""
    model = TypePrestation
    template_name = 'clients/type_prestation_list.html'
    context_object_name = 'types_prestation'


class TypePrestationCreateView(AdminRequiredMixin, CreateView):
    model = TypePrestation
    form_class = TypePrestationForm
    template_name = 'clients/type_prestation_form.html'
    success_url = reverse_lazy('clients:type_prestation_list')

    def form_valid(self, form):
        messages.success(self.request, 'Type de prestation créé avec succès.')
        return super().form_valid(form)


class TypePrestationUpdateView(AdminRequiredMixin, UpdateView):
    model = TypePrestation
    form_class = TypePrestationForm
    template_name = 'clients/type_prestation_form.html'
    success_url = reverse_lazy('clients:type_prestation_list')

    def form_valid(self, form):
        messages.success(self.request, 'Type de prestation modifié avec succès.')
        return super().form_valid(form)


class TypePrestationDeleteView(AdminRequiredMixin, DeleteView):
    model = TypePrestation
    template_name = 'clients/type_prestation_confirm_delete.html'
    success_url = reverse_lazy('clients:type_prestation_list')

    def form_valid(self, form):
        try:
            messages.success(self.request, 'Type de prestation supprimé avec succès.')
            return super().form_valid(form)
        except ProtectedError:
            messages.error(
                self.request,
                "Impossible de supprimer ce type : des séances y sont déjà rattachées. "
                "Désactivez-le plutôt depuis le formulaire de modification."
            )
            return redirect('clients:type_prestation_list')
