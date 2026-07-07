"""Regra de identidade de um run: hash do conjunto de exposições.

A idempotência do reprocessamento (requisito do enunciado) usa como chave
natural ``(data_referencia, hash_do_conjunto)``. O hash cobre apenas os
campos de identidade financeira de cada exposição — ``id``, ``tipo``,
``moeda``, ``valor``, ``vencimento`` — e **ignora ``descricao``** (rótulo,
não identidade). É determinístico, independente da ordem da lista, e
compara ``valor`` por valor (``125000`` e ``125000.00`` colidem de
propósito, pois são o mesmo compromisso) — a canonização de ``valor``
roda num contexto ``Decimal`` de precisão fixa, para não depender do
contexto ambiente (``decimal.getcontext()``). A canonização usa JSON para
escapar qualquer caractere especial em ``id`` — nada de concatenação
ingênua que poderia colidir (ex.: "a"+"bc" vs "ab"+"c").
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable
from decimal import localcontext

from motor_cambial.domain.models import Exposicao


def _canonico(exposicao: Exposicao) -> list[str]:
    with localcontext() as ctx:
        ctx.prec = 50  # fixa a precisão: normalize() não depende do contexto Decimal ambiente
        valor_canon = format(exposicao.valor.normalize(), "f")
    return [
        exposicao.id,
        exposicao.tipo.value,
        exposicao.moeda.value,
        valor_canon,  # valor por valor (sem escala)
        exposicao.vencimento.isoformat(),
    ]


def hash_do_conjunto(exposicoes: Iterable[Exposicao]) -> str:
    """Hash SHA-256 (hex) determinístico e independente de ordem do conjunto."""
    itens = sorted(_canonico(e) for e in exposicoes)
    blob = json.dumps(itens, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()
