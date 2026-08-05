from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver


@receiver(user_logged_in)
def marquer_ecran_chargement(sender, request, user, **kwargs):
    """Déclenche l'écran de chargement une seule fois, juste après la connexion."""
    request.session['afficher_ecran_chargement'] = True
