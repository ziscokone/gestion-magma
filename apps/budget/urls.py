from django.urls import path
from . import views

app_name = 'budget'

urlpatterns = [
    path('', views.OperationBudgetListView.as_view(), name='operation_list'),
    path('nouvelle/', views.OperationBudgetCreateView.as_view(), name='operation_create'),
    path('<int:pk>/supprimer/', views.OperationBudgetDeleteView.as_view(), name='operation_delete'),
    path('export/', views.OperationBudgetExportView.as_view(), name='operation_export'),

    path('categories/', views.CategorieChargeListView.as_view(), name='categorie_charge_list'),
    path('categories/ajouter/', views.CategorieChargeCreateView.as_view(), name='categorie_charge_create'),
    path('categories/<int:pk>/modifier/', views.CategorieChargeUpdateView.as_view(), name='categorie_charge_update'),
    path('categories/<int:pk>/supprimer/', views.CategorieChargeDeleteView.as_view(), name='categorie_charge_delete'),
]
