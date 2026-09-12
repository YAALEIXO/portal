import logging

from django.contrib import messages
from django.db import DatabaseError
from django.http import HttpResponseRedirect
from django.utils import timezone

from .models import Usuario

INTERVALO_ATUALIZACAO = 60  # segundos; evita um UPDATE a cada request

logger = logging.getLogger(__name__)


class AtualizarUltimoAcessoMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        user = getattr(request, "user", None)
        if user is not None and user.is_authenticated:
            agora = timezone.now()
            if not user.last_seen or (agora - user.last_seen).total_seconds() > INTERVALO_ATUALIZACAO:
                Usuario.objects.filter(pk=user.pk).update(last_seen=agora)
        return response


class TratarErroDeBancoMiddleware:
    """Rede de segurança para qualquer CRUD: se uma view deixar subir um erro de
    banco (registro duplicado, chave protegida etc.) sem tratar, evita a página
    de erro do Django e volta para a página anterior com um aviso discreto."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        if not isinstance(exception, DatabaseError):
            return None
        logger.exception("Erro de banco de dados não tratado em %s", request.path)
        messages.error(
            request,
            "Não foi possível concluir a operação: os dados informados geram um conflito "
            "(ex.: registro duplicado ou vinculado a outro). Nada foi salvo.",
        )
        destino = request.META.get("HTTP_REFERER") or "/"
        return HttpResponseRedirect(destino)
