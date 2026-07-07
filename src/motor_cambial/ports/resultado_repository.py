"""Port de persistência do resultado consolidado (contrato dos adapters de store)."""

from __future__ import annotations

from datetime import date
from typing import Protocol, runtime_checkable

from motor_cambial.domain.resultado_consolidacao import (
    RegistroHistorico,
    ResultadoConsolidacao,
)


@runtime_checkable
class ResultadoRepository(Protocol):
    """Persiste e recupera resultados de consolidação por chave natural.

    A chave natural é ``(data_referencia, hash_conjunto)``. ``salvar`` é
    idempotente: sobrescreve o registro "atual" dessa chave e acrescenta uma
    entrada à trilha de auditoria append-only, numa única transação. Levanta
    ``PersistenciaIndisponivel`` em falha de I/O; ``RespostaInvalida`` se um
    payload gravado não desserializar.
    """

    def salvar(self, resultado: ResultadoConsolidacao) -> None: ...

    def buscar(
        self, data_referencia: date, hash_conjunto: str
    ) -> ResultadoConsolidacao | None: ...

    def buscar_historico(
        self, data_referencia: date, hash_conjunto: str
    ) -> tuple[RegistroHistorico, ...]: ...
