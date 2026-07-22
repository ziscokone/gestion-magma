from .models import Etablissement


def etablissement_context(request):
    return {'etablissement': Etablissement.get_instance()}
