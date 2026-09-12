from bi_links.models import LinkBI
from empresas.models import Empresa

from .nav import montar_nav, titulo_pagina


def shell_nav(request):
    """Contexto do shell (sidebar/topbar) usado por `templates/base.html`:
    empresa ativa (real pro Admin global via sessão; fixa na própria pro
    Admin de Empresa) e a navegação já filtrada/resolvida pro papel atual."""

    user = getattr(request, "user", None)
    if user is None or not user.is_authenticated:
        return {}

    empresa_ativa = None
    empresas_disponiveis = None

    if user.is_admin:
        empresas_disponiveis = list(Empresa.objects.order_by("nome"))
        empresa_ativa_id = request.session.get("empresa_ativa_id")
        empresa_ativa = next((e for e in empresas_disponiveis if e.pk == empresa_ativa_id), None)
        if empresa_ativa is None and empresas_disponiveis:
            empresa_ativa = empresas_disponiveis[0]
    elif user.is_admin_empresa and hasattr(user, "funcionario"):
        empresa_ativa = user.funcionario.empresa

    grupos_nav = montar_nav(request, empresa_ativa)

    return {
        "empresa_ativa": empresa_ativa,
        "empresas_disponiveis": empresas_disponiveis,
        "grupos_nav": grupos_nav,
        "titulo_pagina_shell": titulo_pagina(grupos_nav),
    }


def sidebar_setores(request):
    """"Meus Links": acesso rápido ao setor/links do próprio usuário. Admin
    global não tem — ele navega pelas empresas via `shell_nav`/`empresa_ativa`."""

    user = getattr(request, "user", None)
    if user is None or not user.is_authenticated or user.is_admin:
        return {}

    if hasattr(user, "funcionario") and user.funcionario.setor:
        setores = [user.funcionario.setor]
    else:
        setores = []

    links_por_setor = {}
    for link in LinkBI.objects.visible_to(user).filter(ativo=True).select_related("setor"):
        links_por_setor.setdefault(link.setor_id, []).append(link)

    for setor in setores:
        setor.links_visiveis = links_por_setor.get(setor.id, [])

    return {"sidebar_setores": setores}
