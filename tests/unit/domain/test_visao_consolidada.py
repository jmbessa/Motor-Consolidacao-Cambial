"""Testes dos modelos da visão consolidada (agregados de lote)."""

from decimal import Decimal

import pytest
from pydantic import ValidationError

from motor_cambial.domain.enums import Moeda, TipoExposicao
from motor_cambial.domain.resultado import StatusPosicao
from motor_cambial.domain.visao_consolidada import (
    PosicaoNaoAvaliada,
    TopDivergencia,
    TotalMoeda,
    TotalNatureza,
    VisaoConsolidada,
)


def test_total_moeda_valido():
    total = TotalMoeda(
        moeda=Moeda.USD,
        total_brl_ptax=Decimal("8000.00"),
        total_brl_frankfurter=Decimal("7950.00"),
        quantidade_posicoes=2,
    )
    assert total.moeda is Moeda.USD
    assert total.total_brl_ptax == Decimal("8000.00")
    assert total.quantidade_posicoes == 2


def test_total_moeda_rejeita_quantidade_zero():
    with pytest.raises(ValidationError):
        TotalMoeda(
            moeda=Moeda.USD,
            total_brl_ptax=Decimal("1"),
            total_brl_frankfurter=Decimal("1"),
            quantidade_posicoes=0,
        )


def test_total_moeda_rejeita_total_float():
    with pytest.raises(ValidationError):
        TotalMoeda(
            moeda=Moeda.USD,
            total_brl_ptax=8000.0,
            total_brl_frankfurter=Decimal("1"),
            quantidade_posicoes=1,
        )


def test_total_moeda_e_imutavel():
    total = TotalMoeda(
        moeda=Moeda.USD,
        total_brl_ptax=Decimal("1"),
        total_brl_frankfurter=Decimal("1"),
        quantidade_posicoes=1,
    )
    with pytest.raises(ValidationError):
        total.total_brl_ptax = Decimal("2")


def test_total_natureza_valido():
    total = TotalNatureza(
        tipo=TipoExposicao.PAYABLE,
        total_brl=Decimal("5000.00"),
        quantidade_posicoes=1,
    )
    assert total.tipo is TipoExposicao.PAYABLE
    assert total.total_brl == Decimal("5000.00")


def test_top_divergencia_aceita_divergencia_zero():
    # duas fontes concordam: divergência 0 é um valor legítimo (não > 0).
    top = TopDivergencia(
        exposicao_id="1",
        divergencia_absoluta_brl=Decimal("0"),
        divergencia_percentual=Decimal("0"),
    )
    assert top.divergencia_absoluta_brl == Decimal("0")


def test_top_divergencia_rejeita_float():
    with pytest.raises(ValidationError):
        TopDivergencia(
            exposicao_id="1",
            divergencia_absoluta_brl=10.0,
            divergencia_percentual=Decimal("1"),
        )


def test_posicao_nao_avaliada_aceita_parcial():
    p = PosicaoNaoAvaliada(
        exposicao_id="7",
        status=StatusPosicao.PARCIAL,
        erro_frankfurter="fonte fora do ar",
    )
    assert p.status is StatusPosicao.PARCIAL
    assert p.erro_ptax is None


def test_posicao_nao_avaliada_aceita_falha():
    p = PosicaoNaoAvaliada(
        exposicao_id="7",
        status=StatusPosicao.FALHA,
        erro_ptax="timeout",
        erro_frankfurter="moeda não suportada",
    )
    assert p.status is StatusPosicao.FALHA


def test_posicao_nao_avaliada_rejeita_consolidada():
    with pytest.raises(ValidationError):
        PosicaoNaoAvaliada(
            exposicao_id="7",
            status=StatusPosicao.CONSOLIDADA,
        )


def test_visao_consolidada_vazia():
    visao = VisaoConsolidada(
        totais_por_moeda=(),
        posicao_liquida_por_natureza=(),
        top_divergencias=(),
        posicoes_nao_avaliadas=(),
    )
    assert visao.totais_por_moeda == ()
    assert visao.top_divergencias == ()


def test_visao_consolidada_e_imutavel():
    visao = VisaoConsolidada(
        totais_por_moeda=(),
        posicao_liquida_por_natureza=(),
        top_divergencias=(),
        posicoes_nao_avaliadas=(),
    )
    with pytest.raises(ValidationError):
        visao.top_divergencias = ()


def test_visao_consolidada_rejeita_campo_extra():
    with pytest.raises(ValidationError):
        VisaoConsolidada(
            totais_por_moeda=(),
            posicao_liquida_por_natureza=(),
            top_divergencias=(),
            posicoes_nao_avaliadas=(),
            campo_indevido="x",
        )
