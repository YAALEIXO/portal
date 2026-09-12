from django.urls import path

from . import views

app_name = "setores"

urlpatterns = [
    path("", views.SetorListView.as_view(), name="lista"),
    path("novo/", views.SetorCreateView.as_view(), name="criar"),
    path("<int:pk>/editar/", views.SetorUpdateView.as_view(), name="editar"),
    path("<int:pk>/excluir/", views.SetorDeleteView.as_view(), name="excluir"),
]
