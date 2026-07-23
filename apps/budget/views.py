from datetime import date
from io import BytesIO

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill

from core.mixins import AdminRequiredMixin
from .forms import CategorieChargeForm, OperationBudgetForm
from .models import CategorieCharge, OperationBudget


def _operations_filtrees(request):
    """Filtre partagé par la liste et l'export « filtre actif »."""
    queryset = OperationBudget.objects.select_related(
        'categorie_charge', 'seance__client', 'abonnement__client', 'mouvement_stock__produit'
    ).all()
    type_operation = request.GET.get('type', 'tous')
    if type_operation in ('entree', 'sortie'):
        queryset = queryset.filter(type_operation=type_operation)
    categorie = request.GET.get('categorie', 'toutes')
    if categorie != 'toutes':
        queryset = queryset.filter(categorie=categorie)
    return queryset


class OperationBudgetListView(LoginRequiredMixin, ListView):
    """Journal des opérations budgétaires — page d'accueil du module Budget."""
    model = OperationBudget
    template_name = 'budget/operation_list.html'
    context_object_name = 'operations'
    paginate_by = 15

    def get_queryset(self):
        return _operations_filtrees(self.request)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['type_filtre'] = self.request.GET.get('type', 'tous')
        context['categorie_filtre'] = self.request.GET.get('categorie', 'toutes')
        context['categories'] = OperationBudget.CATEGORIE_CHOICES
        context['solde_caisse'] = OperationBudget.solde_caisse()

        today = date.today()
        ops_today = OperationBudget.objects.filter(date__date=today)
        context['recettes_jour'] = sum(o.montant for o in ops_today.filter(type_operation='entree'))
        context['depenses_jour'] = sum(o.montant for o in ops_today.filter(type_operation='sortie'))

        ops_month = OperationBudget.objects.filter(date__year=today.year, date__month=today.month)
        context['recettes_mois'] = sum(o.montant for o in ops_month.filter(type_operation='entree'))
        context['depenses_mois'] = sum(o.montant for o in ops_month.filter(type_operation='sortie'))
        return context


class OperationBudgetCreateView(LoginRequiredMixin, View):
    """Saisie manuelle — uniquement charge/salaire/autre (le reste est automatique)."""
    template_name = 'budget/operation_form.html'

    def get(self, request):
        return render(request, self.template_name, {'form': OperationBudgetForm()})

    def post(self, request):
        form = OperationBudgetForm(request.POST)
        if form.is_valid():
            OperationBudget.objects.create(
                type_operation=form.cleaned_data['type_operation'],
                categorie=form.cleaned_data['categorie'],
                categorie_charge=form.cleaned_data.get('categorie_charge'),
                montant=form.cleaned_data['montant'],
                mode_paiement=form.cleaned_data['mode_paiement'],
                operateur_mobile_money=form.cleaned_data.get('operateur_mobile_money', ''),
                description=form.cleaned_data.get('description', ''),
                enregistre_par=request.user,
            )
            messages.success(request, 'Opération enregistrée avec succès.')
            return redirect('budget:operation_list')
        return render(request, self.template_name, {'form': form})


class OperationBudgetDeleteView(LoginRequiredMixin, View):
    """Suppression réservée aux opérations saisies manuellement."""

    def post(self, request, pk):
        try:
            operation = OperationBudget.objects.get(pk=pk)
        except OperationBudget.DoesNotExist:
            messages.error(request, "Opération introuvable.")
            return redirect('budget:operation_list')

        if operation.est_automatique:
            messages.error(
                request,
                "Cette opération est générée automatiquement depuis une séance, un abonnement "
                "ou un mouvement de stock — corrigez-la à la source plutôt que de la supprimer ici."
            )
        else:
            operation.delete()
            messages.success(request, 'Opération supprimée avec succès.')
        return redirect('budget:operation_list')


class OperationBudgetExportView(LoginRequiredMixin, View):
    """Export Excel du journal des opérations : le filtre actif (GET, lien) ou
    une sélection précise de lignes cochées (POST, formulaire)."""

    ENTETES = ['Date', 'Type', 'Catégorie', 'Sous-catégorie de charge', 'Montant (FCFA)', 'Mode de paiement', 'Description']

    def get(self, request):
        queryset = _operations_filtrees(request).order_by('-date')
        return self._export(queryset, 'operations_budget')

    def post(self, request):
        ids = request.POST.getlist('ids')
        queryset = OperationBudget.objects.select_related('categorie_charge').filter(pk__in=ids).order_by('-date')
        return self._export(queryset, 'operations_budget_selection')

    def _export(self, queryset, nom_fichier):
        classeur = Workbook()
        feuille = classeur.active
        feuille.title = 'Opérations'
        feuille.append(self.ENTETES)
        for cellule in feuille[1]:
            cellule.font = Font(bold=True, color='FFFFFF')
            cellule.fill = PatternFill('solid', fgColor='1E3260')

        for operation in queryset:
            feuille.append([
                timezone.localtime(operation.date).strftime('%d/%m/%Y %H:%M'),
                operation.get_type_operation_display(),
                operation.get_categorie_display(),
                operation.categorie_charge.nom if operation.categorie_charge else '',
                operation.montant,
                operation.mode_paiement_affiche,
                operation.description,
            ])

        for colonne in feuille.columns:
            valeurs = [str(cellule.value) for cellule in colonne if cellule.value is not None]
            largeur = max([len(v) for v in valeurs] + [10]) + 2
            feuille.column_dimensions[colonne[0].column_letter].width = largeur

        buffer = BytesIO()
        classeur.save(buffer)
        buffer.seek(0)
        response = HttpResponse(
            buffer,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )
        horodatage = timezone.now().strftime('%Y%m%d_%H%M')
        response['Content-Disposition'] = f'attachment; filename="{nom_fichier}_{horodatage}.xlsx"'
        return response


class CategorieChargeListView(AdminRequiredMixin, ListView):
    model = CategorieCharge
    template_name = 'budget/categorie_charge_list.html'
    context_object_name = 'categories_charge'


class CategorieChargeCreateView(AdminRequiredMixin, CreateView):
    model = CategorieCharge
    form_class = CategorieChargeForm
    template_name = 'budget/categorie_charge_form.html'
    success_url = reverse_lazy('budget:categorie_charge_list')

    def form_valid(self, form):
        messages.success(self.request, 'Catégorie de charge créée avec succès.')
        return super().form_valid(form)


class CategorieChargeUpdateView(AdminRequiredMixin, UpdateView):
    model = CategorieCharge
    form_class = CategorieChargeForm
    template_name = 'budget/categorie_charge_form.html'
    success_url = reverse_lazy('budget:categorie_charge_list')

    def form_valid(self, form):
        messages.success(self.request, 'Catégorie de charge modifiée avec succès.')
        return super().form_valid(form)


class CategorieChargeDeleteView(AdminRequiredMixin, DeleteView):
    model = CategorieCharge
    template_name = 'budget/categorie_charge_confirm_delete.html'
    success_url = reverse_lazy('budget:categorie_charge_list')

    def form_valid(self, form):
        messages.success(self.request, 'Catégorie de charge supprimée avec succès.')
        return super().form_valid(form)
