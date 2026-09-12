from django.conf import settings
from django.db import models


class AcessoLogQuerySet(models.QuerySet):
    def visible_to(self, usuario):
        if usuario.is_admin:
            return self
        if (usuario.is_diretor or usuario.is_admin_empresa) and hasattr(usuario, "funcionario"):
            return self.filter(usuario__funcionario__empresa=usuario.funcionario.empresa)
        return self.none()


class AcessoLog(models.Model):
    """Registro append-only de acessos a links de BI. Nunca deve ser editado."""

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="acessos"
    )
    link = models.ForeignKey("bi_links.LinkBI", on_delete=models.PROTECT, related_name="acessos")
    acessado_em = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, blank=True)

    objects = AcessoLogQuerySet.as_manager()

    class Meta:
        ordering = ["-acessado_em"]
        indexes = [models.Index(fields=["usuario", "acessado_em"])]

    def __str__(self):
        return f"{self.usuario} -> {self.link} em {self.acessado_em}"
