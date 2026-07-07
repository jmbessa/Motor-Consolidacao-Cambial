"""Testes das funções puras de desserialização do adapter de persistência (sem DB)."""

from datetime import date, datetime, timezone
from decimal import Decimal

import pytest

from motor_cambial.adapters.outbound.persistence.repository import (
    RepositorioResultadoSQL,
)
from motor_cambial.domain.enums import Fonte, Moeda, TipoExposicao, TipoTaxa
from motor_cambial.domain.errors import RespostaInvalida
from motor_cambial.domain.models import Exposicao
from motor_cambial.domain.resultado import Conversao, PosicaoAvaliada, StatusPosicao
from motor_cambial.domain.resultado_consolidacao import ResultadoConsolidacao
from motor_cambial.domain.rules.divergencia import Divergencia
from motor_cambial.domain.services.consolidador import consolidar


def _payload_valido():
    def _conv(fonte, tipo_taxa, taxa):
        return Conversao(
            fonte=fonte, moeda=Moeda.USD, valor_origem=Decimal("1000"),
            data_solicitada=date(2026, 6, 5), data_efetiva=date(2026, 6, 5),
            houve_fallback=False, defasagem_dias=0, tipo_taxa=tipo_taxa,
            taxa_aplicada=Decimal(taxa), valor_brl=Decimal("5100.00"),
        )

    posicao = PosicaoAvaliada(
        exposicao=Exposicao(id="1", tipo=TipoExposicao.PAYABLE, moeda=Moeda.USD,
                            valor="1000", vencimento=date(2026, 6, 5)),
        status=StatusPosicao.CONSOLIDADA,
        conversao_ptax=_conv(Fonte.PTAX, TipoTaxa.VENDA, "5.10"),
        conversao_frankfurter=_conv(Fonte.FRANKFURTER, TipoTaxa.REFERENCIA, "5.05"),
        divergencia=Divergencia(percentual=Decimal("0"), absoluta_brl=Decimal("0")),
    )
    resultado = ResultadoConsolidacao(
        data_referencia=date(2026, 6, 5), hash_conjunto="a" * 64,
        posicoes=(posicao,), visao=consolidar([posicao]),
    )
    return resultado.model_dump(mode="json")


def test_desserializar_payload_valido():
    resultado = RepositorioResultadoSQL._desserializar(_payload_valido())
    assert isinstance(resultado, ResultadoConsolidacao)


def test_desserializar_payload_corrompido_levanta_resposta_invalida():
    with pytest.raises(RespostaInvalida):
        RepositorioResultadoSQL._desserializar({"lixo": "invalido"})


def test_registro_historico_payload_valido():
    reg = RepositorioResultadoSQL._para_registro_historico(
        _payload_valido(),
        datetime(2026, 7, 7, 12, 0, tzinfo=timezone.utc),
        1,
    )
    assert reg.num_processamento == 1


def test_registro_historico_num_invalido_levanta_resposta_invalida():
    # num_processamento <= 0 quebra o validador de RegistroHistorico -> deve virar RespostaInvalida
    with pytest.raises(RespostaInvalida):
        RepositorioResultadoSQL._para_registro_historico(
            _payload_valido(),
            datetime(2026, 7, 7, 12, 0, tzinfo=timezone.utc),
            0,
        )


def test_registro_historico_processado_em_naive_levanta_resposta_invalida():
    with pytest.raises(RespostaInvalida):
        RepositorioResultadoSQL._para_registro_historico(
            _payload_valido(),
            datetime(2026, 7, 7, 12, 0),  # naive
            1,
        )
