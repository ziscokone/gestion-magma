from datetime import date, timedelta
from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.db.models.deletion import ProtectedError
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView

from core.mixins import AdminRequiredMixin
from apps.clients.models import Client
from .forms import AbonnementForm, TypeAbonnementForm
from .models import Abonnement, TypeAbonnement
from .pdf import generer_fiche_abonnement_pdf


class AbonnementListView(LoginRequiredMixin, ListView):
    """Journal des abonnements — page d'accueil du module Abonnements."""
    model = Abonnement
    template_name = 'abonnements/abonnement_list.html'
    context_object_name = 'abonnements'
    paginate_by = 15

    def get_queryset(self):
        queryset = Abonnement.objects.select_related('client', 'type_abonnement').all()
        today = date.today()
        statut = self.request.GET.get('statut', 'tous')
        if statut == 'actifs':
            queryset = queryset.filter(date_fin__gte=today)
        elif statut == 'expires':
            queryset = queryset.filter(date_fin__lt=today)
        elif statut == 'expire_bientot':
            queryset = queryset.filter(date_fin__gte=today, date_fin__lte=today + timedelta(days=7))

        search = self.request.GET.get('q')
        if search:
            queryset = queryset.filter(
                Q(client__nom_complet__icontains=search) | Q(client__telephone__icontains=search)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['statut_filtre'] = self.request.GET.get('statut', 'tous')
        context['search_query'] = self.request.GET.get('q', '')
        return context


class AbonnementCreateView(LoginRequiredMixin, View):
    template_name = 'abonnements/abonnement_form.html'

    def _types_info(self):
        return {
            str(t.pk): {'prix': t.prix, 'duree_jours': t.duree_jours}
            for t in TypeAbonnement.objects.filter(actif=True)
        }

    def get(self, request):
        initial = {}
        if 'telephone' in request.GET:
            initial = {
                'telephone': request.GET.get('telephone'),
                'nom_complet': request.GET.get('nom_complet'),
                'type_abonnement': request.GET.get('type_abonnement'),
                'date_debut': request.GET.get('date_debut'),
            }
        form = AbonnementForm(initial=initial)
        return render(request, self.template_name, {
            'form': form, 'types_info': self._types_info(), 'renouvellement': bool(initial),
        })

    def post(self, request):
        form = AbonnementForm(request.POST)
        if form.is_valid():
            telephone = form.cleaned_data['telephone']
            nom_complet = form.cleaned_data['nom_complet']
            client, _ = Client.objects.get_or_create(
                telephone=telephone,
                defaults={'nom_complet': nom_complet}
            )
            type_abonnement = form.cleaned_data['type_abonnement']
            date_debut = form.cleaned_data['date_debut']
            abonnement = Abonnement.objects.create(
                client=client,
                type_abonnement=type_abonnement,
                date_debut=date_debut,
                date_fin=date_debut + timedelta(days=type_abonnement.duree_jours),
                montant=type_abonnement.prix,
                enregistre_par=request.user,
            )

            messages.success(request, f"Abonnement enregistré pour {client.nom_complet}.")
            return redirect('abonnements:abonnement_detail', pk=abonnement.pk)
        return render(request, self.template_name, {'form': form, 'types_info': self._types_info()})


class AbonnementRenewView(LoginRequiredMixin, View):
    """Pré-remplit le formulaire de nouvel abonnement pour un renouvellement."""

    def get(self, request, pk):
        ancien = get_object_or_404(Abonnement, pk=pk)
        today = date.today()
        nouvelle_date_debut = ancien.date_fin if ancien.date_fin >= today else today
        params = urlencode({
            'telephone': ancien.client.telephone,
            'nom_complet': ancien.client.nom_complet,
            'type_abonnement': ancien.type_abonnement_id,
            'date_debut': nouvelle_date_debut.isoformat(),
        })
        return redirect(f"{reverse('abonnements:abonnement_create')}?{params}")


class AbonnementRelanceListView(LoginRequiredMixin, ListView):
    """Liste des abonnements à relancer avant expiration, triée par urgence."""
    model = Abonnement
    template_name = 'abonnements/relance_list.html'
    context_object_name = 'abonnements'
    paginate_by = 15

    def _jours(self):
        try:
            return int(self.request.GET.get('jours', 7))
        except ValueError:
            return 7

    def get_queryset(self):
        jours = self._jours()
        today = date.today()
        queryset = Abonnement.objects.select_related('client', 'type_abonnement').filter(
            date_fin__gte=today, date_fin__lte=today + timedelta(days=jours)
        ).order_by('date_fin')

        relance_filtre = self.request.GET.get('relance', 'a_faire')
        if relance_filtre == 'a_faire':
            queryset = queryset.filter(relance_effectuee=False)
        elif relance_filtre == 'faites':
            queryset = queryset.filter(relance_effectuee=True)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['jours_filtre'] = str(self._jours())
        context['relance_filtre'] = self.request.GET.get('relance', 'a_faire')

        today = date.today()
        jours = self._jours()
        base_qs = Abonnement.objects.filter(date_fin__gte=today, date_fin__lte=today + timedelta(days=jours))
        context['nb_a_relancer'] = base_qs.filter(relance_effectuee=False).count()
        context['nb_relances_faites'] = base_qs.filter(relance_effectuee=True).count()
        return context


class AbonnementRelanceToggleView(LoginRequiredMixin, View):
    """Marque un abonnement comme contacté / non contacté."""

    def post(self, request, pk):
        abonnement = get_object_or_404(Abonnement, pk=pk)
        abonnement.relance_effectuee = not abonnement.relance_effectuee
        abonnement.date_relance = timezone.now() if abonnement.relance_effectuee else None
        abonnement.save(update_fields=['relance_effectuee', 'date_relance'])
        if abonnement.relance_effectuee:
            messages.success(request, f"{abonnement.client.nom_complet} marqué comme contacté.")
        else:
            messages.success(request, f"{abonnement.client.nom_complet} remis en attente de relance.")
        referer = request.META.get('HTTP_REFERER')
        return redirect(referer or 'abonnements:relance_list')


class AbonnementDetailView(LoginRequiredMixin, DetailView):
    model = Abonnement
    template_name = 'abonnements/abonnement_detail.html'
    context_object_name = 'abonnement'


class TypeAbonnementListView(AdminRequiredMixin, ListView):
    """Configuration des types d'abonnement (nom, prix, durée) — Super Admin / Manager."""
    model = TypeAbonnement
    template_name = 'abonnements/type_abonnement_list.html'
    context_object_name = 'types_abonnement'


class TypeAbonnementCreateView(AdminRequiredMixin, CreateView):
    model = TypeAbonnement
    form_class = TypeAbonnementForm
    template_name = 'abonnements/type_abonnement_form.html'
    success_url = reverse_lazy('abonnements:type_abonnement_list')

    def form_valid(self, form):
        messages.success(self.request, "Type d'abonnement créé avec succès.")
        return super().form_valid(form)


class TypeAbonnementUpdateView(AdminRequiredMixin, UpdateView):
    model = TypeAbonnement
    form_class = TypeAbonnementForm
    template_name = 'abonnements/type_abonnement_form.html'
    success_url = reverse_lazy('abonnements:type_abonnement_list')

    def form_valid(self, form):
        messages.success(self.request, "Type d'abonnement modifié avec succès.")
        return super().form_valid(form)


class TypeAbonnementDeleteView(AdminRequiredMixin, DeleteView):
    model = TypeAbonnement
    template_name = 'abonnements/type_abonnement_confirm_delete.html'
    success_url = reverse_lazy('abonnements:type_abonnement_list')

    def form_valid(self, form):
        try:
            messages.success(self.request, "Type d'abonnement supprimé avec succès.")
            return super().form_valid(form)
        except ProtectedError:
            messages.error(
                self.request,
                "Impossible de supprimer ce type : des abonnements y sont déjà rattachés. "
                "Désactivez-le plutôt depuis le formulaire de modification."
            )
            return redirect('abonnements:type_abonnement_list')


class AbonnementFichePDFView(LoginRequiredMixin, View):
    """Reçu PDF de l'abonnement (paiement unique)."""

    def get(self, request, pk):
        abonnement = get_object_or_404(Abonnement, pk=pk)
        buffer = generer_fiche_abonnement_pdf(abonnement)
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="{abonnement.numero_recu}.pdf"'
        return response
