from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models.deletion import ProtectedError
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect


class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Somente usuários com role ADMIN podem acessar a view."""

    def test_func(self):
        return self.request.user.is_admin


class DiretorRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """ADMIN ou DIRETOR podem acessar a view (ex.: painel de auditoria)."""

    def test_func(self):
        return self.request.user.is_admin or self.request.user.is_diretor


class AdminOuAdminEmpresaRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """ADMIN (global) ou ADMIN_EMPRESA (da própria empresa) podem acessar a view —
    usado por Usuários, Setores e Links; a checagem fina de QUAL empresa vem do
    `EmpresaEscopoMixin`/`FuncionarioEscopoMixin` na sequência."""

    def test_func(self):
        return self.request.user.is_admin or self.request.user.is_admin_empresa


class EmpresaEscopoMixin:
    """Resolve `self.empresa` a partir de `kwargs['empresa_id']` e garante que o usuário pode
    gerenciar aquela empresa especificamente (ADMIN: qualquer uma; ADMIN_EMPRESA: só a própria).

    Deve vir DEPOIS de um mixin de papel (AdminRequiredMixin/AdminOuAdminEmpresaRequiredMixin)
    na lista de bases da view, para que autenticação e o papel coarse-grained já tenham sido
    validados antes desta checagem fina por empresa (fecha o IDOR de trocar o id na URL).
    """

    def dispatch(self, request, *args, **kwargs):
        from empresas.models import Empresa

        self.empresa = get_object_or_404(Empresa, pk=kwargs["empresa_id"])
        user = request.user
        pode_gerenciar = user.is_admin or (
            user.is_admin_empresa
            and hasattr(user, "funcionario")
            and user.funcionario.empresa_id == self.empresa.pk
        )
        if not pode_gerenciar:
            raise Http404
        return super().dispatch(request, *args, **kwargs)


class FuncionarioEscopoMixin:
    """Restringe o queryset de Funcionario ao que o usuário logado pode gerenciar:
    ADMIN global vê/edita todos; ADMIN_EMPRESA só os da própria empresa (fecha o
    IDOR de acessar/editar/excluir um funcionário de outra empresa pela URL)."""

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if not user.is_admin:
            qs = qs.filter(empresa_id=user.funcionario.empresa_id)
        return qs


class ImpedirExclusaoProtegidaMixin:
    """Em DeleteViews cujo model tem dependentes com `on_delete=PROTECT`, evita que uma
    ProtectedError suba como erro 500: mostra mensagem explicando o que está bloqueando
    e volta para a própria página de confirmação."""

    def form_valid(self, form):
        try:
            return super().form_valid(form)
        except ProtectedError as exc:
            nomes = ", ".join(str(obj) for obj in list(exc.protected_objects)[:5])
            messages.error(
                self.request,
                f'Não é possível excluir "{self.object}": ainda existem registros vinculados a ele ({nomes}). Remova-os primeiro.',
            )
            return redirect(self.request.path)
