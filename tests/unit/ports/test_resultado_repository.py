"""Testes estruturais do port ResultadoRepository."""

from datetime import date

from motor_cambial.ports.resultado_repository import ResultadoRepository


def test_implementacao_conforme_passa_isinstance():
    class _Repo:
        def salvar(self, resultado):
            ...

        def buscar(self, data_referencia, hash_conjunto):
            ...

        def buscar_historico(self, data_referencia, hash_conjunto):
            ...

    assert isinstance(_Repo(), ResultadoRepository)


def test_implementacao_incompleta_falha_isinstance():
    class _Incompleto:
        def salvar(self, resultado):
            ...

    assert not isinstance(_Incompleto(), ResultadoRepository)
