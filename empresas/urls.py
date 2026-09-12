from django.urls import path

from . import views

app_name = "empresas"

urlpatterns = [
    path("", views.EmpresaListView.as_view(), name="lista"),
    path("nova/", views.EmpresaCreateView.as_view(), name="criar"),
    path("<int:pk>/", views.EmpresaDetailView.as_view(), name="detalhe"),
    path("<int:pk>/editar/", views.EmpresaUpdateView.as_view(), name="editar"),
    path("<int:pk>/excluir/", views.EmpresaDeleteView.as_view(), name="excluir"),
]
