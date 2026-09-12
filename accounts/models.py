from django.contrib.auth.models import AbstractUser
from django.db import models


class Usuario(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Administrador"
        ADMIN_EMPRESA = "ADMIN_EMPRESA", "Admin da Empresa"
        DIRETOR = "DIRETOR", "Diretor"
        NORMAL = "NORMAL", "Usuário Normal"

    role = models.CharField(max_length=13, choices=Role.choices, default=Role.NORMAL)
    last_seen = models.DateTimeField(null=True, blank=True)

    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN

    @property
    def is_admin_empresa(self):
        return self.role == self.Role.ADMIN_EMPRESA

    @property
    def is_diretor(self):
        return self.role == self.Role.DIRETOR

    @property
    def is_normal(self):
        return self.role == self.Role.NORMAL

    def __str__(self):
        return self.get_full_name() or self.username
