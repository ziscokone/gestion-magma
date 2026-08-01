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
from core.models import modes_paiement_filtrables
from apps.abonnements.models import Abonnement
from .forms import SeanceForm, ClientForm, ObjectifSportifForm, QuartierForm, TypePrestationForm
from .models import Client, ObjectifSportif, Quartier, Seance, TypePrestation
from .services import repartition_clients_par_zone


class SeanceListView(LoginRequiredMixin, ListView):
    """Journal des séances — page d'accueil du module Clients & Séances."""
    model = Seance
    template_name = 'clients/seance_list.html'
    context_object_name = 'seances'
    paginate_by = 15

    def _queryset_jour(self):
        queryset = Seance.objects.select_related('client', 'type_prestation').all()
        jour = self.request.GET.get('date')
        if jour:
            queryset = queryset.filter(date__date=jour)
        else:
            queryset = queryset.filter(date__date=date.today())
        return queryset

    def get_queryset(self):
        queryset = self._queryset_jour()
        paiement = self.request.GET.get('paiement', 'tous')
        for cle, _, filtre, _ in modes_paiement_filtrables():
            if paiement == cle:
                return queryset.filter(**filtre)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['date_filtre'] = self.request.GET.get('date', date.today().isoformat())
        context['paiement_filtre'] = self.request.GET.get('paiement', 'tous')
        context['modes_paiement'] = [(cle, libelle) for cle, libelle, _, _ in modes_paiement_filtrables()]

        queryset_jour = self._queryset_jour()
        context['recette_jour'] = queryset_jour.aggregate(total=Sum('montant'))['total'] or 0

        repartition = []
        for cle, libelle, filtre, couleur in modes_paiement_filtrables():
            sous_ensemble = queryset_jour.filter(**filtre)
            nombre = sous_ensemble.count()
            if nombre:
                repartition.append({
                    'cle': cle, 'libelle': libelle, 'couleur': couleur, 'nombre': nombre,
                    'montant': sous_ensemble.aggregate(total=Sum('montant'))['total'] or 0,
                })
        context['repartition_paiement'] = repartition
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
                statut_paiement='paye',
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


class ClientRepartitionZoneView(LoginRequiredMixin, View):
    """Répartition des clients par quartier/zone, sous forme de camembert — met
    en évidence la zone dominante. Au-delà de 6 quartiers peuplés, les plus
    petits sont regroupés dans une part "Autres" pour garder le graphique lisible ;
    le tableau en dessous, lui, détaille chaque quartier individuellement."""
    template_name = 'clients/repartition_zone.html'

    def get(self, request):
        return render(request, self.template_name, repartition_clients_par_zone())


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

        paginator = Paginator(seances_qs, 5)
        page_number = self.request.GET.get('page', 1)
        context['seances'] = paginator.get_page(page_number)

        context['nb_seances'] = seances_qs.count()
        context['montant_total'] = seances_qs.aggregate(total=Sum('montant'))['total'] or 0
        context['derniere_seance'] = seances_qs.order_by('-date').first()

        abonnements_qs = client.abonnements.select_related('type_abonnement').all()
        abo_paginator = Paginator(abonnements_qs, 5)
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


class ObjectifSportifListView(AdminRequiredMixin, ListView):
    """Configuration des objectifs sportifs proposés aux clients — Super Admin / Manager."""
    model = ObjectifSportif
    template_name = 'clients/objectif_sportif_list.html'
    context_object_name = 'objectifs_sportifs'


class ObjectifSportifCreateView(AdminRequiredMixin, CreateView):
    model = ObjectifSportif
    form_class = ObjectifSportifForm
    template_name = 'clients/objectif_sportif_form.html'
    success_url = reverse_lazy('clients:objectif_sportif_list')

    def form_valid(self, form):
        messages.success(self.request, 'Objectif sportif créé avec succès.')
        return super().form_valid(form)


class ObjectifSportifUpdateView(AdminRequiredMixin, UpdateView):
    model = ObjectifSportif
    form_class = ObjectifSportifForm
    template_name = 'clients/objectif_sportif_form.html'
    success_url = reverse_lazy('clients:objectif_sportif_list')

    def form_valid(self, form):
        messages.success(self.request, 'Objectif sportif modifié avec succès.')
        return super().form_valid(form)


class ObjectifSportifDeleteView(AdminRequiredMixin, DeleteView):
    model = ObjectifSportif
    template_name = 'clients/objectif_sportif_confirm_delete.html'
    success_url = reverse_lazy('clients:objectif_sportif_list')

    def form_valid(self, form):
        try:
            messages.success(self.request, 'Objectif sportif supprimé avec succès.')
            return super().form_valid(form)
        except ProtectedError:
            messages.error(
                self.request,
                "Impossible de supprimer cet objectif : des clients y sont déjà rattachés. "
                "Désactivez-le plutôt depuis le formulaire de modification."
            )
            return redirect('clients:objectif_sportif_list')


class QuartierListView(AdminRequiredMixin, ListView):
    """Configuration des quartiers/zones proposés aux clients — Super Admin / Manager."""
    model = Quartier
    template_name = 'clients/quartier_list.html'
    context_object_name = 'quartiers'
    paginate_by = 10


class QuartierCreateView(AdminRequiredMixin, CreateView):
    model = Quartier
    form_class = QuartierForm
    template_name = 'clients/quartier_form.html'
    success_url = reverse_lazy('clients:quartier_list')

    def form_valid(self, form):
        messages.success(self.request, 'Quartier créé avec succès.')
        return super().form_valid(form)


class QuartierUpdateView(AdminRequiredMixin, UpdateView):
    model = Quartier
    form_class = QuartierForm
    template_name = 'clients/quartier_form.html'
    success_url = reverse_lazy('clients:quartier_list')

    def form_valid(self, form):
        messages.success(self.request, 'Quartier modifié avec succès.')
        return super().form_valid(form)


class QuartierDeleteView(AdminRequiredMixin, DeleteView):
    model = Quartier
    template_name = 'clients/quartier_confirm_delete.html'
    success_url = reverse_lazy('clients:quartier_list')

    def form_valid(self, form):
        try:
            messages.success(self.request, 'Quartier supprimé avec succès.')
            return super().form_valid(form)
        except ProtectedError:
            messages.error(
                self.request,
                "Impossible de supprimer ce quartier : des clients y sont déjà rattachés. "
                "Désactivez-le plutôt depuis le formulaire de modification."
            )
            return redirect('clients:quartier_list')
