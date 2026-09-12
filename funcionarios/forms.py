from django import forms

from accounts.models import Usuario
from empresas.models import Empresa
from setores.models import Setor

from .models import Funcionario

ROLE_CHOICES_GERENCIAVEIS = [
    (Usuario.Role.NORMAL, Usuario.Role.NORMAL.label),
    (Usuario.Role.DIRETOR, Usuario.Role.DIRETOR.label),
    (Usuario.Role.ADMIN_EMPRESA, Usuario.Role.ADMIN_EMPRESA.label),
]


class SetorComEmpresaChoiceField(forms.ModelChoiceField):
    """Setor.__str__ é só o nome (óbvio quando a tela já está escopada numa
    empresa); aqui a lista mistura empresas, então precisa desambiguar."""

    def label_from_instance(self, setor):
        return f"{setor.nome} ({setor.empresa.nome})"


class CadastroUsuarioForm(forms.ModelForm):
    """Cadastro único: cria o Usuario (login) e o Funcionario, já vinculados à
    empresa, ao setor e ao nível (role) escolhidos. Quem pode acessar cada
    link é escolhido no próprio formulário do Link, não aqui. Admin global
    escolhe a empresa no próprio formulário; Admin de Empresa fica travado na
    sua própria empresa."""

    username = forms.CharField(label="Usuário (login)")
    first_name = forms.CharField(label="Nome")
    last_name = forms.CharField(label="Sobrenome", required=False)
    email = forms.EmailField(label="E-mail", required=False)
    password = forms.CharField(label="Senha", widget=forms.PasswordInput)
    role = forms.ChoiceField(label="Nível", choices=ROLE_CHOICES_GERENCIAVEIS)

    class Meta:
        model = Funcionario
        fields = ["setor"]

    def __init__(self, *args, usuario_logado, empresa_id_lock=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["setor"].required = True

        empresa_travada_pela_url = None
        if usuario_logado.is_admin and empresa_id_lock:
            empresa_travada_pela_url = Empresa.objects.filter(pk=empresa_id_lock).first()

        if usuario_logado.is_admin and not empresa_travada_pela_url:
            self.empresa_fixa = None
            self.fields["empresa"] = forms.ModelChoiceField(
                label="Empresa",
                queryset=Empresa.objects.all(),
            )
            self.fields["setor"] = SetorComEmpresaChoiceField(
                label="Setor",
                queryset=Setor.objects.select_related("empresa").all(),
                required=True,
            )
            self.order_fields(
                ["username", "first_name", "last_name", "email", "password", "empresa", "role", "setor"]
            )
        else:
            self.empresa_fixa = (
                empresa_travada_pela_url if usuario_logado.is_admin else usuario_logado.funcionario.empresa
            )
            self.fields["setor"].queryset = Setor.objects.filter(empresa=self.empresa_fixa)

    def clean_username(self):
        username = self.cleaned_data["username"]
        if Usuario.objects.filter(username=username).exists():
            raise forms.ValidationError("Já existe um usuário com esse login.")
        return username

    def clean(self):
        cleaned_data = super().clean()
        empresa = cleaned_data.get("empresa", self.empresa_fixa)
        setor = cleaned_data.get("setor")
        if empresa and setor and setor.empresa_id != empresa.pk:
            self.add_error("setor", "O setor deve pertencer à empresa selecionada.")
        return cleaned_data

    def save(self, commit=True):
        empresa = self.cleaned_data.get("empresa", self.empresa_fixa)

        usuario = Usuario(
            username=self.cleaned_data["username"],
            first_name=self.cleaned_data["first_name"],
            last_name=self.cleaned_data["last_name"],
            email=self.cleaned_data["email"],
            role=self.cleaned_data["role"],
        )
        usuario.set_password(self.cleaned_data["password"])
        usuario.save()

        funcionario = super().save(commit=False)
        funcionario.usuario = usuario
        funcionario.empresa = empresa
        if commit:
            funcionario.save()
        return funcionario


class UsuarioEditForm(forms.ModelForm):
    """Edição de um usuário já cadastrado: dados de perfil, nível e setor. O
    login vem travado (não é editável) e a senha é opcional — só troca se for
    preenchida. A empresa também não é editável aqui (evita reatribuir alguém
    pra outra empresa sem passar pelo fluxo de cadastro)."""

    username = forms.CharField(label="Usuário (login)", disabled=True)
    first_name = forms.CharField(label="Nome")
    last_name = forms.CharField(label="Sobrenome", required=False)
    email = forms.EmailField(label="E-mail", required=False)
    password = forms.CharField(
        label="Nova senha",
        required=False,
        widget=forms.PasswordInput,
        help_text="Deixe em branco para manter a senha atual.",
    )
    role = forms.ChoiceField(label="Nível", choices=ROLE_CHOICES_GERENCIAVEIS)

    class Meta:
        model = Funcionario
        fields = ["setor"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["setor"].required = True
        self.fields["setor"].queryset = Setor.objects.filter(empresa=self.instance.empresa)
        self.fields["username"].initial = self.instance.usuario.username
        self.fields["first_name"].initial = self.instance.usuario.first_name
        self.fields["last_name"].initial = self.instance.usuario.last_name
        self.fields["email"].initial = self.instance.usuario.email
        self.fields["role"].initial = self.instance.usuario.role
        self.order_fields(["username", "first_name", "last_name", "email", "password", "role", "setor"])

    def save(self, commit=True):
        funcionario = super().save(commit=commit)
        usuario = funcionario.usuario
        usuario.first_name = self.cleaned_data["first_name"]
        usuario.last_name = self.cleaned_data["last_name"]
        usuario.email = self.cleaned_data["email"]
        usuario.role = self.cleaned_data["role"]
        update_fields = ["first_name", "last_name", "email", "role"]
        if self.cleaned_data["password"]:
            usuario.set_password(self.cleaned_data["password"])
            update_fields.append("password")
        if commit:
            usuario.save(update_fields=update_fields)
        return funcionario
