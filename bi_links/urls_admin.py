from django.urls import path

from . import views

app_name = "bi_links_admin"

urlpatterns = [
    path("", views.LinkBIAdminListView.as_view(), name="admin_lista"),
    path("novo/", views.LinkBICreateView.as_view(), name="criar"),
    path("<int:pk>/editar/", views.LinkBIUpdateView.as_view(), name="editar"),
    path("<int:pk>/excluir/", views.LinkBIDeleteView.as_view(), name="excluir"),
]
