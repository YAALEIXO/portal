from django.test import TestCase

from accounts.models import Usuario

from .models import Empresa


class EmpresaFormTests(TestCase):
    def setUp(self):
        self.admin = Usuario.objects.create_superuser("admin_x", "admin_x@teste.com", "senha12345")
        self.admin.role = Usuario.Role.ADMIN
        self.admin.save()
        self.client.login(username="admin_x", password="senha12345")

    def test_status_vem_marcado_como_ativada_por_padrao_ao_criar(self):
        resp = self.client.get("/empresas/nova/")
        self.assertContains(resp, 'value="True"')
        self.assertContains(resp, "checked")

    def test_criar_empresa_sem_marcar_status_falha_a_validacao(self):
        """O campo é obrigatório (radio), então omitir 'ativo' no POST não deve
        criar silenciosamente uma empresa inativa por acidente."""
        resp = self.client.post("/empresas/nova/", {"nome": "Sem Status", "cnpj": "10.101.010/0001-10"})
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(Empresa.objects.filter(nome="Sem Status").exists())

    def test_criar_empresa_inativa_explicitamente(self):
        resp = self.client.post(
            "/empresas/nova/", {"nome": "Inativa", "cnpj": "20.202.020/0001-20", "ativo": "False"}
        )
        self.assertEqual(resp.status_code, 302)
        self.assertFalse(Empresa.objects.get(nome="Inativa").ativo)

    def test_editar_empresa_inativa_mostra_status_correto(self):
        empresa = Empresa.objects.create(nome="Inativa 2", cnpj="30.303.030/0001-30", ativo=False)
        resp = self.client.get(f"/empresas/{empresa.pk}/editar/")
        self.assertContains(resp, 'value="False"')
        form = resp.context["form"]
        self.assertEqual(form.initial.get("ativo", form.fields["ativo"].initial), False)
