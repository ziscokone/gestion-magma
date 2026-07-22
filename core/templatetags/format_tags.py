from django import template

from core.utils import format_fcfa

register = template.Library()


@register.filter
def fcfa(value):
    """Formate un montant en FCFA avec séparateur de milliers : 15000 -> '15 000 FCFA'."""
    return format_fcfa(value)
