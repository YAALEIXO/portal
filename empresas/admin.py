from django.contrib import admin

from funcionarios.models import Funcionario
from setores.models import Setor

from .models import Empresa


class SetorInline(admin.TabularInline):
    model = Setor
    fields = ("nome",)
    extra = 1


class FuncionarioInline(admin.TabularInline):
    """Somente leitura: criação/edição de Funcionário passa pelo fluxo próprio
    (cria também o Usuario/login), não pelo inline genérico do admin."""

    model = Funcionario
    fields = ("usuario", "setor")
    readonly_fields = ("usuario", "setor")
    extra = 0
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ("nome", "cnpj", "ativo", "criado_em")
    list_filter = ("ativo",)
    search_fields = ("nome", "cnpj")
    inlines = [SetorInline, FuncionarioInline]
