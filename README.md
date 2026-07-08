# Motor de Consolidação Cambial para Tesouraria

> Recebe uma lista de **exposições cambiais** (compromissos financeiros futuros em moeda
> estrangeira — `payable`, `receivable`, `intercompany`) e produz uma **visão consolidada em
> BRL** usando **duas fontes de cotação independentes** (PTAX/BCB e Frankfurter/BCE),
> destacando **divergências** e **alertas de materialidade**.

Teste técnico de Engenharia de Tesouraria (VTEX). A prioridade do projeto é **decisões
conscientes e bem justificadas** — as justificativas técnicas e financeiras estão em
[`DECISOES.md`](DECISOES.md).

---

## Visão geral

O motor carrega exposições de um arquivo JSON local e, para cada uma:

1. Busca a cotação **PTAX** (BCB, OData) e a cotação de referência **Frankfurter** (BCE) para a moeda e a data.
2. Converte o valor para BRL por **cada fonte**, escolhendo o tipo de taxa conforme a natureza da exposição (payable → venda; receivable → compra; intercompany → mid — ver [`DECISOES.md`](DECISOES.md)).
3. Calcula a **divergência** absoluta e percentual entre as duas visões.
4. Consolida **totais por moeda**, **posição por natureza** e **top 3 divergências**, e gera **alertas** (> 1,5% **ou** > R$ 10.000 por posição, limites configuráveis).
5. **Persiste** o resultado em MySQL de forma **idempotente** (reprocessar a mesma data com o mesmo conjunto não duplica o registro atual; o histórico é append-only) e **exporta** o resultado completo em JSON.

Entrega atual: **CLI + relatório de console + JSON exportado + persistência MySQL**.
Arquitetura **Hexagonal** (`adapters → application → domain`, domínio puro, sem I/O). Uma
API REST e um front-end web são um **diferencial não implementado** (ver
[Escopo e limitações](#escopo-limitações-e-o-que-faria-diferente)).

---

## Pré-requisitos

| Ferramenta | Para quê | Observação |
|---|---|---|
| **Docker** | Rodar o MySQL (persistência) | Inicie o Docker Desktop **antes** de `make run`/`make up`. |
| **Python 3.12+** | Rodar a aplicação (venv) | — |
| **Make** | Porta de entrada única | Padrão em Linux/macOS; no Windows, disponível via Git Bash, Chocolatey ou WSL. |

> A aplicação roda a partir de um **venv local** e conecta no **MySQL em container**. Não há
> container para a aplicação nesta entrega (é um dos pontos de "o que faria diferente").

---

## Rodar em menos de 5 minutos

```bash
make install    # cria o venv (.venv) e instala as dependências
make run         # sobe o MySQL (Docker), aplica o schema e roda a CLI com os defaults
```

`make run` imprime o **relatório no console** e grava o **JSON completo** em
`data/output/consolidacao_<data>.json`.

> **Primeira execução (máquina fria):** o `make up` baixa a imagem `mysql:8.0` (~150 MB) e
> inicializa o volume — isso pode levar 1–2 min conforme a rede; as execuções seguintes são
> quase instantâneas. Se você já tiver um MySQL local ocupando a porta `3306`, pare-o antes
> (o container publica `3306:3306`).

**Prova instantânea, sem Docker** (valida o núcleo de cálculo/conversão):

```bash
make test        # 295 testes unitários (~1s), sem rede nem banco
```

Um exemplo de saída já vem versionado em [`examples/`](examples/), para inspeção sem rodar nada.

---

## Modo live vs. cache

O enunciado permite cache local, mas exige um **modo live demonstrável**. Ambos existem:

| Comando | Comportamento |
|---|---|
| `make run` | **Cache-first**: na 1ª execução bate nas APIs reais e popula `data/cache/`; nas seguintes serve do cache (rápido, offline). |
| `make run-live` | **Sempre ao vivo**: ignora o cache e consulta PTAX e Frankfurter a cada execução (`--live`). |

Como `data/cache/` não é versionado, a **primeira** `make run` de um checkout limpo já
consome as duas APIs de verdade.

---

## Uso da CLI

A CLI é um comando único (não há subcomando). Todas as opções têm default — rodar sem flags
consolida `data/exposicoes.json` para a data de hoje.

| Flag | Default | Descrição |
|---|---|---|
| `--arquivo` | `data/exposicoes.json` | Arquivo JSON de exposições. |
| `--data` | hoje | Data de referência (`YYYY-MM-DD`). **Reprocessamento por data.** |
| `--live` / `--cache` | `--cache` | Busca ao vivo (ignora o cache) vs. cache-first. |
| `--limite-percentual` | `1.5` | Limite percentual de alerta (configurável). |
| `--limite-absoluto` | `10000` | Limite absoluto em BRL de alerta (configurável). |
| `--janela-dias` | `7` | Janela do fallback de data (dias retrocedidos). |
| `--saida` | `data/output/consolidacao_{data}.json` | Caminho do JSON exportado. |

### Reprocessar uma data informada pelo usuário

Para rodar com flags customizadas, suba o banco e invoque a CLI a partir do venv apontando
para o MySQL local:

```bash
make up                       # garante o MySQL de pé (Docker)
make migrate                  # aplica o schema (idempotente)
```

Ative o venv e rode (o `MOTOR_DB_HOST=127.0.0.1` faz o venv do host achar o MySQL do container):

```bash
# Linux / macOS
source .venv/bin/activate
MOTOR_DB_HOST=127.0.0.1 python -m motor_cambial.adapters.inbound.cli.app \
  --data 2026-07-03 --live --limite-percentual 2.0
```

```powershell
# Windows (PowerShell)
.venv\Scripts\Activate.ps1
$env:MOTOR_DB_HOST = "127.0.0.1"
python -m motor_cambial.adapters.inbound.cli.app --data 2026-07-03 --live --limite-percentual 2.0
```

Reprocessar a **mesma data com o mesmo conjunto de exposições** é **idempotente**: o registro
atual é sobrescrito (não duplicado) e o histórico de reprocessamentos é preservado
(append-only). Ver [Idempotência](DECISOES.md#6-rastreabilidade-e-auditoria).

---

## O que o relatório entrega

O relatório de console tem estas seções (cada uma omitida se vazia):

- **Posições** — um bloco por exposição: o valor original e, para **cada fonte** (PTAX e Frankfurter), a data efetiva, a taxa aplicada (com o tipo — compra/venda/mid) e o BRL convertido; mais a divergência (% e absoluta) e o alerta.
- **Totais por moeda** — soma em BRL por moeda, pelas duas fontes.
- **Posição líquida por natureza** — soma por `payable` / `receivable` / `intercompany` (âncora PTAX).
- **Top divergências** — as 3 exposições com maior diferença absoluta em BRL entre as fontes.
- **Posições não avaliadas** — exposições com status `PARCIAL`/`FALHA` e o motivo (moeda não suportada, sem cotação na janela, etc.), mantidas **fora** dos totais para não contaminar a consolidação.

O **JSON exportado** (`data/output/…json`) é o registro exaustivo: cada posição carrega as
duas conversões completas com a **trilha de rastreabilidade** (fonte, data efetiva, tipo de
taxa, se houve fallback e a defasagem em dias).

---

## Arquitetura

Monólito modular, estilo **Hexagonal (Ports & Adapters)**. Regra de dependência inviolável:
`adapters → application → domain`. O **domínio é puro** (sem I/O, sem framework); as bordas o
implementam via ports (`Protocol`). Injeção de dependências manual em `composition_root.py`.

```
src/motor_cambial/
  domain/        # PURO: models, enums, rules/ (selecao_taxa, fallback_data, alertas,
                 #        divergencia, idempotencia), services/ (conversor, consolidador)
  ports/         # interfaces: cotacao_provider, resultado_repository
  application/   # use_cases/: consolidar_exposicoes, reprocessar_por_data
  adapters/
    inbound/cli/     # loader, relatório, app (comando `consolidar`)
    outbound/        # ptax/, frankfurter/, cache/, persistence/ (MySQL)
  config.py          # thresholds, timeouts, modo live/cache, conexão do banco
  composition_root.py
tests/           # unit/ (domínio, alvo do TDD) · integration/ (APIs + MySQL reais, opt-in)
data/            # exposicoes.json (entrada) · output/ (resultados, gerado) · cache/ (gerado)
examples/        # exemplo de output versionado
```

Detalhes e justificativas de cada decisão: [`DECISOES.md`](DECISOES.md).

---

## Testes

```bash
make test              # 295 unitários (sem rede/DB): cálculo, conversão, seleção de taxa,
                       #   fallback, alertas, divergência, idempotência, normalização, cache
make test-integration  # 8 de integração (opt-in): sobe o MySQL e bate nas APIs reais
```

Os testes de integração são **opt-in** (marcador `integration`) e requerem a variável
`MOTOR_TEST_DB_URL` — `make test-integration` a configura e sobe o banco automaticamente.

---

## Regras de negócio (resumo)

| Regra | Comportamento | Justificativa completa |
|---|---|---|
| **Payables** | Taxa de **venda** (`cotacaoVenda`) do BCB | [DECISOES.md §2](DECISOES.md#2-seleção-de-taxa-por-tipo) |
| **Receivables** | Taxa de **compra** (`cotacaoCompra`) do BCB | [DECISOES.md §2](DECISOES.md#2-seleção-de-taxa-por-tipo) |
| **Intercompany** | **Mid** `(compra+venda)/2` (premissa documentada) | [DECISOES.md §2](DECISOES.md#2-seleção-de-taxa-por-tipo) |
| **Fallback de data** | Retrocede dia a dia até achar cotação (janela configurável); rastreável | [DECISOES.md §4](DECISOES.md#4-fallback-de-data-e-moedas-não-suportadas) |
| **Alertas** | > 1,5% **ou** > R$ 10.000 por posição; limites configuráveis | [DECISOES.md §5](DECISOES.md#5-alertas-materialidade-e-priorização-de-risco) |
| **Rastreabilidade** | Cada conversão registra fonte, data efetiva e tipo de taxa | [DECISOES.md §6](DECISOES.md#6-rastreabilidade-e-auditoria) |

---

## Configuração

Defaults versionados em `src/motor_cambial/config.py`, sobrescrivíveis por variável de
ambiente (prefixo `MOTOR_`) ou por um arquivo `.env` (ver [`.env.example`](.env.example)).
Exemplos: `MOTOR_MODO_LIVE`, `MOTOR_HTTP_TIMEOUT_S`, `MOTOR_JANELA_FALLBACK_DIAS`,
`MOTOR_DB_HOST`. Onde há flag de CLI equivalente (`--live/--cache`, `--janela-dias`,
`--limite-percentual`, `--limite-absoluto`), a **flag tem precedência** sobre a env var quando
informada; omitida, vale a env var (ou o default versionado).

---

## Uso de IA generativa

Este projeto foi desenvolvido com uso explícito e rastreado de IA generativa (Claude Code),
seguindo uma metodologia **spec-driven** de três fases (plano → TDD → revisão adversarial).
O registro de **quais** skills/agentes foram usados e **em que fase** está em
[`.claude/skills/README.md`](.claude/skills/README.md).

---

## Escopo, limitações e o que faria diferente

**Nesta entrega (consciente):**

- **CLI-only.** A API REST e o front-end web (diferencial) não foram implementados; a CLI já
  cumpre todo o entregável funcional do enunciado.
- **Só o MySQL em container.** A aplicação roda do venv. Conteinerizar a app (e um
  `docker compose up` de caminho único) é o próximo passo natural.
- **Schema por `create_all`**, não por migrações versionadas (Alembic fora de escopo para o prazo).
- **Concorrência fora de escopo** — assume escritor único na persistência.
- **Moedas** restritas ao conjunto suportado pelas fontes (enum fechado; moeda fora do
  conjunto vira erro explícito e rastreável, não silencioso).

**Com mais tempo:** API REST + front-end; app conteinerizada; migrações versionadas; um modo
de demo sem Docker; e opção de netting real por natureza. Detalhes em
[DECISOES.md §9](DECISOES.md#9-trade-offs-e-o-que-faria-diferente-com-mais-tempo).
