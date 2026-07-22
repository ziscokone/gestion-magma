from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import render


@login_required
def hub(request):
    from apps.comptes.models import Module
    user = request.user
    if user.is_superuser or user.has_global_access:
        modules = Module.objects.filter(actif=True)
    else:
        modules = user.modules_autorises.filter(actif=True)
    return render(request, 'hub.html', {'modules': modules})


def module_placeholder(request, titre):
    return render(request, 'core/placeholder.html', {'titre': titre})


@login_required
def configuration_hub(request):
    """
    Point d'entrée centralisé (Super Admin / Manager) vers tous les écrans de
    configuration des différents modules (types, catégories...) — pour ne pas
    avoir à naviguer dans chaque module séparément.
    """
    if not (request.user.is_superuser or request.user.has_global_access):
        raise PermissionDenied("Cette page est réservée aux rôles de gestion.")
    return render(request, 'core/configuration_hub.html')
