"""Testes do serviço de consolidação de lote (domain/services/consolidador.py)."""

from datetime import date
from decimal import Decimal

from motor_cambial.domain.enums import Fonte, Moeda, TipoExposicao, TipoTaxa
from motor_cambial.domain.models import Exposicao
from motor_cambial.domain.resultado import Conversao, PosicaoAvaliada, StatusPosicao
from motor_cambial.domain.rules.divergencia import Divergencia
from motor_cambial.domain.services.consolidador import consolidar


def _conversao(fonte, moeda, valor_brl, tipo_taxa):
    return Conversao(
        fonte=fonte,
        moeda=moeda,
        valor_origem=Decimal("1000"),
        data_solicitada=date(2026, 6, 5),
        data_efetiva=date(2026, 6, 5),
        houve_fallback=False,
        defasagem_dias=0,
        tipo_taxa=tipo_taxa,
        taxa_aplicada=Decimal("5.00"),
        valor_brl=valor_brl,
    )


def _consolidada(id, moeda, tipo, brl_ptax, brl_frank, abs_brl, pct):
    return PosicaoAvaliada(
        exposicao=Exposicao(
            id=id, tipo=tipo, moeda=moeda, valor="1000", vencimento=date(2026, 6, 5)
        ),
        status=StatusPosicao.CONSOLIDADA,
        conversao_ptax=_conversao(Fonte.PTAX, moeda, brl_ptax, TipoTaxa.VENDA),
        conversao_frankfurter=_conversao(
            Fonte.FRANKFURTER, moeda, brl_frank, TipoTaxa.REFERENCIA
        ),
        divergencia=Divergencia(percentual=pct, absoluta_brl=abs_brl),
    )


def _parcial(id, moeda, tipo, erro_frankfurter="fonte fora do ar"):
    return PosicaoAvaliada(
        exposicao=Exposicao(
            id=id, tipo=tipo, moeda=moeda, valor="1000", vencimento=date(2026, 6, 5)
        ),
        status=StatusPosicao.PARCIAL,
        conversao_ptax=_conversao(Fonte.PTAX, moeda, Decimal("5000.00"), TipoTaxa.VENDA),
        erro_frankfurter=erro_frankfurter,
    )


def test_lote_vazio_gera_visao_vazia():
    visao = consolidar([])
    assert visao.totais_por_moeda == ()
    assert visao.posicao_liquida_por_natureza == ()
    assert visao.top_divergencias == ()
    assert visao.posicoes_nao_avaliadas == ()


def test_total_por_moeda_soma_as_duas_fontes():
    posicoes = [
        _consolidada("1", Moeda.USD, TipoExposicao.PAYABLE,
                     Decimal("5000.00"), Decimal("5050.00"), Decimal("50.00"), Decimal("1")),
        _consolidada("2", Moeda.USD, TipoExposicao.PAYABLE,
                     Decimal("3000.00"), Decimal("2900.00"), Decimal("100.00"), Decimal("3.3")),
    ]
    visao = consolidar(posicoes)
    assert len(visao.totais_por_moeda) == 1
    total = visao.totais_por_moeda[0]
    assert total.moeda is Moeda.USD
    assert total.total_brl_ptax == Decimal("8000.00")
    assert total.total_brl_frankfurter == Decimal("7950.00")
    assert total.quantidade_posicoes == 2


def test_multiplas_moedas_na_ordem_de_primeira_aparicao():
    posicoes = [
        _consolidada("1", Moeda.USD, TipoExposicao.PAYABLE,
                     Decimal("5000.00"), Decimal("5000.00"), Decimal("0"), Decimal("0")),
        _consolidada("2", Moeda.EUR, TipoExposicao.RECEIVABLE,
                     Decimal("6000.00"), Decimal("6000.00"), Decimal("0"), Decimal("0")),
    ]
    visao = consolidar(posicoes)
    assert [t.moeda for t in visao.totais_por_moeda] == [Moeda.USD, Moeda.EUR]


def test_posicao_liquida_por_natureza_sem_netting():
    posicoes = [
        _consolidada("1", Moeda.USD, TipoExposicao.PAYABLE,
                     Decimal("5000.00"), Decimal("5000.00"), Decimal("0"), Decimal("0")),
        _consolidada("2", Moeda.USD, TipoExposicao.RECEIVABLE,
                     Decimal("3000.00"), Decimal("3000.00"), Decimal("0"), Decimal("0")),
        _consolidada("3", Moeda.USD, TipoExposicao.INTERCOMPANY,
                     Decimal("9000.00"), Decimal("9000.00"), Decimal("0"), Decimal("0")),
    ]
    visao = consolidar(posicoes)
    por_tipo = {t.tipo: t.total_brl for t in visao.posicao_liquida_por_natureza}
    assert por_tipo[TipoExposicao.PAYABLE] == Decimal("5000.00")
    assert por_tipo[TipoExposicao.RECEIVABLE] == Decimal("3000.00")
    assert por_tipo[TipoExposicao.INTERCOMPANY] == Decimal("9000.00")


def test_top_3_pega_as_tres_maiores_divergencias_absolutas():
    posicoes = [
        _consolidada("a", Moeda.USD, TipoExposicao.PAYABLE,
                     Decimal("100.00"), Decimal("110.00"), Decimal("10.00"), Decimal("10")),
        _consolidada("b", Moeda.USD, TipoExposicao.PAYABLE,
                     Decimal("100.00"), Decimal("150.00"), Decimal("50.00"), Decimal("50")),
        _consolidada("c", Moeda.USD, TipoExposicao.PAYABLE,
                     Decimal("100.00"), Decimal("130.00"), Decimal("30.00"), Decimal("30")),
        _consolidada("d", Moeda.USD, TipoExposicao.PAYABLE,
                     Decimal("100.00"), Decimal("105.00"), Decimal("5.00"), Decimal("5")),
        _consolidada("e", Moeda.USD, TipoExposicao.PAYABLE,
                     Decimal("100.00"), Decimal("140.00"), Decimal("40.00"), Decimal("40")),
    ]
    visao = consolidar(posicoes)
    assert [t.exposicao_id for t in visao.top_divergencias] == ["b", "e", "c"]


def test_top_3_com_menos_de_tres_retorna_o_que_houver():
    posicoes = [
        _consolidada("a", Moeda.USD, TipoExposicao.PAYABLE,
                     Decimal("100.00"), Decimal("110.00"), Decimal("10.00"), Decimal("10")),
        _consolidada("b", Moeda.USD, TipoExposicao.PAYABLE,
                     Decimal("100.00"), Decimal("150.00"), Decimal("50.00"), Decimal("50")),
    ]
    visao = consolidar(posicoes)
    assert len(visao.top_divergencias) == 2


def test_empate_de_divergencia_preserva_ordem_de_entrada():
    posicoes = [
        _consolidada("a", Moeda.USD, TipoExposicao.PAYABLE,
                     Decimal("100.00"), Decimal("120.00"), Decimal("20.00"), Decimal("20")),
        _consolidada("b", Moeda.USD, TipoExposicao.PAYABLE,
                     Decimal("100.00"), Decimal("120.00"), Decimal("20.00"), Decimal("20")),
    ]
    visao = consolidar(posicoes)
    assert [t.exposicao_id for t in visao.top_divergencias] == ["a", "b"]


def test_parcial_fica_fora_dos_totais_e_vai_para_nao_avaliadas():
    posicoes = [
        _consolidada("1", Moeda.USD, TipoExposicao.PAYABLE,
                     Decimal("5000.00"), Decimal("5050.00"), Decimal("50.00"), Decimal("1")),
        _parcial("2", Moeda.USD, TipoExposicao.PAYABLE),
    ]
    visao = consolidar(posicoes)
    assert visao.totais_por_moeda[0].quantidade_posicoes == 1
    assert len(visao.top_divergencias) == 1
    assert len(visao.posicoes_nao_avaliadas) == 1
    nao_avaliada = visao.posicoes_nao_avaliadas[0]
    assert nao_avaliada.exposicao_id == "2"
    assert nao_avaliada.status is StatusPosicao.PARCIAL
    assert nao_avaliada.erro_frankfurter == "fonte fora do ar"


def test_determinismo_mesma_entrada_mesma_saida():
    posicoes = [
        _consolidada("1", Moeda.USD, TipoExposicao.PAYABLE,
                     Decimal("5000.00"), Decimal("5050.00"), Decimal("50.00"), Decimal("1")),
        _parcial("2", Moeda.EUR, TipoExposicao.RECEIVABLE),
    ]
    assert consolidar(posicoes) == consolidar(posicoes)
