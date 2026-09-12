from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views import View
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from accounts.exclusao_cascata import excluir_link_em_cascata
from accounts.mixins import AdminOuAdminEmpresaRequiredMixin, EmpresaEscopoMixin
from auditoria.models import AcessoLog

from .forms import LinkBIForm
from .models import LinkBI


class LinkBIListView(LoginRequiredMixin, ListView):
    """Lista os links de BI visíveis para o usuário logado (Admin vê todos)."""

    model = LinkBI
    template_name = "bi_links/link_list.html"
    context_object_name = "links"
    paginate_by = 25

    def get_queryset(self):
        return (
            LinkBI.objects.visible_to(self.request.user)
            .filter(ativo=True)
            .select_related("setor", "setor__empresa")
        )


class LinkBIAcessarView(LoginRequiredMixin, View):
    """Audita o acesso e mostra o link embutido num iframe dentro do próprio
    portal (o usuário não sai do portal nem abre outra aba)."""

    def get(self, request, pk):
        link = get_object_or_404(LinkBI.objects.visible_to(request.user), pk=pk)
        AcessoLog.objects.create(
            usuario=request.user,
            link=link,
            ip_address=request.META.get("REMOTE_ADDR"),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
        )
        return render(request, "bi_links/link_acessar.html", {"link": link})


class LinkBIAdminListView(AdminOuAdminEmpresaRequiredMixin, EmpresaEscopoMixin, ListView):
    model = LinkBI
    template_name = "bi_links/admin_link_list.html"
    context_object_name = "links"
    paginate_by = 25

    def get_queryset(self):
        qs = LinkBI.objects.filter(setor__empresa=self.empresa).select_related("setor")
        setor_id = self.request.GET.get("setor")
        if setor_id:
            qs = qs.filter(setor_id=setor_id)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["empresa"] = self.empresa
        return context


class LinkBICreateView(AdminOuAdminEmpresaRequiredMixin, EmpresaEscopoMixin, CreateView):
    model = LinkBI
    form_class = LinkBIForm
    template_name = "bi_links/link_form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["empresa"] = self.empresa
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["empresa"] = self.empresa
        return context

    def form_valid(self, form):
        form.instance.criado_por = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("bi_links_admin:admin_lista", kwargs={"empresa_id": self.empresa.pk})


class LinkBIUpdateView(AdminOuAdminEmpresaRequiredMixin, EmpresaEscopoMixin, UpdateView):
    model = LinkBI
    form_class = LinkBIForm
    template_name = "bi_links/link_form.html"

    def get_queryset(self):
        return LinkBI.objects.filter(setor__empresa=self.empresa)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["empresa"] = self.empresa
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["empresa"] = self.empresa
        return context

    def get_success_url(self):
        return reverse("bi_links_admin:admin_lista", kwargs={"empresa_id": self.empresa.pk})


class LinkBIDeleteView(AdminOuAdminEmpresaRequiredMixin, EmpresaEscopoMixin, DeleteView):
    """Exclui o LinkBI e o histórico de acesso (AcessoLog) vinculado a ele."""

    model = LinkBI
    template_name = "bi_links/link_confirm_delete.html"

    def get_queryset(self):
        return LinkBI.objects.filter(setor__empresa=self.empresa)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["empresa"] = self.empresa
        return context

    def form_valid(self, form):
        success_url = self.get_success_url()
        nome = str(self.object)
        with transaction.atomic():
            excluir_link_em_cascata(self.object)
        messages.success(self.request, f'Link "{nome}" excluído, junto com seu histórico de acesso.')
        return HttpResponseRedirect(success_url)

    def get_success_url(self):
        return reverse("bi_links_admin:admin_lista", kwargs={"empresa_id": self.empresa.pk})
