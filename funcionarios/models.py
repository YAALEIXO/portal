from django.core.exceptions import ValidationError
from django.db import models

from accounts.models import Usuario
from empresas.models import Empresa
from setores.models import Setor


class Funcionario(models.Model):
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, related_name="funcionario")
    empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT, related_name="funcionarios")
    setor = models.ForeignKey(
        Setor, on_delete=models.PROTECT, related_name="funcionarios", null=True, blank=True
    )
    links_liberados = models.ManyToManyField(
        "bi_links.LinkBI", related_name="funcionarios_liberados", blank=True
    )

    class Meta:
        ordering = ["empresa__nome", "usuario__first_name"]

    def clean(self):
        if self.pk:
            if self.setor_id and self.setor.empresa_id != self.empresa_id:
                raise ValidationError("O setor do funcionário deve pertencer à mesma empresa dele.")
            fora_do_setor = self.links_liberados.exclude(setor=self.setor)
            if fora_do_setor.exists():
                raise ValidationError(
                    "Só é possível liberar links do setor ao qual o funcionário está vinculado."
                )

    def __str__(self):
        return str(self.usuario)
