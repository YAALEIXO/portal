from django.db import models

from empresas.models import Empresa


class Setor(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT, related_name="setores")
    nome = models.CharField(max_length=255)

    class Meta:
        ordering = ["empresa__nome", "nome"]
        constraints = [
            models.UniqueConstraint(fields=["empresa", "nome"], name="setor_unico_por_empresa"),
        ]

    def __str__(self):
        return self.nome
