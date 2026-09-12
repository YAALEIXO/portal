from django.test import TestCase

from accounts.models import Usuario
from bi_links.models import LinkBI
from empresas.models import Empresa
from funcionarios.models import Funcionario
from setores.models import Setor


class NestedAdminPagesRenderTests(TestCase):
    def setUp(self):
        self.admin = Usuario.objects.create_superuser("admin_x", "a@a.com", "senha12345")
        self.admin.role = Usuario.Role.ADMIN
        self.admin.save()
        self.empresa = Empresa.objects.create(nome="Empresa X", cnpj="99.999.999/0001-99")
        self.setor = Setor.objects.create(empresa=self.empresa, nome="TI")
        u = Usuario.objects.create_user("func1", password="senha12345", role=Usuario.Role.NORMAL)
        self.func = Funcionario.objects.create(usuario=u, empresa=self.empresa, setor=self.setor)
        self.link = LinkBI.objects.create(
            setor=self.setor, nome="L1", url="https://x.com", criado_por=self.admin
        )
        self.client.login(username="admin_x", password="senha12345")

    def test_pages(self):
        e = self.empresa.pk
        urls = [
            "/",
            "/empresas/",
            "/empresas/nova/",
            f"/empresas/{e}/",
            f"/empresas/{e}/editar/",
            f"/empresas/{e}/setores/",
            f"/empresas/{e}/setores/novo/",
            f"/empresas/{e}/setores/{self.setor.pk}/editar/",
            "/usuarios/novo/",
            f"/empresas/{e}/links/",
            f"/empresas/{e}/links/novo/",
            f"/empresas/{e}/links/{self.link.pk}/editar/",
            "/links/",
            "/auditoria/",
        ]
        for url in urls:
            resp = self.client.get(url)
            assert resp.status_code == 200, f"{url} -> {resp.status_code}"

    def test_setor_criar_form_sem_campo_empresa(self):
        resp = self.client.post(
            f"/empresas/{self.empresa.pk}/setores/novo/", {"nome": "Comercial"}
        )
        assert resp.status_code == 302, resp.content[:500]
        novo = Setor.objects.get(nome="Comercial")
        assert novo.empresa_id == self.empresa.pk

    def test_link_criar_form_restringe_setor_a_empresa(self):
        outra_empresa = Empresa.objects.create(nome="Outra", cnpj="88.888.888/0001-88")
        outro_setor = Setor.objects.create(empresa=outra_empresa, nome="Outro")
        resp = self.client.post(
            f"/empresas/{self.empresa.pk}/links/novo/",
            {
                "setor": outro_setor.pk,
                "nome": "Tentativa",
                "url": "https://y.com",
                "descricao": "",
            },
        )
        assert resp.status_code == 200  # form invalido, setor fora do queryset
        assert not LinkBI.objects.filter(nome="Tentativa").exists()
