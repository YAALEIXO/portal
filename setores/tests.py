from django.test import TestCase

from accounts.models import Usuario
from auditoria.models import AcessoLog
from bi_links.models import LinkBI
from empresas.models import Empresa
from funcionarios.models import Funcionario

from .models import Setor


class SetorEscopoTests(TestCase):
    """Setores são geridos pelo Admin global (qualquer empresa) e pelo Admin de
    Empresa (só a própria), sempre escopados pela empresa da URL."""

    def setUp(self):
        self.empresa_a = Empresa.objects.create(nome="Empresa A", cnpj="11.111.111/0001-11")
        self.empresa_b = Empresa.objects.create(nome="Empresa B", cnpj="22.222.222/0001-22")
        self.setor_a = Setor.objects.create(empresa=self.empresa_a, nome="Financeiro")
        self.setor_b = Setor.objects.create(empresa=self.empresa_b, nome="RH")

        self.admin = Usuario.objects.create_superuser("admin_teste", "admin@teste.com", "senha12345")
        self.admin.role = Usuario.Role.ADMIN
        self.admin.save()

        self.normal = Usuario.objects.create_user(
            "normal_a", password="senha12345", role=Usuario.Role.NORMAL
        )

        u_admin_empresa_a = Usuario.objects.create_user(
            "admin_emp_a", password="senha12345", role=Usuario.Role.ADMIN_EMPRESA
        )
        self.f_admin_empresa_a = Funcionario.objects.create(
            usuario=u_admin_empresa_a, empresa=self.empresa_a
        )

    def test_admin_lista_apenas_setores_da_empresa_da_url(self):
        self.client.login(username="admin_teste", password="senha12345")
        resp = self.client.get(f"/empresas/{self.empresa_a.pk}/setores/")
        nomes = [s.nome for s in resp.context["setores"]]
        self.assertEqual(nomes, ["Financeiro"])

    def test_admin_cria_setor_vinculado_a_empresa_da_url(self):
        self.client.login(username="admin_teste", password="senha12345")
        resp = self.client.post(f"/empresas/{self.empresa_a.pk}/setores/novo/", {"nome": "Comercial"})
        self.assertEqual(resp.status_code, 302)
        novo = Setor.objects.get(nome="Comercial")
        self.assertEqual(novo.empresa, self.empresa_a)

    def test_admin_nao_edita_setor_de_outra_empresa_via_url_forjada(self):
        self.client.login(username="admin_teste", password="senha12345")
        resp = self.client.get(f"/empresas/{self.empresa_a.pk}/setores/{self.setor_b.pk}/editar/")
        self.assertEqual(resp.status_code, 404)

    def test_setores_de_empresa_inexistente_404(self):
        self.client.login(username="admin_teste", password="senha12345")
        resp = self.client.get("/empresas/9999/setores/")
        self.assertEqual(resp.status_code, 404)

    def test_normal_nao_acessa_gestao_de_setores(self):
        self.client.login(username="normal_a", password="senha12345")
        resp = self.client.get(f"/empresas/{self.empresa_a.pk}/setores/")
        self.assertEqual(resp.status_code, 403)

    def test_admin_empresa_cadastra_setor_na_propria_empresa(self):
        self.client.login(username="admin_emp_a", password="senha12345")
        resp = self.client.post(f"/empresas/{self.empresa_a.pk}/setores/novo/", {"nome": "Comercial"})
        self.assertEqual(resp.status_code, 302)
        novo = Setor.objects.get(nome="Comercial")
        self.assertEqual(novo.empresa, self.empresa_a)

    def test_admin_empresa_nao_gerencia_setores_de_outra_empresa(self):
        self.client.login(username="admin_emp_a", password="senha12345")
        resp = self.client.get(f"/empresas/{self.empresa_b.pk}/setores/")
        self.assertEqual(resp.status_code, 404)

    def test_exclusao_de_setor_apaga_links_e_usuarios_vinculados_em_cascata(self):
        link = LinkBI.objects.create(
            setor=self.setor_a, nome="Dashboard", url="https://exemplo.com", criado_por=self.admin
        )
        u_normal_a = Usuario.objects.create_user(
            "normal_a2", password="senha12345", role=Usuario.Role.NORMAL
        )
        funcionario = Funcionario.objects.create(
            usuario=u_normal_a, empresa=self.empresa_a, setor=self.setor_a
        )
        AcessoLog.objects.create(usuario=u_normal_a, link=link)

        self.client.login(username="admin_teste", password="senha12345")
        resp = self.client.post(f"/empresas/{self.empresa_a.pk}/setores/{self.setor_a.pk}/excluir/")

        self.assertEqual(resp.status_code, 302)
        self.assertFalse(Setor.objects.filter(pk=self.setor_a.pk).exists())
        self.assertFalse(LinkBI.objects.filter(pk=link.pk).exists())
        self.assertFalse(Funcionario.objects.filter(pk=funcionario.pk).exists())
        self.assertFalse(Usuario.objects.filter(pk=u_normal_a.pk).exists())
        self.assertFalse(AcessoLog.objects.filter(link_id=link.pk).exists())
        # setor_b (outra empresa) não deve ser afetado
        self.assertTrue(Setor.objects.filter(pk=self.setor_b.pk).exists())
