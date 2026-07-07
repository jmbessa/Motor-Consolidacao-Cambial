"""Modelos da visão consolidada de um lote de posições (agregados).

Agrega ``PosicaoAvaliada`` (Fatia 4) na visão que a tesouraria consome:
totais por moeda (comparando PTAX e Frankfurter), posição líquida por
natureza (payable/receivable/intercompany, cada uma seu próprio total, sem
netting) e as top 3 exposições com maior diferença financeira absoluta
entre as duas fontes. Posições que não foram totalmente consolidadas ficam
listadas à parte (``PosicaoNaoAvaliada``) com o motivo — os agregados nunca
incluem dado incompleto.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, model_validator

from motor_cambial.domain.decimal_utils import DecimalPositivo, DecimalSeguro
from motor_cambial.domain.enums import Moeda, TipoExposicao
from motor_cambial.domain.resultado import StatusPosicao


class TotalMoeda(BaseModel):
    """Total consolidado de uma moeda, comparando as duas fontes."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    moeda: Moeda
    total_brl_ptax: DecimalPositivo
    total_brl_frankfurter: DecimalPositivo
    quantidade_posicoes: int = Field(ge=1)


class TotalNatureza(BaseModel):
    """Total consolidado de uma natureza (payable/receivable/intercompany).

    Sem netting: cada natureza é o seu próprio total (lado PTAX, âncora
    oficial). Responde separadamente ao impacto cambial sobre contas a pagar
    e a receber.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    tipo: TipoExposicao
    total_brl: DecimalPositivo
    quantidade_posicoes: int = Field(ge=1)


class TopDivergencia(BaseModel):
    """Uma das exposições com maior diferença financeira entre as fontes."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    exposicao_id: str
    divergencia_absoluta_brl: DecimalSeguro
    divergencia_percentual: DecimalSeguro


class PosicaoNaoAvaliada(BaseModel):
    """Posição PARCIAL/FALHA excluída dos agregados, com o motivo preservado."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    exposicao_id: str
    status: StatusPosicao
    erro_ptax: str | None = None
    erro_frankfurter: str | None = None

    @model_validator(mode="after")
    def _valida_nao_consolidada(self) -> "PosicaoNaoAvaliada":
        if self.status is StatusPosicao.CONSOLIDADA:
            raise ValueError(
                "PosicaoNaoAvaliada não pode ter status CONSOLIDADA"
            )
        return self


class VisaoConsolidada(BaseModel):
    """Visão de lote: totais por moeda, posição líquida, top 3 e não avaliadas."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    totais_por_moeda: tuple[TotalMoeda, ...]
    posicao_liquida_por_natureza: tuple[TotalNatureza, ...]
    top_divergencias: tuple[TopDivergencia, ...]
    posicoes_nao_avaliadas: tuple[PosicaoNaoAvaliada, ...]
