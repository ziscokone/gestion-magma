import json

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db.models import Q
from django.db.models.deletion import ProtectedError
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView

from apps.budget.models import OperationBudget
from core.mixins import AdminRequiredMixin
from .forms import (
    AjustementForm, ApprovisionnementForm, CategorieProduitForm, FournisseurForm, ProduitForm, VenteForm,
)
from .models import CategorieProduit, Fournisseur, Produit, MouvementStock, Vente
from .pdf import generer_inventaire_pdf, generer_ticket_vente_pdf

LIBELLES_FILTRE_STOCK = {
    'tous': 'Tous les produits',
    'faible': 'Stock faible',
    'epuise': 'Stock épuisé',
}


def _produits_filtres(request):
    """Filtre partagé par la liste et l'export PDF d'inventaire."""
    queryset = Produit.objects.select_related('categorie').all()
    search = request.GET.get('q')
    categorie = request.GET.get('categorie', 'toutes')
    if search:
        queryset = queryset.filter(nom__icontains=search)
    if categorie != 'toutes':
        queryset = queryset.filter(categorie_id=categorie)

    stock_filtre = request.GET.get('stock', 'tous')
    if stock_filtre == 'epuise':
        queryset = [p for p in queryset if p.stock_actuel <= 0]
    elif stock_filtre == 'faible':
        queryset = [p for p in queryset if 0 < p.stock_actuel <= p.seuil_alerte]
    return queryset


def _produits_info_json():
    """Infos produit (stock, prix) embarquées en JSON pour les rappels en
    direct des formulaires Approvisionnement/Vente — même pattern que les
    prix de prestation/abonnement déjà utilisés ailleurs dans l'app."""
    return {
        str(p.pk): {
            'nom': p.nom,
            'categorie': p.categorie.nom,
            'unite': p.get_unite_display(),
            'stock_actuel': p.stock_actuel,
            'seuil_alerte': p.seuil_alerte,
            'prix_achat': p.prix_achat,
            'prix_vente': p.prix_vente or 0,
        }
        for p in Produit.objects.filter(actif=True).select_related('categorie')
    }


class ProduitListView(LoginRequiredMixin, ListView):
    """Catalogue produits — page d'accueil du module Gestion de Stock."""
    model = Produit
    template_name = 'stock/produit_list.html'
    context_object_name = 'produits'
    paginate_by = 15

    def get_queryset(self):
        return _produits_filtres(self.request)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q', '')
        context['categorie_filtre'] = self.request.GET.get('categorie', 'toutes')
        context['stock_filtre'] = self.request.GET.get('stock', 'tous')
        context['categories'] = CategorieProduit.objects.filter(actif=True)
        tous = Produit.objects.filter(actif=True)
        context['nb_produits'] = tous.count()
        context['nb_stock_faible'] = sum(1 for p in tous if p.stock_faible)
        context['nb_stock_epuise'] = sum(1 for p in tous if p.stock_actuel <= 0)
        context['valeur_totale_stock'] = sum(p.valeur_stock for p in tous)
        return context


class ProduitInventairePDFView(LoginRequiredMixin, View):
    """Export PDF de l'inventaire, respectant les mêmes filtres que la liste."""

    def get(self, request):
        produits = list(_produits_filtres(request))

        stock_filtre = request.GET.get('stock', 'tous')
        libelle = LIBELLES_FILTRE_STOCK.get(stock_filtre, 'Tous les produits')
        categorie_id = request.GET.get('categorie', 'toutes')
        if categorie_id != 'toutes':
            categorie = CategorieProduit.objects.filter(pk=categorie_id).first()
            if categorie:
                libelle += f" — {categorie.nom}"

        buffer = generer_inventaire_pdf(produits, libelle)
        response = HttpResponse(buffer, content_type='application/pdf')
        horodatage = timezone.now().strftime('%Y%m%d_%H%M')
        response['Content-Disposition'] = f'inline; filename="inventaire_{horodatage}.pdf"'
        return response


class ProduitCreateView(AdminRequiredMixin, CreateView):
    model = Produit
    form_class = ProduitForm
    template_name = 'stock/produit_form.html'
    success_url = reverse_lazy('stock:produit_list')

    def form_valid(self, form):
        messages.success(self.request, 'Produit créé avec succès.')
        return super().form_valid(form)


class ProduitUpdateView(AdminRequiredMixin, UpdateView):
    model = Produit
    form_class = ProduitForm
    template_name = 'stock/produit_form.html'
    success_url = reverse_lazy('stock:produit_list')

    def form_valid(self, form):
        messages.success(self.request, 'Produit modifié avec succès.')
        return super().form_valid(form)


class ProduitDeleteView(AdminRequiredMixin, DeleteView):
    model = Produit
    template_name = 'stock/produit_confirm_delete.html'
    success_url = reverse_lazy('stock:produit_list')

    def form_valid(self, form):
        try:
            messages.success(self.request, 'Produit supprimé avec succès.')
            return super().form_valid(form)
        except ProtectedError:
            messages.error(
                self.request,
                "Impossible de supprimer ce produit : des mouvements de stock y sont déjà rattachés. "
                "Désactivez-le plutôt depuis le formulaire de modification."
            )
            return redirect('stock:produit_list')


class ProduitDetailView(LoginRequiredMixin, DetailView):
    model = Produit
    template_name = 'stock/produit_detail.html'
    context_object_name = 'produit'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        mouvements_qs = self.object.mouvements.select_related('fournisseur').all()
        paginator = Paginator(mouvements_qs, 10)
        context['mouvements'] = paginator.get_page(self.request.GET.get('page', 1))
        return context


class MouvementListView(LoginRequiredMixin, ListView):
    """Journal des mouvements de stock (entrées/sorties)."""
    model = MouvementStock
    template_name = 'stock/mouvement_list.html'
    context_object_name = 'mouvements'
    paginate_by = 15

    def get_queryset(self):
        queryset = MouvementStock.objects.select_related('produit', 'fournisseur').all()
        type_mouvement = self.request.GET.get('type', 'tous')
        if type_mouvement in ('entree', 'sortie'):
            queryset = queryset.filter(type_mouvement=type_mouvement)
        search = self.request.GET.get('q')
        if search:
            queryset = queryset.filter(produit__nom__icontains=search)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['type_filtre'] = self.request.GET.get('type', 'tous')
        context['search_query'] = self.request.GET.get('q', '')
        return context


class ApprovisionnementCreateView(LoginRequiredMixin, View):
    """Entrée de stock — achat auprès d'un fournisseur."""
    template_name = 'stock/approvisionnement_form.html'

    def get(self, request):
        initial = {}
        if request.GET.get('produit'):
            initial['produit'] = request.GET['produit']
        return render(request, self.template_name, {
            'form': ApprovisionnementForm(initial=initial),
            'produits_info': _produits_info_json(),
        })

    def post(self, request):
        form = ApprovisionnementForm(request.POST)
        if form.is_valid():
            produit = form.cleaned_data['produit']
            MouvementStock.objects.create(
                produit=produit,
                type_mouvement='entree',
                quantite=form.cleaned_data['quantite'],
                prix_unitaire=form.cleaned_data['prix_unitaire'],
                fournisseur=form.cleaned_data.get('fournisseur'),
                date_peremption=form.cleaned_data.get('date_peremption'),
                mode_paiement=form.cleaned_data['mode_paiement'],
                operateur_mobile_money=form.cleaned_data.get('operateur_mobile_money', ''),
                enregistre_par=request.user,
            )
            messages.success(request, f"Approvisionnement enregistré pour {produit.nom}.")
            return redirect('stock:mouvement_list')
        return render(request, self.template_name, {
            'form': form,
            'produits_info': _produits_info_json(),
        })


class VenteCreateView(LoginRequiredMixin, View):
    """Sortie de stock — vente au client, l'écran le plus utilisé du module.
    Le panier (plusieurs produits possibles) est constitué en JS et soumis
    en une seule fois via le champ caché `lignes_json`."""
    template_name = 'stock/vente_form.html'

    def get(self, request):
        initial = {}
        if request.GET.get('produit'):
            initial['produit'] = request.GET['produit']
        return render(request, self.template_name, {
            'form': VenteForm(initial=initial),
            'produits_info': _produits_info_json(),
        })

    def post(self, request):
        form = VenteForm(request.POST)
        lignes_panier, erreur_panier = self._parser_panier(request.POST.get('lignes_json', ''))

        if erreur_panier:
            messages.error(request, erreur_panier)
        if form.is_valid() and not erreur_panier:
            vente = Vente.objects.create(
                mode_paiement=form.cleaned_data['mode_paiement'],
                operateur_mobile_money=form.cleaned_data.get('operateur_mobile_money', ''),
                enregistre_par=request.user,
            )
            for produit, quantite, prix_unitaire in lignes_panier:
                MouvementStock.objects.create(
                    produit=produit,
                    type_mouvement='sortie',
                    motif='vente',
                    quantite=quantite,
                    prix_unitaire=prix_unitaire,
                    mode_paiement=vente.mode_paiement,
                    operateur_mobile_money=vente.operateur_mobile_money,
                    vente=vente,
                    enregistre_par=request.user,
                )
            OperationBudget.objects.create(
                type_operation='entree',
                categorie='vente_produit',
                montant=vente.montant_total,
                mode_paiement=vente.mode_paiement,
                operateur_mobile_money=vente.operateur_mobile_money,
                vente=vente,
                enregistre_par=request.user,
            )
            return redirect('stock:vente_confirmation', pk=vente.pk)

        return render(request, self.template_name, {
            'form': form,
            'produits_info': _produits_info_json(),
        })

    @staticmethod
    def _parser_panier(brut):
        """Valide le panier soumis en JSON : renvoie (lignes, message_erreur).
        `lignes` est une liste de tuples (produit, quantite, prix_unitaire),
        avec les quantités du même produit déjà fusionnées côté JS."""
        try:
            lignes_json = json.loads(brut) if brut else []
        except (ValueError, TypeError):
            return [], "Panier invalide — merci de réessayer."

        if not lignes_json:
            return [], "Ajoutez au moins un produit au panier avant de valider la vente."

        lignes = []
        for ligne in lignes_json:
            try:
                produit = Produit.objects.get(pk=ligne['produit_id'], actif=True)
                quantite = int(ligne['quantite'])
                prix_unitaire = int(ligne['prix_unitaire'])
            except (Produit.DoesNotExist, KeyError, TypeError, ValueError):
                return [], "Panier invalide — merci de réessayer."

            if quantite < 1:
                return [], f"Quantité invalide pour {produit.nom}."
            if quantite > produit.stock_actuel:
                return [], (
                    f"Stock insuffisant pour {produit.nom} : il ne reste que "
                    f"{produit.stock_actuel} {produit.get_unite_display().lower()}(s)."
                )
            lignes.append((produit, quantite, prix_unitaire))
        return lignes, None


class VenteConfirmationView(LoginRequiredMixin, DetailView):
    """Écran de confirmation après une vente : récap du panier + accès au ticket PDF."""
    model = Vente
    template_name = 'stock/vente_confirmation.html'
    context_object_name = 'vente'


class AjustementCreateView(LoginRequiredMixin, View):
    """Sortie de stock hors vente (casse/perte, usage interne)."""
    template_name = 'stock/ajustement_form.html'

    def get(self, request):
        return render(request, self.template_name, {'form': AjustementForm()})

    def post(self, request):
        form = AjustementForm(request.POST)
        if form.is_valid():
            produit = form.cleaned_data['produit']
            MouvementStock.objects.create(
                produit=produit,
                type_mouvement='sortie',
                motif=form.cleaned_data['motif'],
                quantite=form.cleaned_data['quantite'],
                prix_unitaire=0,
                enregistre_par=request.user,
            )
            messages.success(request, f"Sortie de stock enregistrée pour {produit.nom}.")
            return redirect('stock:mouvement_list')
        return render(request, self.template_name, {'form': form})


class VenteTicketPDFView(LoginRequiredMixin, View):
    def get(self, request, pk):
        vente = get_object_or_404(Vente, pk=pk)
        buffer = generer_ticket_vente_pdf(vente)
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="{vente.numero_vente}.pdf"'
        return response


class FournisseurListView(LoginRequiredMixin, ListView):
    model = Fournisseur
    template_name = 'stock/fournisseur_list.html'
    context_object_name = 'fournisseurs'
    paginate_by = 15

    def get_queryset(self):
        queryset = Fournisseur.objects.all()
        search = self.request.GET.get('q')
        if search:
            queryset = queryset.filter(Q(nom__icontains=search) | Q(telephone__icontains=search))
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q', '')
        return context


class FournisseurCreateView(AdminRequiredMixin, CreateView):
    model = Fournisseur
    form_class = FournisseurForm
    template_name = 'stock/fournisseur_form.html'
    success_url = reverse_lazy('stock:fournisseur_list')

    def form_valid(self, form):
        messages.success(self.request, 'Fournisseur créé avec succès.')
        return super().form_valid(form)


class FournisseurUpdateView(AdminRequiredMixin, UpdateView):
    model = Fournisseur
    form_class = FournisseurForm
    template_name = 'stock/fournisseur_form.html'
    success_url = reverse_lazy('stock:fournisseur_list')

    def form_valid(self, form):
        messages.success(self.request, 'Fournisseur modifié avec succès.')
        return super().form_valid(form)


class FournisseurDeleteView(AdminRequiredMixin, DeleteView):
    model = Fournisseur
    template_name = 'stock/fournisseur_confirm_delete.html'
    success_url = reverse_lazy('stock:fournisseur_list')

    def form_valid(self, form):
        messages.success(self.request, 'Fournisseur supprimé avec succès.')
        return super().form_valid(form)


class CategorieProduitListView(AdminRequiredMixin, ListView):
    model = CategorieProduit
    template_name = 'stock/categorie_produit_list.html'
    context_object_name = 'categories_produit'


class CategorieProduitCreateView(AdminRequiredMixin, CreateView):
    model = CategorieProduit
    form_class = CategorieProduitForm
    template_name = 'stock/categorie_produit_form.html'
    success_url = reverse_lazy('stock:categorie_produit_list')

    def form_valid(self, form):
        messages.success(self.request, 'Catégorie de produit créée avec succès.')
        return super().form_valid(form)


class CategorieProduitUpdateView(AdminRequiredMixin, UpdateView):
    model = CategorieProduit
    form_class = CategorieProduitForm
    template_name = 'stock/categorie_produit_form.html'
    success_url = reverse_lazy('stock:categorie_produit_list')

    def form_valid(self, form):
        messages.success(self.request, 'Catégorie de produit modifiée avec succès.')
        return super().form_valid(form)


class CategorieProduitDeleteView(AdminRequiredMixin, DeleteView):
    model = CategorieProduit
    template_name = 'stock/categorie_produit_confirm_delete.html'
    success_url = reverse_lazy('stock:categorie_produit_list')

    def form_valid(self, form):
        try:
            messages.success(self.request, 'Catégorie de produit supprimée avec succès.')
            return super().form_valid(form)
        except ProtectedError:
            messages.error(
                self.request,
                "Impossible de supprimer cette catégorie : des produits y sont déjà rattachés. "
                "Désactivez-la plutôt depuis le formulaire de modification."
            )
            return redirect('stock:categorie_produit_list')
