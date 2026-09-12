from django.db import migrations


def preencher_links_liberados(apps, schema_editor):
    """Antes desta mudança, o acesso era só por setor: todo link dos setores do
    funcionário era visível. Preenche links_liberados com esse mesmo conjunto,
    pra ninguém perder acesso a links que já tinha no dia da migração."""
    Funcionario = apps.get_model("funcionarios", "Funcionario")
    LinkBI = apps.get_model("bi_links", "LinkBI")
    for funcionario in Funcionario.objects.prefetch_related("setores").all():
        setor_ids = funcionario.setores.values_list("pk", flat=True)
        links = LinkBI.objects.filter(setor_id__in=setor_ids)
        funcionario.links_liberados.set(links)


def reverter(apps, schema_editor):
    Funcionario = apps.get_model("funcionarios", "Funcionario")
    for funcionario in Funcionario.objects.all():
        funcionario.links_liberados.clear()


class Migration(migrations.Migration):

    dependencies = [
        ("funcionarios", "0002_funcionario_links_liberados"),
    ]

    operations = [
        migrations.RunPython(preencher_links_liberados, reverter),
    ]
