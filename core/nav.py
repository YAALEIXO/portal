"""Config da navegação da sidebar/topbar do shell interno (`templates/base.html`).

Cada item aponta pra uma página real do sistema — nada de itens sem destino.
O item "ativo" (e o título mostrado na topbar) é resolvido comparando o
namespace da URL atual com o namespace do item, então nenhuma das páginas de
conteúdo precisa saber nada sobre isso.
"""

from dataclasses import dataclass
from typing import Callable, Optional

from django.urls import NoReverseMatch, reverse


@dataclass
class NavItem:
    label: str
    icone: str
    view_name: str
    roles: Optional[tuple] = None  # None = visível pra qualquer usuário autenticado
    kwargs_fn: Optional[Callable] = None  # (empresa_ativa) -> dict de kwargs pro reverse()

    @property
    def namespace(self):
        return self.view_name.split(":")[0]

    def visivel_para(self, user):
        if self.roles is None:
            return True
        return any(getattr(user, role, False) for role in self.roles)

    def resolver_url(self, empresa_ativa):
        kwargs = self.kwargs_fn(empresa_ativa) if self.kwargs_fn else {}
        if kwargs is None:
            return None
        try:
            return reverse(self.view_name, kwargs=kwargs)
        except NoReverseMatch:
            return None


GRUPOS = [
    {
        "titulo": "Painéis",
        "itens": [
            NavItem("Visão geral", "bi-grid-1x2", "core:home"),
        ],
    },
    {
        "titulo": "Administração",
        "itens": [
            NavItem(
                "Usuários", "bi-people", "funcionarios:lista",
                roles=("is_admin", "is_admin_empresa"),
            ),
            NavItem(
                "Empresas", "bi-building", "empresas:lista",
                roles=("is_admin",),
            ),
            NavItem(
                "Setores", "bi-diagram-3", "setores:lista",
                roles=("is_admin", "is_admin_empresa"),
                kwargs_fn=lambda empresa: {"empresa_id": empresa.pk} if empresa else None,
            ),
            NavItem(
                "Links de BI", "bi-link-45deg", "bi_links_admin:admin_lista",
                roles=("is_admin", "is_admin_empresa"),
                kwargs_fn=lambda empresa: {"empresa_id": empresa.pk} if empresa else None,
            ),
        ],
    },
    {
        "titulo": "Sistema",
        "itens": [
            NavItem(
                "Auditoria", "bi-shield-check", "auditoria:lista",
                roles=("is_admin", "is_diretor"),
            ),
        ],
    },
]


def montar_nav(request, empresa_ativa):
    """Monta os grupos de navegação já filtrados pro usuário logado, com o
    item ativo marcado. Grupos sem nenhum item visível/resolvível somem."""

    user = request.user
    resolver_match = request.resolver_match
    namespace_atual = resolver_match.namespace if resolver_match else None

    grupos_render = []
    for grupo in GRUPOS:
        itens_render = []
        for item in grupo["itens"]:
            if not item.visivel_para(user):
                continue
            url = item.resolver_url(empresa_ativa)
            if url is None:
                continue
            itens_render.append(
                {
                    "label": item.label,
                    "icone": item.icone,
                    "url": url,
                    "ativo": namespace_atual == item.namespace,
                }
            )
        if itens_render:
            grupos_render.append({"titulo": grupo["titulo"], "itens": itens_render})
    return grupos_render


def titulo_pagina(grupos_nav, padrao="Portal Axion"):
    for grupo in grupos_nav:
        for item in grupo["itens"]:
            if item["ativo"]:
                return item["label"]
    return padrao
