"""Serviço puro de conversão de uma exposição para BRL, por fonte.

Aplica, em sequência: seleção do lado da taxa por tipo de exposição
(``tipo_taxa_para``), fallback de data sobre as cotações disponíveis
(``resolver_data_efetiva``) e a taxa da cotação resolvida
(``CotacaoNormalizada.taxa_para``). A multiplicação ocorre em precisão
plena; só o valor final em BRL é quantizado (``quantizar_brl``) — nunca as
taxas, que preservam a precisão da fonte.
"""

from __future__ import annotations

from datetime import date

from motor_cambial.domain.decimal_utils import quantizar_brl
from motor_cambial.domain.models import CotacaoNormalizada, Exposicao
from motor_cambial.domain.resultado import Conversao
from motor_cambial.domain.rules.fallback_data import resolver_data_efetiva
from motor_cambial.domain.rules.selecao_taxa import tipo_taxa_para


def converter(
    exposicao: Exposicao,
    cotacoes: list[CotacaoNormalizada],
    data_referencia: date,
    janela_dias: int,
) -> Conversao:
    """Converte uma exposição para BRL usando as cotações de UMA fonte.

    ``cotacoes`` deve conter só cotações da moeda de ``exposicao`` (o
    chamador garante isso ao buscar por ``exposicao.moeda``). Levanta
    ``SemCotacaoNaJanela`` se nenhuma data em ``cotacoes`` cair dentro da
    janela retroativa a partir de ``data_referencia``.
    """
    tipo_taxa = tipo_taxa_para(exposicao.tipo)
    por_data = {c.data_referencia: c for c in cotacoes}
    fallback = resolver_data_efetiva(
        data_solicitada=data_referencia,
        datas_disponiveis=por_data.keys(),
        janela_dias=janela_dias,
    )
    cotacao = por_data[fallback.data_efetiva]
    taxa = cotacao.taxa_para(tipo_taxa)
    valor_brl = quantizar_brl(exposicao.valor * taxa)
    return Conversao(
        fonte=cotacao.fonte,
        moeda=exposicao.moeda,
        valor_origem=exposicao.valor,
        data_solicitada=data_referencia,
        data_efetiva=fallback.data_efetiva,
        houve_fallback=fallback.houve_fallback,
        defasagem_dias=fallback.defasagem_dias,
        tipo_taxa=tipo_taxa,
        taxa_aplicada=taxa,
        valor_brl=valor_brl,
    )
