from django.contrib import messages
from django.db import transaction
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from accounts.exclusao_cascata import excluir_setor_em_cascata
from accounts.mixins import AdminOuAdminEmpresaRequiredMixin, EmpresaEscopoMixin

from .forms import SetorForm
from .models import Setor


class SetorListView(AdminOuAdminEmpresaRequiredMixin, EmpresaEscopoMixin, ListView):
    model = Setor
    template_name = "setores/setor_list.html"
    context_object_name = "setores"
    paginate_by = 25

    def get_queryset(self):
        return Setor.objects.filter(empresa=self.empresa)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["empresa"] = self.empresa
        return context


class SetorCreateView(AdminOuAdminEmpresaRequiredMixin, EmpresaEscopoMixin, CreateView):
    model = Setor
    form_class = SetorForm
    template_name = "setores/setor_form.html"

    def form_valid(self, form):
        form.instance.empresa = self.empresa
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["empresa"] = self.empresa
        return context

    def get_success_url(self):
        return reverse("setores:lista", kwargs={"empresa_id": self.empresa.pk})


class SetorUpdateView(AdminOuAdminEmpresaRequiredMixin, EmpresaEscopoMixin, UpdateView):
    model = Setor
    form_class = SetorForm
    template_name = "setores/setor_form.html"

    def get_queryset(self):
        return Setor.objects.filter(empresa=self.empresa)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["empresa"] = self.empresa
        return context

    def get_success_url(self):
        return reverse("setores:lista", kwargs={"empresa_id": self.empresa.pk})


class SetorDeleteView(AdminOuAdminEmpresaRequiredMixin, EmpresaEscopoMixin, DeleteView):
    """Exclui o Setor e tudo que depende dele em cascata: links de BI (com
    seus logs de acesso) e os usuários vinculados ao setor."""

    model = Setor
    template_name = "setores/setor_confirm_delete.html"

    def get_queryset(self):
        return Setor.objects.filter(empresa=self.empresa)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["empresa"] = self.empresa
        return context

    def form_valid(self, form):
        success_url = self.get_success_url()
        nome = str(self.object)
        with transaction.atomic():
            excluir_setor_em_cascata(self.object)
        messages.success(
            self.request,
            f'Setor "{nome}" excluído, junto com seus links de BI e usuários vinculados.',
        )
        return HttpResponseRedirect(success_url)

    def get_success_url(self):
        return reverse("setores:lista", kwargs={"empresa_id": self.empresa.pk})
