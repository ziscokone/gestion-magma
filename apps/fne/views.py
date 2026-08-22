from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic import ListView

from core.mixins import AdminRequiredMixin

from .models import CertificationFNE
from .services import relancer_certification


class CertificationFNEListView(AdminRequiredMixin, ListView):
    """Journal des certifications FNE — réservé Manager / Super Admin."""
    model = CertificationFNE
    template_name = 'fne/certification_list.html'
    context_object_name = 'certifications'
    paginate_by = 10

    def get_queryset(self):
        queryset = CertificationFNE.objects.select_related('content_type').all()
        statut = self.request.GET.get('statut', 'tous')
        if statut in dict(CertificationFNE.STATUT_CHOICES):
            queryset = queryset.filter(statut=statut)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['statut_filtre'] = self.request.GET.get('statut', 'tous')
        return context


class CertificationFNERelancerView(AdminRequiredMixin, View):
    """Relance manuelle d'une certification en échec, avec le même payload."""

    def post(self, request, pk):
        certification = get_object_or_404(CertificationFNE, pk=pk)
        nouvelle = relancer_certification(certification)
        if nouvelle.statut == 'succes':
            messages.success(request, f"Facture certifiée avec succès (référence {nouvelle.reference_fne}).")
        else:
            messages.error(request, f"Échec de la certification : {nouvelle.erreur_message}")
        return redirect('fne:certification_list')
