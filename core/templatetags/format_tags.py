from django import template

from core.utils import format_duree, format_fcfa

register = template.Library()


@register.filter
def fcfa(value):
    """Formate un montant en FCFA avec séparateur de milliers : 15000 -> '15 000 FCFA'."""
    return format_fcfa(value)


@register.filter
def duree(value):
    """Formate une durée en minutes de façon lisible : 90 -> '1h30'."""
    return format_duree(value)
