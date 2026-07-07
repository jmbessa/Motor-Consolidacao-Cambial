"""Testes da regra de seleção de taxa por tipo de exposição (req. 6.8/6.9)."""

import pytest

from motor_cambial.domain.enums import TipoExposicao, TipoTaxa
from motor_cambial.domain.rules.selecao_taxa import tipo_taxa_para


def test_payable_usa_taxa_de_venda():
    # Para liquidar, a empresa compra a moeda: taxa mais conservadora p/ saída de caixa.
    assert tipo_taxa_para(TipoExposicao.PAYABLE) is TipoTaxa.VENDA


def test_receivable_usa_taxa_de_compra():
    # Ao receber, a empresa vende a moeda: taxa coerente com a entrada de caixa.
    assert tipo_taxa_para(TipoExposicao.RECEIVABLE) is TipoTaxa.COMPRA


def test_intercompany_usa_taxa_de_referencia():
    # Operação interna ao grupo não cruza o spread de mercado: usa o mid.
    assert tipo_taxa_para(TipoExposicao.INTERCOMPANY) is TipoTaxa.REFERENCIA


def test_aceita_valor_string_do_enum():
    assert tipo_taxa_para("payable") is TipoTaxa.VENDA


def test_rejeita_tipo_invalido():
    with pytest.raises(ValueError):
        tipo_taxa_para("hedge")
