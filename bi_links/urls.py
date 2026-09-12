from django.urls import path

from . import views

app_name = "bi_links"

urlpatterns = [
    path("", views.LinkBIListView.as_view(), name="lista"),
    path("<int:pk>/acessar/", views.LinkBIAcessarView.as_view(), name="acessar"),
]
