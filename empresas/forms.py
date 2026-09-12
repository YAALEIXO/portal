from django import forms

from core.forms import status_field

from .models import Empresa


class EmpresaForm(forms.ModelForm):
    ativo = status_field(label="Status", ativado="Ativada", desativado="Não ativada")

    class Meta:
        model = Empresa
        fields = ["nome", "cnpj", "ativo"]
