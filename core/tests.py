from django.test import TestCase

from accounts.models import Usuario
from bi_links.models import LinkBI
from empresas.models import Empresa
from funcionarios.models import Funcionario
from setores.models import Setor


class DashboardPorPapelTests(TestCase):
    """Cada papel vê uma versão diferente de `/`: Admin global vê o painel
    consolidado (empresas/usuários/links + gráfico por empresa); Admin de
    Empresa e Diretor veem os "Indicadores de Alerta" da própria empresa;
    os demais veem só a lista dos próprios links."""

    def setUp(self):
        self.empresa_a = Empresa.objects.create(nome="Empresa A", cnpj="11.111.111/0001-11")
        self.empresa_b = Empresa.objects.create(nome="Empresa B", cnpj="22.222.222/0001-22")
        self.setor_a = Setor.objects.create(empresa=self.empresa_a, nome="Financeiro")
        self.setor_b = Setor.objects.create(empresa=self.empresa_b, nome="RH")

        self.admin = Usuario.objects.create_superuser("admin_teste", "admin@teste.com", "senha12345")
        self.admin.role = Usuario.Role.ADMIN
        self.admin.save()

        self.link_a = LinkBI.objects.create(
            setor=self.setor_a, nome="Dashboard A", url="https://example.com/a", criado_por=self.admin
        )
        LinkBI.objects.create(
            setor=self.setor_b, nome="Dashboard B1", url="https://example.com/b1", criado_por=self.admin
        )
        LinkBI.objects.create(
            setor=self.setor_b, nome="Dashboard B2", url="https://example.com/b2", criado_por=self.admin
        )

        u_admin_empresa_a = Usuario.objects.create_user(
            "admin_emp_a", password="senha12345", role=Usuario.Role.ADMIN_EMPRESA
        )
        self.f_admin_empresa_a = Funcionario.objects.create(
            usuario=u_admin_empresa_a, empresa=self.empresa_a, setor=self.setor_a
        )

        u_diretor_a = Usuario.objects.create_user(
            "diretor_a", password="senha12345", role=Usuario.Role.DIRETOR
        )
        self.f_diretor_a = Funcionario.objects.create(
            usuario=u_diretor_a, empresa=self.empresa_a, setor=self.setor_a
        )

        u_normal_a = Usuario.objects.create_user(
            "normal_a", password="senha12345", role=Usuario.Role.NORMAL
        )
        self.f_normal_a = Funcionario.objects.create(
            usuario=u_normal_a, empresa=self.empresa_a, setor=self.setor_a
        )

    def test_admin_ve_painel_consolidado(self):
        self.client.login(username="admin_teste", password="senha12345")
        resp = self.client.get("/")
        self.assertTrue(resp.context["mostrar_painel_admin"])
        self.assertNotIn("mostrar_indicadores", resp.context)
        self.assertEqual(resp.context["total_empresas"], 2)
        # 3 Funcionarios (admin_emp_a, diretor_a, normal_a) — o próprio admin não
        # tem Funcionario, então "total de usuários" não deve contá-lo.
        self.assertEqual(resp.context["total_usuarios"], 3)
        self.assertEqual(resp.context["total_links"], 3)
        por_empresa = {i["setor__empresa__nome"]: i["total"] for i in resp.context["links_por_empresa"]}
        self.assertEqual(por_empresa, {"Empresa A": 1, "Empresa B": 2})
        self.assertContains(resp, "Empresas Cadastradas")
        self.assertContains(resp, "Total de Links Cadastrados")

    def test_admin_empresa_ve_indicadores_da_propria_empresa(self):
        self.client.login(username="admin_emp_a", password="senha12345")
        resp = self.client.get("/")
        self.assertFalse(resp.context.get("mostrar_painel_admin"))
        self.assertTrue(resp.context["mostrar_indicadores"])
        self.assertContains(resp, "Indicadores de Alerta")

    def test_diretor_continua_vendo_indicadores(self):
        self.client.login(username="diretor_a", password="senha12345")
        resp = self.client.get("/")
        self.assertFalse(resp.context.get("mostrar_painel_admin"))
        self.assertTrue(resp.context["mostrar_indicadores"])
        self.assertContains(resp, "Indicadores de Alerta")

    def test_normal_ve_apenas_seus_links(self):
        self.client.login(username="normal_a", password="senha12345")
        resp = self.client.get("/")
        self.assertFalse(resp.context.get("mostrar_painel_admin"))
        self.assertFalse(resp.context["mostrar_indicadores"])
        self.assertContains(resp, "Seus links de BI")


class ShellNavTests(TestCase):
    """Sidebar/topbar novas (base.html): empresa ativa (real, via sessão, só
    pro Admin global) e os grupos de navegação filtrados por papel."""

    def setUp(self):
        self.empresa_a = Empresa.objects.create(nome="Empresa A", cnpj="33.333.333/0001-33")
        self.empresa_b = Empresa.objects.create(nome="Empresa B", cnpj="44.444.444/0001-44")
        self.setor_a = Setor.objects.create(empresa=self.empresa_a, nome="Financeiro")

        self.admin = Usuario.objects.create_superuser("admin_x", "admin_x@teste.com", "senha12345")
        self.admin.role = Usuario.Role.ADMIN
        self.admin.save()

        u_admin_empresa_a = Usuario.objects.create_user(
            "admin_emp_a", password="senha12345", role=Usuario.Role.ADMIN_EMPRESA
        )
        self.f_admin_empresa_a = Funcionario.objects.create(
            usuario=u_admin_empresa_a, empresa=self.empresa_a, setor=self.setor_a
        )

        u_normal_a = Usuario.objects.create_user(
            "normal_a", password="senha12345", role=Usuario.Role.NORMAL
        )
        self.f_normal_a = Funcionario.objects.create(
            usuario=u_normal_a, empresa=self.empresa_a, setor=self.setor_a
        )

    def test_visitar_hub_de_empresa_grava_empresa_ativa_na_sessao(self):
        self.client.login(username="admin_x", password="senha12345")
        self.client.get(f"/empresas/{self.empresa_b.pk}/")
        self.assertEqual(self.client.session["empresa_ativa_id"], self.empresa_b.pk)

    def test_sem_empresa_ativa_na_sessao_usa_a_primeira_por_ordem_alfabetica(self):
        self.client.login(username="admin_x", password="senha12345")
        resp = self.client.get("/")
        self.assertEqual(resp.context["empresa_ativa"], self.empresa_a)

    def test_links_de_setores_e_bi_seguem_a_empresa_ativa(self):
        self.client.login(username="admin_x", password="senha12345")
        self.client.get(f"/empresas/{self.empresa_b.pk}/")
        resp = self.client.get("/")
        grupos = {g["titulo"]: g["itens"] for g in resp.context["grupos_nav"]}
        urls = {item["label"]: item["url"] for item in grupos["Administração"]}
        self.assertEqual(urls["Setores"], f"/empresas/{self.empresa_b.pk}/setores/")
        self.assertEqual(urls["Links de BI"], f"/empresas/{self.empresa_b.pk}/links/")

    def test_admin_empresa_nao_ve_seletor_de_troca_nem_item_empresas(self):
        self.client.login(username="admin_emp_a", password="senha12345")
        resp = self.client.get("/")
        self.assertEqual(resp.context["empresa_ativa"], self.empresa_a)
        self.assertIsNone(resp.context["empresas_disponiveis"])
        self.assertNotContains(resp, "shellEmpresaToggle")
        grupos = {g["titulo"]: g["itens"] for g in resp.context["grupos_nav"]}
        labels = [item["label"] for item in grupos["Administração"]]
        self.assertNotIn("Empresas", labels)

    def test_normal_nao_ve_grupos_administracao_e_sistema(self):
        self.client.login(username="normal_a", password="senha12345")
        resp = self.client.get("/")
        titulos = [g["titulo"] for g in resp.context["grupos_nav"]]
        self.assertNotIn("Administração", titulos)
        self.assertNotIn("Sistema", titulos)
