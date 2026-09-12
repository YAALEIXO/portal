from django.test import TestCase

from accounts.models import Usuario
from auditoria.models import AcessoLog
from empresas.models import Empresa
from funcionarios.models import Funcionario
from setores.models import Setor

from .models import LinkBI


class EscopoDeAcessoTests(TestCase):
    """Cobre o ponto crítico de segurança do sistema: visible_to() de cada papel."""

    def setUp(self):
        self.empresa_a = Empresa.objects.create(nome="Empresa A", cnpj="11.111.111/0001-11")
        self.empresa_b = Empresa.objects.create(nome="Empresa B", cnpj="22.222.222/0001-22")

        self.setor_a1 = Setor.objects.create(empresa=self.empresa_a, nome="Financeiro")
        self.setor_a2 = Setor.objects.create(empresa=self.empresa_a, nome="Comercial")
        self.setor_b1 = Setor.objects.create(empresa=self.empresa_b, nome="RH")

        self.admin = Usuario.objects.create_superuser(
            "admin_teste", "admin@teste.com", "senha12345"
        )
        self.admin.role = Usuario.Role.ADMIN
        self.admin.save()

        self.u_normal_a = Usuario.objects.create_user(
            "normal_a", password="senha12345", role=Usuario.Role.NORMAL
        )
        self.f_normal_a = Funcionario.objects.create(
            usuario=self.u_normal_a, empresa=self.empresa_a, setor=self.setor_a1
        )

        self.u_diretor_a = Usuario.objects.create_user(
            "diretor_a", password="senha12345", role=Usuario.Role.DIRETOR
        )
        self.f_diretor_a = Funcionario.objects.create(
            usuario=self.u_diretor_a, empresa=self.empresa_a, setor=self.setor_a1
        )

        self.u_normal_b = Usuario.objects.create_user(
            "normal_b", password="senha12345", role=Usuario.Role.NORMAL
        )
        self.f_normal_b = Funcionario.objects.create(
            usuario=self.u_normal_b, empresa=self.empresa_b, setor=self.setor_b1
        )

        self.link_a1 = LinkBI.objects.create(
            setor=self.setor_a1, nome="Dashboard Financeiro A", url="https://example.com/a1",
            criado_por=self.admin,
        )
        self.link_a1b = LinkBI.objects.create(
            setor=self.setor_a1, nome="Dashboard Financeiro A2", url="https://example.com/a1b",
            criado_por=self.admin,
        )
        self.link_a2 = LinkBI.objects.create(
            setor=self.setor_a2, nome="Dashboard Comercial A", url="https://example.com/a2",
            criado_por=self.admin,
        )
        self.link_b1 = LinkBI.objects.create(
            setor=self.setor_b1, nome="Dashboard RH B", url="https://example.com/b1",
            criado_por=self.admin,
        )

        # Acesso agora é por link individual, não só por setor: libera links
        # específicos pra cada um (sempre dentro do próprio setor).
        self.f_normal_a.links_liberados.set([self.link_a1])
        self.f_diretor_a.links_liberados.set([self.link_a1, self.link_a1b])
        self.f_normal_b.links_liberados.set([self.link_b1])

    def test_normal_ve_apenas_links_do_proprio_setor(self):
        self.client.login(username="normal_a", password="senha12345")
        resp = self.client.get("/links/")
        nomes = [l.nome for l in resp.context["links"]]
        self.assertEqual(nomes, ["Dashboard Financeiro A"])

    def test_normal_nao_acessa_link_de_outro_setor_mesma_empresa(self):
        self.client.login(username="normal_a", password="senha12345")
        resp = self.client.get(f"/links/{self.link_a2.pk}/acessar/")
        self.assertEqual(resp.status_code, 404)

    def test_normal_nao_acessa_link_de_outra_empresa(self):
        self.client.login(username="normal_a", password="senha12345")
        resp = self.client.get(f"/links/{self.link_b1.pk}/acessar/")
        self.assertEqual(resp.status_code, 404)

    def test_acesso_permitido_gera_log_e_mostra_iframe(self):
        """O link abre embutido num iframe dentro do próprio portal — não
        redireciona nem abre em outra aba."""
        self.client.login(username="normal_a", password="senha12345")
        resp = self.client.get(f"/links/{self.link_a1.pk}/acessar/")
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, f'src="{self.link_a1.url}"')
        self.assertTrue(
            AcessoLog.objects.filter(usuario=self.u_normal_a, link=self.link_a1).exists()
        )

    def test_normal_nao_acessa_auditoria(self):
        self.client.login(username="normal_a", password="senha12345")
        resp = self.client.get("/auditoria/")
        self.assertEqual(resp.status_code, 403)

    def test_diretor_ve_todos_os_links_liberados_a_ele(self):
        self.client.login(username="diretor_a", password="senha12345")
        resp = self.client.get("/links/")
        nomes = sorted(l.nome for l in resp.context["links"])
        self.assertEqual(nomes, ["Dashboard Financeiro A", "Dashboard Financeiro A2"])

    def test_diretor_ve_auditoria_apenas_da_propria_empresa(self):
        self.client.login(username="normal_a", password="senha12345")
        self.client.get(f"/links/{self.link_a1.pk}/acessar/")
        self.client.logout()

        self.client.login(username="normal_b", password="senha12345")
        self.client.get(f"/links/{self.link_b1.pk}/acessar/")
        self.client.logout()

        self.client.login(username="diretor_a", password="senha12345")
        resp = self.client.get("/auditoria/")
        usuarios_no_log = sorted({a.usuario.username for a in resp.context["acessos"]})
        self.assertEqual(usuarios_no_log, ["normal_a"])

    def test_admin_ve_tudo(self):
        self.client.login(username="admin_teste", password="senha12345")
        resp = self.client.get("/links/")
        self.assertEqual(len(resp.context["links"]), 4)

        resp = self.client.get("/auditoria/")
        self.assertEqual(resp.status_code, 200)


class LinkBIAdminEscopoTests(TestCase):
    """Gerenciador de Links (admin) é escopado pela empresa da URL aninhada."""

    def setUp(self):
        self.empresa_a = Empresa.objects.create(nome="Empresa A", cnpj="33.333.333/0001-33")
        self.empresa_b = Empresa.objects.create(nome="Empresa B", cnpj="44.444.444/0001-44")
        self.setor_a = Setor.objects.create(empresa=self.empresa_a, nome="Financeiro")
        self.setor_b = Setor.objects.create(empresa=self.empresa_b, nome="RH")

        self.admin = Usuario.objects.create_superuser("admin_x", "admin_x@teste.com", "senha12345")
        self.admin.role = Usuario.Role.ADMIN
        self.admin.save()

        self.normal = Usuario.objects.create_user(
            "normal_x", password="senha12345", role=Usuario.Role.NORMAL
        )

        u_admin_empresa_a = Usuario.objects.create_user(
            "admin_emp_a", password="senha12345", role=Usuario.Role.ADMIN_EMPRESA
        )
        self.f_admin_empresa_a = Funcionario.objects.create(
            usuario=u_admin_empresa_a, empresa=self.empresa_a
        )

        self.link_a = LinkBI.objects.create(
            setor=self.setor_a, nome="Dashboard A", url="https://example.com/a", criado_por=self.admin,
        )
        self.link_b = LinkBI.objects.create(
            setor=self.setor_b, nome="Dashboard B", url="https://example.com/b", criado_por=self.admin,
        )

    def test_admin_lista_apenas_links_da_empresa_da_url(self):
        self.client.login(username="admin_x", password="senha12345")
        resp = self.client.get(f"/empresas/{self.empresa_a.pk}/links/")
        nomes = [l.nome for l in resp.context["links"]]
        self.assertEqual(nomes, ["Dashboard A"])

    def test_form_de_criacao_restringe_setor_a_empresa_da_url(self):
        self.client.login(username="admin_x", password="senha12345")
        resp = self.client.get(f"/empresas/{self.empresa_a.pk}/links/novo/")
        setores_disponiveis = list(resp.context["form"].fields["setor"].queryset)
        self.assertEqual(setores_disponiveis, [self.setor_a])

    def test_admin_nao_edita_link_de_outra_empresa_via_url_forjada(self):
        self.client.login(username="admin_x", password="senha12345")
        resp = self.client.get(f"/empresas/{self.empresa_a.pk}/links/{self.link_b.pk}/editar/")
        self.assertEqual(resp.status_code, 404)

    def test_links_admin_de_empresa_inexistente_404(self):
        self.client.login(username="admin_x", password="senha12345")
        resp = self.client.get("/empresas/9999/links/")
        self.assertEqual(resp.status_code, 404)

    def test_normal_nao_acessa_gerenciador_de_links(self):
        self.client.login(username="normal_x", password="senha12345")
        resp = self.client.get(f"/empresas/{self.empresa_a.pk}/links/")
        self.assertEqual(resp.status_code, 403)

    def test_admin_empresa_cria_link_na_propria_empresa(self):
        self.client.login(username="admin_emp_a", password="senha12345")
        resp = self.client.post(
            f"/empresas/{self.empresa_a.pk}/links/novo/",
            {
                "setor": self.setor_a.pk,
                "nome": "Dashboard Novo",
                "url": "https://example.com/novo",
                "ativo": "True",
            },
        )
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(LinkBI.objects.filter(nome="Dashboard Novo", setor=self.setor_a).exists())

    def test_admin_empresa_nao_gerencia_links_de_outra_empresa(self):
        self.client.login(username="admin_emp_a", password="senha12345")
        resp = self.client.get(f"/empresas/{self.empresa_b.pk}/links/")
        self.assertEqual(resp.status_code, 404)

    def test_exclusao_de_link_apaga_historico_de_acesso_em_cascata(self):
        AcessoLog.objects.create(usuario=self.admin, link=self.link_a)
        self.client.login(username="admin_x", password="senha12345")
        resp = self.client.post(f"/empresas/{self.empresa_a.pk}/links/{self.link_a.pk}/excluir/")
        self.assertEqual(resp.status_code, 302)
        self.assertFalse(LinkBI.objects.filter(pk=self.link_a.pk).exists())
        self.assertFalse(AcessoLog.objects.filter(link_id=self.link_a.pk).exists())


class LinkBIUsuariosLiberadosTests(TestCase):
    """No formulário do Link (não só no do usuário) dá pra escolher quem
    acessa: um checklist com os funcionários do setor escolhido."""

    def setUp(self):
        self.empresa = Empresa.objects.create(nome="Empresa Y", cnpj="66.666.666/0001-66")
        self.setor = Setor.objects.create(empresa=self.empresa, nome="Financeiro")
        self.outro_setor = Setor.objects.create(empresa=self.empresa, nome="Comercial")

        self.admin = Usuario.objects.create_superuser("admin_y", "admin_y@teste.com", "senha12345")
        self.admin.role = Usuario.Role.ADMIN
        self.admin.save()

        u1 = Usuario.objects.create_user("colab1", password="senha12345", role=Usuario.Role.NORMAL)
        self.f1 = Funcionario.objects.create(usuario=u1, empresa=self.empresa, setor=self.setor)
        u2 = Usuario.objects.create_user("colab2", password="senha12345", role=Usuario.Role.NORMAL)
        self.f2 = Funcionario.objects.create(usuario=u2, empresa=self.empresa, setor=self.setor)
        u3 = Usuario.objects.create_user("colab3", password="senha12345", role=Usuario.Role.NORMAL)
        self.f3 = Funcionario.objects.create(usuario=u3, empresa=self.empresa, setor=self.outro_setor)

        self.client.login(username="admin_y", password="senha12345")

    def test_criar_link_libera_para_varios_usuarios_de_uma_vez(self):
        resp = self.client.post(
            f"/empresas/{self.empresa.pk}/links/novo/",
            {
                "setor": self.setor.pk,
                "nome": "Dashboard Financeiro",
                "url": "https://example.com/fin",
                "ativo": "True",
                "usuarios_liberados": [self.f1.pk, self.f2.pk],
            },
        )
        self.assertEqual(resp.status_code, 302)
        link = LinkBI.objects.get(nome="Dashboard Financeiro")
        self.assertEqual(set(link.funcionarios_liberados.all()), {self.f1, self.f2})
        self.assertIn(link, LinkBI.objects.visible_to(self.f1.usuario))
        self.assertNotIn(link, LinkBI.objects.visible_to(self.f3.usuario))

    def test_nao_libera_link_para_usuario_de_outro_setor(self):
        resp = self.client.post(
            f"/empresas/{self.empresa.pk}/links/novo/",
            {
                "setor": self.setor.pk,
                "nome": "Dashboard Financeiro",
                "url": "https://example.com/fin",
                "ativo": "True",
                "usuarios_liberados": [self.f3.pk],
            },
        )
        self.assertEqual(resp.status_code, 200)  # form re-renderizado com erro
        self.assertFalse(LinkBI.objects.filter(nome="Dashboard Financeiro").exists())

    def test_editar_link_troca_quem_tem_acesso(self):
        link = LinkBI.objects.create(
            setor=self.setor, nome="Dashboard X", url="https://example.com/x", criado_por=self.admin
        )
        link.funcionarios_liberados.set([self.f1])

        resp = self.client.post(
            f"/empresas/{self.empresa.pk}/links/{link.pk}/editar/",
            {
                "setor": self.setor.pk,
                "nome": "Dashboard X",
                "url": "https://example.com/x",
                "ativo": "True",
                "usuarios_liberados": [self.f2.pk],
            },
        )
        self.assertEqual(resp.status_code, 302)
        link.refresh_from_db()
        self.assertEqual(set(link.funcionarios_liberados.all()), {self.f2})
