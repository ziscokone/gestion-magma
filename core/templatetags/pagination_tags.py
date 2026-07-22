from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def paginate_url(context, page_number, param_name='page'):
    """
    Construit l'URL d'une page en conservant tous les autres paramètres GET
    actifs (recherche, filtres de statut...) — évite qu'un changement de page
    ne réinitialise les filtres en cours.
    """
    request = context['request']
    query = request.GET.copy()
    query[param_name] = page_number
    return '?' + query.urlencode()
