from django.urls import path
from . import views

app_name = 'etablissement'

urlpatterns = [
    path('parametres/', views.ParametresView.as_view(), name='parametres'),
]
