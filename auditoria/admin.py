from django.contrib import admin

from .models import AcessoLog


@admin.register(AcessoLog)
class AcessoLogAdmin(admin.ModelAdmin):
    list_display = ("usuario", "link", "acessado_em", "ip_address")
    list_filter = ("link__setor__empresa",)
    search_fields = ("usuario__username", "link__nome")
    readonly_fields = [f.name for f in AcessoLog._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
