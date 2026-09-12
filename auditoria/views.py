from django.views.generic import ListView

from accounts.mixins import DiretorRequiredMixin

from .models import AcessoLog


class AcessoLogListView(DiretorRequiredMixin, ListView):
    model = AcessoLog
    template_name = "auditoria/acessolog_list.html"
    context_object_name = "acessos"
    paginate_by = 50

    def get_queryset(self):
        qs = AcessoLog.objects.visible_to(self.request.user).select_related(
            "usuario", "link", "link__setor"
        )
        funcionario_id = self.request.GET.get("funcionario")
        link_id = self.request.GET.get("link")
        if funcionario_id:
            qs = qs.filter(usuario_id=funcionario_id)
        if link_id:
            qs = qs.filter(link_id=link_id)
        return qs
