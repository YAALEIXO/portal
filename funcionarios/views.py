from django.contrib import messages
from django.db import transaction
from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from accounts.exclusao_cascata import excluir_usuario_em_cascata
from accounts.mixins import AdminOuAdminEmpresaRequiredMixin, FuncionarioEscopoMixin
from empresas.models import Empresa

from .forms import CadastroUsuarioForm, UsuarioEditForm
from .models import Funcionario


class UsuarioListView(AdminOuAdminEmpresaRequiredMixin, FuncionarioEscopoMixin, ListView):
    """Admin global vê os usuários de todas as empresas; Admin de Empresa só os
    da própria empresa."""

    queryset = Funcionario.objects.select_related("usuario", "empresa", "setor")
    template_name = "funcionarios/usuario_list.html"
    context_object_name = "funcionarios"
    paginate_by = 25


class CadastroUsuarioView(AdminOuAdminEmpresaRequiredMixin, CreateView):
    """Cadastro de novo usuário já vinculado a uma empresa e a um nível (role).
    Acessível pelo Admin global (escolhe a empresa no formulário, ou já vem
    travado quando chega pelo botão "Cadastrar usuário" do hub de uma
    empresa, via ?empresa_id_lock=) e pelo Admin de Empresa (sempre travado
    na própria empresa)."""

    model = Funcionario
    form_class = CadastroUsuarioForm
    template_name = "funcionarios/cadastro_usuario_form.html"

    def get_empresa_id_lock(self):
        return self.request.GET.get("empresa_id_lock") or self.request.POST.get("empresa_id_lock")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["usuario_logado"] = self.request.user
        kwargs["empresa_id_lock"] = self.get_empresa_id_lock()
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        empresa_id_lock = self.get_empresa_id_lock()
        if self.request.user.is_admin and empresa_id_lock:
            context["empresa_locked"] = Empresa.objects.filter(pk=empresa_id_lock).first()
        return context

    def get_success_url(self):
        empresa_locked = self.object.empresa
        if self.request.user.is_admin and str(empresa_locked.pk) == (self.get_empresa_id_lock() or ""):
            return reverse("empresas:detalhe", args=[empresa_locked.pk])
        return reverse("funcionarios:lista")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Usuário "{self.object.usuario}" cadastrado com sucesso.')
        return response


class UsuarioUpdateView(AdminOuAdminEmpresaRequiredMixin, FuncionarioEscopoMixin, UpdateView):
    queryset = Funcionario.objects.select_related("usuario", "empresa")
    form_class = UsuarioEditForm
    template_name = "funcionarios/usuario_form.html"
    success_url = reverse_lazy("funcionarios:lista")


class UsuarioDeleteView(AdminOuAdminEmpresaRequiredMixin, FuncionarioEscopoMixin, DeleteView):
    """Exclui o Usuario (e o Funcionario junto, via FK CASCADE) em cascata com
    tudo que depende dele: links de BI que criou (e o log de acesso desses
    links) e seu próprio histórico de acesso."""

    queryset = Funcionario.objects.select_related("usuario", "empresa")
    template_name = "funcionarios/usuario_confirm_delete.html"
    success_url = reverse_lazy("funcionarios:lista")

    def form_valid(self, form):
        usuario = self.object.usuario
        nome = str(usuario)
        with transaction.atomic():
            excluir_usuario_em_cascata(usuario)
        messages.success(
            self.request,
            f'Usuário "{nome}" excluído, junto com os links que criou e seu histórico de acesso.',
        )
        return HttpResponseRedirect(self.success_url)
