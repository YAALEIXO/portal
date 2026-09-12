from django.db import migrations


def preencher_setor_unico(apps, schema_editor):
    """Funcionario passa a ter um único setor (FK) em vez de vários (M2M).
    Pra quem já tinha mais de um setor, mantém o primeiro — o admin ajusta
    manualmente depois se precisar trocar."""
    Funcionario = apps.get_model("funcionarios", "Funcionario")
    for funcionario in Funcionario.objects.prefetch_related("setores").all():
        primeiro_setor = funcionario.setores.first()
        if primeiro_setor:
            funcionario.setor = primeiro_setor
            funcionario.save(update_fields=["setor"])


def reverter(apps, schema_editor):
    Funcionario = apps.get_model("funcionarios", "Funcionario")
    for funcionario in Funcionario.objects.all():
        if funcionario.setor_id:
            funcionario.setores.add(funcionario.setor_id)


class Migration(migrations.Migration):

    dependencies = [
        ("funcionarios", "0004_funcionario_setor_alter_funcionario_setores"),
    ]

    operations = [
        migrations.RunPython(preencher_setor_unico, reverter),
    ]
