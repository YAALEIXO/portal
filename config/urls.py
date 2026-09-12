from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("core.urls")),
    path("accounts/", include("accounts.urls")),
    path("empresas/", include("empresas.urls")),
    path("empresas/<int:empresa_id>/setores/", include("setores.urls")),
    path("empresas/<int:empresa_id>/links/", include("bi_links.urls_admin")),
    path("usuarios/", include("funcionarios.urls")),
    path("links/", include("bi_links.urls")),
    path("auditoria/", include("auditoria.urls")),
]
