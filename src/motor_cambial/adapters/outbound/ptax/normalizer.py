"""Normalização de payloads da PTAX para CotacaoNormalizada (puro)."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from motor_cambial.domain.enums import Moeda
from motor_cambial.domain.errors import RespostaInvalida
from motor_cambial.domain.models import CotacaoNormalizada

_BRASILIA = ZoneInfo("America/Sao_Paulo")
_FORMATO_PTAX = "%Y-%m-%d %H:%M:%S.%f"


def normalizar_ptax(value: list[dict[str, Any]], moeda: Moeda) -> list[CotacaoNormalizada]:
    """Converte o array ``value`` da PTAX em cotações de fechamento normalizadas.

    Entradas de moedas não-USD trazem ``tipoBoletim`` (Abertura/Intermediário/
    Fechamento) — só o ``Fechamento`` importa. Entradas de USD não têm o campo
    e já são o fechamento. ``dataHoraCotacao`` é naive em horário de Brasília;
    anexamos o fuso ``America/Sao_Paulo``.
    """
    cotacoes: list[CotacaoNormalizada] = []
    for item in value:
        if "tipoBoletim" in item and item["tipoBoletim"] != "Fechamento":
            continue
        try:
            momento = datetime.strptime(item["dataHoraCotacao"], _FORMATO_PTAX).replace(
                tzinfo=_BRASILIA
            )
            compra = item["cotacaoCompra"]
            venda = item["cotacaoVenda"]
        except (KeyError, TypeError, ValueError) as exc:
            raise RespostaInvalida(f"entrada malformada na PTAX: {item!r}") from exc
        cotacoes.append(
            CotacaoNormalizada.de_ptax(
                moeda=moeda,
                data_referencia=momento.date(),
                taxa_compra=compra,
                taxa_venda=venda,
                timestamp=momento,
            )
        )
    return sorted(cotacoes, key=lambda c: c.data_referencia)
