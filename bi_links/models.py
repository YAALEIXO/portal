from django.conf import settings
from django.db import models

from setores.models import Setor


class LinkBIQuerySet(models.QuerySet):
    def visible_to(self, usuario):
        if usuario.is_admin:
            return self
        if hasattr(usuario, "funcionario"):
            return self.filter(funcionarios_liberados=usuario.funcionario)
        return self.none()


class LinkBI(models.Model):
    setor = models.ForeignKey(Setor, on_delete=models.PROTECT, related_name="links_bi")
    nome = models.CharField(max_length=255)
    url = models.URLField(max_length=500)
    descricao = models.TextField(blank=True)
    ativo = models.BooleanField(default=True)
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="links_criados"
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    objects = LinkBIQuerySet.as_manager()

    class Meta:
        ordering = ["setor__empresa__nome", "setor__nome", "nome"]

    def __str__(self):
        return self.nome
