from django.urls import path

from . import views

app_name = "funcionarios"

urlpatterns = [
    path("", views.UsuarioListView.as_view(), name="lista"),
    path("novo/", views.CadastroUsuarioView.as_view(), name="cadastrar_usuario"),
    path("<int:pk>/editar/", views.UsuarioUpdateView.as_view(), name="editar"),
    path("<int:pk>/excluir/", views.UsuarioDeleteView.as_view(), name="excluir"),
]
