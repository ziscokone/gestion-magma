from django.urls import path
from . import views

app_name = 'budget'

urlpatterns = [
    path('', views.OperationBudgetListView.as_view(), name='operation_list'),
    path('nouvelle/', views.OperationBudgetCreateView.as_view(), name='operation_create'),
    path('<int:pk>/annuler/', views.OperationBudgetAnnulerView.as_view(), name='operation_annuler'),
    path('export/', views.OperationBudgetExportView.as_view(), name='operation_export'),

    path('rapport/', views.RapportOperationsView.as_view(), name='rapport_operations'),
    path('rapport/export/', views.RapportOperationsExportView.as_view(), name='rapport_operations_export'),
    path('bilan/', views.BilanMensuelView.as_view(), name='bilan_mensuel'),

    path('categories/', views.CategorieChargeListView.as_view(), name='categorie_charge_list'),
    path('categories/ajouter/', views.CategorieChargeCreateView.as_view(), name='categorie_charge_create'),
    path('categories/<int:pk>/modifier/', views.CategorieChargeUpdateView.as_view(), name='categorie_charge_update'),
    path('categories/<int:pk>/supprimer/', views.CategorieChargeDeleteView.as_view(), name='categorie_charge_delete'),
]
