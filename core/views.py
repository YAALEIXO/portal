from datetime import timedelta

from django.db.models import Count
from django.shortcuts import render
from django.utils import timezone
from django.views.generic import TemplateView

from accounts.models import Usuario
from auditoria.models import AcessoLog
from bi_links.models import LinkBI
from empresas.models import Empresa
from funcionarios.models import Funcionario

MINUTOS_PARA_CONSIDERAR_ONLINE = 5


class DashboardView(TemplateView):
    """Em `/`: visitante não autenticado vê a landing page pública;
    usuário autenticado vê um dashboard diferente por papel:
    - Admin global: visão consolidada de todas as empresas (`_painel_admin`).
    - Admin de Empresa e Diretor: "Indicadores de Alerta" da própria empresa
      (`_indicadores_empresa`).
    - Demais: lista simples dos próprios links de BI."""

    template_name = "core/dashboard.html"

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return render(request, "core/landing.html")
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        if user.is_admin:
            context["mostrar_painel_admin"] = True
            context.update(self._painel_admin())
            return context

        context["mostrar_indicadores"] = user.is_admin_empresa or user.is_diretor

        if not context["mostrar_indicadores"]:
            context["meus_links"] = (
                LinkBI.objects.visible_to(user).filter(ativo=True).select_related("setor")
            )
            return context

        context.update(self._indicadores_empresa(user))
        return context

    def _painel_admin(self):
        links_por_empresa = list(
            LinkBI.objects.values("setor__empresa__nome")
            .annotate(total=Count("id"))
            .order_by("-total")
        )
        return {
            "total_empresas": Empresa.objects.count(),
            "total_usuarios": Funcionario.objects.count(),
            "total_links": LinkBI.objects.count(),
            "links_por_empresa": links_por_empresa,
        }

    def _indicadores_empresa(self, user):
        agora = timezone.now()
        cutoff_online = agora - timedelta(minutes=MINUTOS_PARA_CONSIDERAR_ONLINE)
        cutoff_24h = agora - timedelta(hours=24)

        links_visiveis = LinkBI.objects.visible_to(user).filter(ativo=True)
        acessos_visiveis = AcessoLog.objects.visible_to(user)

        usuarios_online = Usuario.objects.filter(
            last_seen__gte=cutoff_online,
            funcionario__empresa=user.funcionario.empresa,
        ).count()

        ranking_setores = list(
            acessos_visiveis.values("link__setor__nome")
            .annotate(total=Count("id"))
            .order_by("-total")[:10]
        )
        top_links = list(
            acessos_visiveis.values("link__nome")
            .annotate(total=Count("id"))
            .order_by("-total")[:10]
        )
        frequencia = []
        for i in range(6, -1, -1):
            dia = (agora - timedelta(days=i)).date()
            total = acessos_visiveis.filter(acessado_em__date=dia).count()
            frequencia.append({"dia": dia.strftime("%d/%m"), "total": total})

        return {
            "total_links_ativos": links_visiveis.count(),
            "total_setores": links_visiveis.values("setor").distinct().count(),
            "usuarios_online": usuarios_online,
            "conexoes_recentes": acessos_visiveis.filter(acessado_em__gte=cutoff_24h).count(),
            "ranking_setores": ranking_setores,
            "top_links": top_links,
            "frequencia": frequencia,
        }
