from django.urls import path

from . import views

app_name = 'fne'

urlpatterns = [
    path('', views.CertificationFNEListView.as_view(), name='certification_list'),
    path('<int:pk>/relancer/', views.CertificationFNERelancerView.as_view(), name='certification_relancer'),
]
