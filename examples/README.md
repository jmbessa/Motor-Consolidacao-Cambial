# Exemplo de output

[`consolidacao-exemplo.json`](consolidacao-exemplo.json) é um **output real**, gerado ao vivo
contra as APIs PTAX/BCB e Frankfurter/BCE e persistido no MySQL. É o JSON exportado por uma
execução da CLI sobre as 5 exposições do enunciado ([`../data/exposicoes.json`](../data/exposicoes.json)).

## Como foi gerado

```bash
make migrate   # sobe o MySQL (Docker) e aplica o schema
# a partir do venv, apontando para o MySQL local:
MOTOR_DB_HOST=127.0.0.1 python -m motor_cambial.adapters.inbound.cli.app --data 2026-07-05 --live
```

A data de referência escolhida (**2026-07-05, um domingo**) foi proposital: sem cotação no fim
de semana, o exemplo demonstra o **fallback de data rastreável**.

## O que este exemplo demonstra

- **Conversão pelas duas fontes** — cada posição traz `conversao_ptax` e
  `conversao_frankfurter`, com `valor_brl` e `taxa_aplicada` (Decimal, sem perda de precisão).
- **Seleção de taxa por tipo** (campo `tipo_taxa`) — `payable → venda`, `receivable → compra`,
  `intercompany → referencia` (mid). Ver [`../DECISOES.md`](../DECISOES.md).
- **Fallback rastreável** — `data_solicitada: 2026-07-05` → `data_efetiva: 2026-07-03`,
  `houve_fallback: true`, `defasagem_dias: 2`. Ambas as fontes recuaram para a mesma sexta,
  então `datas_efetivas_divergem: false`.
- **Divergência** absoluta e percentual por posição, **top 3 divergências**, **totais por
  moeda** e **posição líquida por natureza** (bloco `visao`).
- **Idempotência** — `hash_conjunto` é a chave natural (junto com `data_referencia`) que
  garante o reprocessamento sem duplicar o registro atual.

## Sobre os alertas

Neste exemplo, `alertas` está vazio em todas as posições: com os limites default (**1,5%** ou
**R$ 10.000**), nenhuma posição rompe o limiar — PTAX e Frankfurter divergem pouco (aqui,
~0,45%–0,59%, e no máximo R$ 7.440 na maior posição). Isso é **realista**: as duas fontes
seguem o mesmo mercado de perto. Os limites são **configuráveis**; para ver um alerta disparar
com estes mesmos dados, basta apertar o limite absoluto:

```bash
MOTOR_DB_HOST=127.0.0.1 python -m motor_cambial.adapters.inbound.cli.app \
  --data 2026-07-05 --live --limite-absoluto 5000
```

A lógica de alerta (semântica **OU**, `>` estrito, limites configuráveis) é coberta por testes
unitários dedicados (`tests/unit/domain/test_alertas.py`).
