from django import forms

from core.forms import checklist_dropdown_widget, status_field
from funcionarios.models import Funcionario
from setores.models import Setor

from .models import LinkBI


class FuncionarioMultipleChoiceField(forms.ModelMultipleChoiceField):
    """Mostra o setor do usuário junto do nome, já que a lista mistura vários
    setores da empresa (a liberação só é válida dentro do setor do link)."""

    def label_from_instance(self, funcionario):
        setor = funcionario.setor.nome if funcionario.setor else "sem setor"
        return f"{funcionario.usuario} ({setor})"


class LinkBIForm(forms.ModelForm):
    ativo = status_field(label="Situação", ativado="Ativado", desativado="Desativado")
    usuarios_liberados = FuncionarioMultipleChoiceField(
        label="Quem pode acessar",
        queryset=Funcionario.objects.none(),
        widget=checklist_dropdown_widget(),
        required=False,
    )

    class Meta:
        model = LinkBI
        fields = ["setor", "nome", "url", "ativo"]

    def __init__(self, *args, empresa, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["setor"].queryset = Setor.objects.filter(empresa=empresa)
        self.fields["usuarios_liberados"].queryset = Funcionario.objects.filter(
            empresa=empresa
        ).select_related("usuario", "setor")
        if self.instance.pk:
            self.fields["usuarios_liberados"].initial = self.instance.funcionarios_liberados.all()

    def clean(self):
        cleaned_data = super().clean()
        setor = cleaned_data.get("setor")
        usuarios = cleaned_data.get("usuarios_liberados")
        if setor and usuarios and usuarios.exclude(setor=setor).exists():
            self.add_error(
                "usuarios_liberados", "Só é possível liberar para usuários do setor escolhido."
            )
        return cleaned_data

    def save(self, commit=True):
        link = super().save(commit=False)
        if commit:
            link.save()
            link.funcionarios_liberados.set(self.cleaned_data.get("usuarios_liberados") or [])
        return link
