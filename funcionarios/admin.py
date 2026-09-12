from django.contrib import admin

from .models import Funcionario


@admin.register(Funcionario)
class FuncionarioAdmin(admin.ModelAdmin):
    list_display = ("usuario", "empresa", "setor")
    list_filter = ("empresa", "setor")
    search_fields = ("usuario__username", "usuario__first_name", "usuario__last_name")
    filter_horizontal = ("links_liberados",)
