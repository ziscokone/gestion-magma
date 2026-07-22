import os
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from core.views import hub, configuration_hub

ADMIN_URL = os.environ.get('ADMIN_URL', 'magma-admin-panel/')

urlpatterns = [
    path(ADMIN_URL, admin.site.urls),
    path('', RedirectView.as_view(pattern_name='hub', permanent=False)),
    path('hub/', hub, name='hub'),
    path('configuration/', configuration_hub, name='configuration_hub'),
    path('', include('apps.comptes.urls')),
    path('clients/', include('apps.clients.urls')),
    path('abonnements/', include('apps.abonnements.urls')),
    path('stock/', include('apps.stock.urls')),
    path('budget/', include('apps.budget.urls')),
    path('etablissement/', include('apps.etablissement.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
