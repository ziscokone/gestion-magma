def modules_actifs(request):
    """
    Liste des modules actifs, tous rôles confondus — utilisée pour la vitrine
    de la page de connexion (avant authentification, donc pas de filtrage
    par permissions utilisateur comme sur le hub après connexion).
    """
    from apps.comptes.models import Module
    return {'modules_actifs': Module.objects.filter(actif=True).order_by('ordre')}


def active_module(request):
    match = getattr(request, 'resolver_match', None)
    if not match:
        return {'active_module': None}

    app = match.app_name

    if app == 'clients':
        module = 'clients'
    elif app == 'abonnements':
        module = 'abonnements'
    elif app == 'stock':
        module = 'stock'
    elif app == 'budget':
        module = 'budget'
    elif app == 'comptes':
        module = 'comptes'
    else:
        module = None

    return {'active_module': module}
