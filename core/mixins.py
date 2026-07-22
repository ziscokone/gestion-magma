"""
Mixins personnalisés pour les vues.
"""
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied


class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin qui requiert que l'utilisateur soit Super Admin ou Manager.
    Utilisé pour les actions de gestion courantes (utilisateurs, modules...).
    """

    def test_func(self):
        return self.request.user.has_global_access

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            raise PermissionDenied("Vous n'avez pas les droits nécessaires pour accéder à cette page.")
        return super().handle_no_permission()


class SuperAdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin réservé exclusivement au Super Administrateur.
    Utilisé pour les actions destructives (suppression d'utilisateur) et les
    paramètres globaux de l'établissement, que le Manager ne peut pas toucher.
    """

    def test_func(self):
        return self.request.user.is_superuser or self.request.user.role == 'super_admin'

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            raise PermissionDenied("Cette action est réservée au Super Administrateur.")
        return super().handle_no_permission()
