from django import forms
from django.test import TestCase

from accounts.models import Usuario
from auditoria.models import AcessoLog
from bi_links.models import LinkBI
from empresas.models import Empresa
from setores.models import Setor

from .models import Funcionario


class CadastroUsuarioTests(TestCase):
    """/usuarios/novo/: cadastro único de Usuario + Funcionario, já vinculado a
    uma empresa, um setor (único) e um nível. Admin global escolhe a empresa;
    Admin de Empresa fica travado na própria empresa."""

    def setUp(self):
        self.empresa_a = Empresa.objects.create(nome="Empresa A", cnpj="11.111.111/0001-11")
        self.empresa_b = Empresa.objects.create(nome="Empresa B", cnpj="22.222.222/0001-22")
        self.setor_a = Setor.objects.create(empresa=self.empresa_a, nome="Financeiro")
        self.setor_b = Setor.objects.create(empresa=self.empresa_b, nome="RH")

        self.admin = Usuario.objects.create_superuser("admin_teste", "admin@teste.com", "senha12345")
        self.admin.role = Usuario.Role.ADMIN
        self.admin.save()

        self.u_admin_empresa_a = Usuario.objects.create_user(
            "admin_emp_a", password="senha12345", role=Usuario.Role.ADMIN_EMPRESA
        )
        self.f_admin_empresa_a = Funcionario.objects.create(
            usuario=self.u_admin_empresa_a, empresa=self.empresa_a, setor=self.setor_a
        )

        self.normal = Usuario.objects.create_user(
            "normal_a", password="senha12345", role=Usuario.Role.NORMAL
        )

    def _payload(self, **overrides):
        payload = {
            "username": "novo_usuario",
            "first_name": "Novo",
            "last_name": "",
            "email": "",
            "password": "senha12345",
            "role": Usuario.Role.NORMAL,
            "setor": self.setor_a.pk,
        }
        payload.update(overrides)
        return payload

    def test_admin_empresa_cadastra_usuario_na_propria_empresa(self):
        self.client.login(username="admin_emp_a", password="senha12345")
        resp = self.client.post("/usuarios/novo/", self._payload())
        self.assertEqual(resp.status_code, 302)
        novo = Funcionario.objects.get(usuario__username="novo_usuario")
        self.assertEqual(novo.empresa, self.empresa_a)
        self.assertEqual(novo.setor, self.setor_a)

    def test_admin_empresa_nao_ve_campo_empresa_no_formulario(self):
        self.client.login(username="admin_emp_a", password="senha12345")
        resp = self.client.get("/usuarios/novo/")
        self.assertNotIn("empresa", resp.context["form"].fields)

    def test_setor_e_uma_lista_suspensa_de_selecao_unica(self):
        self.client.login(username="admin_emp_a", password="senha12345")
        resp = self.client.get("/usuarios/novo/")
        widget = resp.context["form"].fields["setor"].widget
        self.assertIsInstance(widget, forms.Select)
        self.assertNotIsInstance(widget, forms.CheckboxSelectMultiple)

    def test_admin_empresa_nao_atribui_setor_de_outra_empresa(self):
        self.client.login(username="admin_emp_a", password="senha12345")
        resp = self.client.post("/usuarios/novo/", self._payload(setor=self.setor_b.pk))
        self.assertEqual(resp.status_code, 200)  # form re-renderizado com erro
        self.assertFalse(Funcionario.objects.filter(usuario__username="novo_usuario").exists())

    def test_admin_global_cadastra_usuario_escolhendo_empresa(self):
        self.client.login(username="admin_teste", password="senha12345")
        resp = self.client.post(
            "/usuarios/novo/", self._payload(empresa=self.empresa_b.pk, setor=self.setor_b.pk)
        )
        self.assertEqual(resp.status_code, 302)
        novo = Funcionario.objects.get(usuario__username="novo_usuario")
        self.assertEqual(novo.empresa, self.empresa_b)
        self.assertEqual(novo.setor, self.setor_b)

    def test_admin_global_nao_atribui_setor_de_empresa_diferente_da_escolhida(self):
        self.client.login(username="admin_teste", password="senha12345")
        resp = self.client.post(
            "/usuarios/novo/", self._payload(empresa=self.empresa_a.pk, setor=self.setor_b.pk)
        )
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(Funcionario.objects.filter(usuario__username="novo_usuario").exists())

    def test_username_duplicado_nao_permite_cadastro(self):
        self.client.login(username="admin_teste", password="senha12345")
        resp = self.client.post(
            "/usuarios/novo/", self._payload(username="admin_emp_a", empresa=self.empresa_a.pk)
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Funcionario.objects.filter(usuario__username="admin_emp_a").count(), 1)

    def test_normal_nao_acessa_cadastro_de_usuario(self):
        self.client.login(username="normal_a", password="senha12345")
        resp = self.client.get("/usuarios/novo/")
        self.assertEqual(resp.status_code, 403)

    def test_formulario_de_cadastro_nao_tem_campo_links_liberados(self):
        """Quem pode acessar cada link agora só se escolhe no formulário do
        Link (usuarios_liberados), não mais no cadastro de usuário."""
        self.client.login(username="admin_emp_a", password="senha12345")
        resp = self.client.get("/usuarios/novo/")
        self.assertNotIn("links_liberados", resp.context["form"].fields)

    def test_empresa_inativa_continua_aparecendo_no_formulario_de_cadastro(self):
        """Regressão: uma empresa marcada como inativa não deve desaparecer do
        seletor de empresa ao cadastrar um usuário."""
        self.empresa_b.ativo = False
        self.empresa_b.save(update_fields=["ativo"])

        self.client.login(username="admin_teste", password="senha12345")
        resp = self.client.get("/usuarios/novo/")
        self.assertIn(self.empresa_b, resp.context["form"].fields["empresa"].queryset)

        resp2 = self.client.post(
            "/usuarios/novo/", self._payload(empresa=self.empresa_b.pk, setor=self.setor_b.pk)
        )
        self.assertEqual(resp2.status_code, 302)
        self.assertTrue(Funcionario.objects.filter(usuario__username="novo_usuario", empresa=self.empresa_b).exists())

    def test_admin_global_com_empresa_travada_pela_url_nao_ve_campo_empresa(self):
        """Vindo do botão "Cadastrar usuário" do hub de uma empresa
        (?empresa_id_lock=), o Admin global não vê o seletor de empresa —
        igual ao que já acontece com "Cadastrar setor"."""
        self.client.login(username="admin_teste", password="senha12345")
        resp = self.client.get(f"/usuarios/novo/?empresa_id_lock={self.empresa_b.pk}")
        self.assertNotIn("empresa", resp.context["form"].fields)
        self.assertEqual(resp.context["empresa_locked"], self.empresa_b)

    def test_admin_global_cadastra_com_empresa_travada_pela_url(self):
        self.client.login(username="admin_teste", password="senha12345")
        resp = self.client.post(
            f"/usuarios/novo/?empresa_id_lock={self.empresa_b.pk}",
            self._payload(setor=self.setor_b.pk, empresa_id_lock=self.empresa_b.pk),
        )
        self.assertRedirects(resp, f"/empresas/{self.empresa_b.pk}/")
        novo = Funcionario.objects.get(usuario__username="novo_usuario")
        self.assertEqual(novo.empresa, self.empresa_b)
        self.assertEqual(novo.setor, self.setor_b)

    def test_admin_empresa_ignora_empresa_id_lock_de_outra_empresa(self):
        """Admin de Empresa nunca deve conseguir usar empresa_id_lock pra
        cadastrar em outra empresa que não a própria — o form ignora o
        parâmetro pra quem não é Admin global."""
        self.client.login(username="admin_emp_a", password="senha12345")
        resp = self.client.post(
            f"/usuarios/novo/?empresa_id_lock={self.empresa_b.pk}",
            self._payload(setor=self.setor_a.pk),
        )
        self.assertEqual(resp.status_code, 302)
        novo = Funcionario.objects.get(usuario__username="novo_usuario")
        self.assertEqual(novo.empresa, self.empresa_a)


class UsuarioCrudTests(TestCase):
    """/usuarios/: listar, editar e excluir usuários já cadastrados. Admin global
    vê/gerencia todas as empresas; Admin de Empresa só a própria (IDOR fechado
    por FuncionarioEscopoMixin)."""

    def setUp(self):
        self.empresa_a = Empresa.objects.create(nome="Empresa A", cnpj="33.333.333/0001-33")
        self.empresa_b = Empresa.objects.create(nome="Empresa B", cnpj="44.444.444/0001-44")
        self.setor_a = Setor.objects.create(empresa=self.empresa_a, nome="Financeiro")
        self.setor_a2 = Setor.objects.create(empresa=self.empresa_a, nome="Comercial")
        self.setor_b = Setor.objects.create(empresa=self.empresa_b, nome="RH")

        self.admin = Usuario.objects.create_superuser("admin_x", "admin_x@teste.com", "senha12345")
        self.admin.role = Usuario.Role.ADMIN
        self.admin.save()

        self.u_admin_empresa_a = Usuario.objects.create_user(
            "admin_emp_a", password="senha12345", role=Usuario.Role.ADMIN_EMPRESA
        )
        self.f_admin_empresa_a = Funcionario.objects.create(
            usuario=self.u_admin_empresa_a, empresa=self.empresa_a, setor=self.setor_a
        )

        u_normal_a = Usuario.objects.create_user(
            "normal_a", password="senha12345", role=Usuario.Role.NORMAL
        )
        self.f_normal_a = Funcionario.objects.create(
            usuario=u_normal_a, empresa=self.empresa_a, setor=self.setor_a
        )

        u_normal_b = Usuario.objects.create_user(
            "normal_b", password="senha12345", role=Usuario.Role.NORMAL
        )
        self.f_normal_b = Funcionario.objects.create(usuario=u_normal_b, empresa=self.empresa_b)

    def test_admin_ve_usuarios_de_todas_as_empresas(self):
        self.client.login(username="admin_x", password="senha12345")
        resp = self.client.get("/usuarios/")
        nomes = sorted(f.usuario.username for f in resp.context["funcionarios"])
        self.assertEqual(nomes, ["admin_emp_a", "normal_a", "normal_b"])

    def test_admin_empresa_ve_apenas_usuarios_da_propria_empresa(self):
        self.client.login(username="admin_emp_a", password="senha12345")
        resp = self.client.get("/usuarios/")
        nomes = sorted(f.usuario.username for f in resp.context["funcionarios"])
        self.assertEqual(nomes, ["admin_emp_a", "normal_a"])

    def test_admin_empresa_edita_usuario_da_propria_empresa(self):
        self.client.login(username="admin_emp_a", password="senha12345")
        resp = self.client.post(
            f"/usuarios/{self.f_normal_a.pk}/editar/",
            {
                "first_name": "Normal Editado",
                "last_name": "",
                "email": "",
                "role": Usuario.Role.DIRETOR,
                "setor": self.setor_a2.pk,
            },
        )
        self.assertEqual(resp.status_code, 302)
        self.f_normal_a.refresh_from_db()
        self.f_normal_a.usuario.refresh_from_db()
        self.assertEqual(self.f_normal_a.usuario.first_name, "Normal Editado")
        self.assertEqual(self.f_normal_a.usuario.role, Usuario.Role.DIRETOR)
        self.assertEqual(self.f_normal_a.setor, self.setor_a2)

    def test_admin_empresa_nao_edita_usuario_de_outra_empresa(self):
        self.client.login(username="admin_emp_a", password="senha12345")
        resp = self.client.get(f"/usuarios/{self.f_normal_b.pk}/editar/")
        self.assertEqual(resp.status_code, 404)

    def test_admin_empresa_nao_exclui_usuario_de_outra_empresa(self):
        self.client.login(username="admin_emp_a", password="senha12345")
        resp = self.client.post(f"/usuarios/{self.f_normal_b.pk}/excluir/")
        self.assertEqual(resp.status_code, 404)
        self.assertTrue(Funcionario.objects.filter(pk=self.f_normal_b.pk).exists())

    def test_exclusao_remove_funcionario_e_usuario(self):
        self.client.login(username="admin_x", password="senha12345")
        usuario_id = self.f_normal_b.usuario_id
        resp = self.client.post(f"/usuarios/{self.f_normal_b.pk}/excluir/")
        self.assertEqual(resp.status_code, 302)
        self.assertFalse(Funcionario.objects.filter(pk=self.f_normal_b.pk).exists())
        self.assertFalse(Usuario.objects.filter(pk=usuario_id).exists())

    def test_exclusao_de_usuario_apaga_links_criados_e_historico_em_cascata(self):
        link = LinkBI.objects.create(
            setor=self.setor_a, nome="Dashboard", url="https://exemplo.com",
            criado_por=self.f_normal_a.usuario,
        )
        AcessoLog.objects.create(usuario=self.f_normal_a.usuario, link=link)

        self.client.login(username="admin_x", password="senha12345")
        resp = self.client.post(f"/usuarios/{self.f_normal_a.pk}/excluir/")

        self.assertEqual(resp.status_code, 302)
        self.assertFalse(LinkBI.objects.filter(pk=link.pk).exists())
        self.assertFalse(AcessoLog.objects.filter(link_id=link.pk).exists())
        self.assertFalse(Funcionario.objects.filter(pk=self.f_normal_a.pk).exists())

    def test_normal_nao_acessa_lista_de_usuarios(self):
        self.client.login(username="normal_a", password="senha12345")
        resp = self.client.get("/usuarios/")
        self.assertEqual(resp.status_code, 403)


class UsuarioEditFormTests(TestCase):
    """Formulário de edição de usuário: login travado, senha opcional, e não
    toca em links_liberados (isso agora só se edita pelo formulário do Link)."""

    def setUp(self):
        self.empresa = Empresa.objects.create(nome="Empresa Links", cnpj="55.555.555/0001-55")
        self.setor = Setor.objects.create(empresa=self.empresa, nome="Financeiro")

        self.admin = Usuario.objects.create_superuser("admin_l", "admin_l@teste.com", "senha12345")
        self.admin.role = Usuario.Role.ADMIN
        self.admin.save()

        self.link_1 = LinkBI.objects.create(
            setor=self.setor, nome="Dashboard 1", url="https://example.com/1", criado_por=self.admin
        )

        u = Usuario.objects.create_user("colaborador", password="senha12345", role=Usuario.Role.NORMAL)
        self.funcionario = Funcionario.objects.create(
            usuario=u, empresa=self.empresa, setor=self.setor
        )
        self.funcionario.links_liberados.set([self.link_1])

        self.client.login(username="admin_l", password="senha12345")

    def test_formulario_de_edicao_nao_tem_campo_links_liberados(self):
        resp = self.client.get(f"/usuarios/{self.funcionario.pk}/editar/")
        self.assertNotIn("links_liberados", resp.context["form"].fields)

    def test_edicao_de_usuario_nao_altera_links_liberados(self):
        resp = self.client.post(
            f"/usuarios/{self.funcionario.pk}/editar/",
            {
                "username": "colaborador",
                "first_name": "Colaborador Editado",
                "last_name": "",
                "email": "",
                "password": "",
                "role": Usuario.Role.NORMAL,
                "setor": self.setor.pk,
            },
        )
        self.assertEqual(resp.status_code, 302)
        self.funcionario.refresh_from_db()
        self.assertEqual(set(self.funcionario.links_liberados.all()), {self.link_1})

    def test_edicao_de_usuario_permite_trocar_senha(self):
        resp = self.client.post(
            f"/usuarios/{self.funcionario.pk}/editar/",
            {
                "username": "colaborador",
                "first_name": "Colaborador",
                "last_name": "",
                "email": "",
                "password": "novasenha123",
                "role": Usuario.Role.NORMAL,
                "setor": self.setor.pk,
            },
        )
        self.assertEqual(resp.status_code, 302)
        self.funcionario.usuario.refresh_from_db()
        self.assertTrue(self.funcionario.usuario.check_password("novasenha123"))

    def test_edicao_de_usuario_nao_permite_trocar_login(self):
        self.client.post(
            f"/usuarios/{self.funcionario.pk}/editar/",
            {
                "username": "outro_login",
                "first_name": "Colaborador",
                "last_name": "",
                "email": "",
                "password": "",
                "role": Usuario.Role.NORMAL,
                "setor": self.setor.pk,
            },
        )
        self.funcionario.usuario.refresh_from_db()
        self.assertEqual(self.funcionario.usuario.username, "colaborador")
