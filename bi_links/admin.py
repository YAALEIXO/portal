from django.contrib import admin

from .models import LinkBI


@admin.register(LinkBI)
class LinkBIAdmin(admin.ModelAdmin):
    list_display = ("nome", "setor", "ativo", "criado_por", "criado_em")
    list_filter = ("setor__empresa", "setor", "ativo")
    search_fields = ("nome", "setor__nome")

    def save_model(self, request, obj, form, change):
        if not change:
            obj.criado_por = request.user
        super().save_model(request, obj, form, change)
