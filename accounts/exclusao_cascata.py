"""Exclusão em cascata para Setor, LinkBI e Usuário.

O Admin (e o Admin de Empresa, dentro da própria empresa) está autorizado a
excluir esses três por completo, junto com tudo que depende deles — inclusive
o histórico de auditoria (`AcessoLog`), que normalmente é protegido contra
exclusão (`on_delete=PROTECT`) para preservar o registro de acessos. Essas
funções assumem essa autorização e não devem ser chamadas fora de uma view
que já validou o papel do usuário.
"""


def excluir_link_em_cascata(link):
    """Exclui um LinkBI e todo o histórico de acesso (AcessoLog) vinculado a ele."""
    link.acessos.all().delete()
    link.delete()


def excluir_usuario_em_cascata(usuario):
    """Exclui um Usuario e tudo que depende dele: os links de BI que ele criou
    (com o histórico de acesso desses links) e o próprio histórico de acesso
    do usuário. O Funcionario é excluído junto automaticamente (FK CASCADE)."""
    for link in list(usuario.links_criados.all()):
        excluir_link_em_cascata(link)
    usuario.acessos.all().delete()
    usuario.delete()


def excluir_setor_em_cascata(setor):
    """Exclui um Setor e tudo que depende dele: os links de BI do setor (com
    seus logs) e os funcionários/usuários vinculados ao setor."""
    for link in list(setor.links_bi.all()):
        excluir_link_em_cascata(link)
    for funcionario in list(setor.funcionarios.select_related("usuario").all()):
        excluir_usuario_em_cascata(funcionario.usuario)
    setor.delete()
