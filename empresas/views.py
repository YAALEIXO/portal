from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from accounts.mixins import AdminRequiredMixin, ImpedirExclusaoProtegidaMixin

from bi_links.models import LinkBI

from .forms import EmpresaForm
from .models import Empresa


class EmpresaListView(AdminRequiredMixin, ListView):
    model = Empresa
    template_name = "empresas/empresa_list.html"
    context_object_name = "empresas"
    paginate_by = 25


class EmpresaDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """Hub da empresa: acesso a Setores, Funcionários e Gerenciador de Links dela."""

    model = Empresa
    template_name = "empresas/empresa_detail.html"
    context_object_name = "empresa"

    def test_func(self):
        return self.request.user.is_admin or self.request.user.is_admin_empresa

    def get_queryset(self):
        user = self.request.user
        if user.is_admin:
            return Empresa.objects.all()
        return Empresa.objects.filter(pk=user.funcionario.empresa_id)

    def get_object(self, queryset=None):
        empresa = super().get_object(queryset)
        if self.request.user.is_admin:
            self.request.session["empresa_ativa_id"] = empresa.pk
        return empresa

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        empresa = self.object
        context["total_setores"] = empresa.setores.count()
        context["total_funcionarios"] = empresa.funcionarios.count()
        context["total_links"] = LinkBI.objects.filter(setor__empresa=empresa).count()
        return context


class EmpresaCreateView(AdminRequiredMixin, CreateView):
    model = Empresa
    form_class = EmpresaForm
    template_name = "empresas/empresa_form.html"
    success_url = reverse_lazy("empresas:lista")


class EmpresaUpdateView(AdminRequiredMixin, UpdateView):
    model = Empresa
    form_class = EmpresaForm
    template_name = "empresas/empresa_form.html"
    success_url = reverse_lazy("empresas:lista")


class EmpresaDeleteView(AdminRequiredMixin, ImpedirExclusaoProtegidaMixin, DeleteView):
    model = Empresa
    template_name = "empresas/empresa_confirm_delete.html"
    success_url = reverse_lazy("empresas:lista")
