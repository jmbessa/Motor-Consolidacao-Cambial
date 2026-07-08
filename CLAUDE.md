# CLAUDE.md

Guia de trabalho para o Claude neste repositório. Leia antes de qualquer ação.

## Sobre o projeto

**Motor de Consolidação Cambial para Tesouraria (VTEX)** — teste técnico de engenharia de software (prazo: 5 dias corridos).

Serviço que recebe uma lista de **exposições cambiais** (compromissos financeiros futuros em moeda estrangeira: `payable`, `receivable`, `intercompany`) e produz uma **visão consolidada em BRL** usando **duas fontes de cotação independentes**, destacando desvios e alertas.

**Fontes de cotação:**
- **PTAX / BCB** (OData) — cotações oficiais de compra/venda do mercado interbancário brasileiro.
- **Frankfurter** — taxas de referência do BCE (mercado europeu).
- Elas **não são equivalentes** (diferença metodológica). Tratar isso explicitamente é parte da avaliação.

**Regras de negócio (avaliadas na apresentação):**
- **Payables:** taxa mais conservadora do ponto de vista da saída de caixa. Documentar `cotacaoCompra` vs `cotacaoVenda` e justificar.
- **Receivables:** taxa coerente com a entrada de caixa esperada. Mesma exigência de documentação.
- **Fallback de data** (fim de semana/feriado): regra definida, documentada e **rastreável**.
- **Alertas:** diferença > 1,5% **ou** > BRL 10.000 por posição. Limite **configurável**.
- **Rastreabilidade:** toda conversão registra fonte, data efetiva e tipo de taxa usados.

**Requisitos de engenharia:** consumo real das APIs (modo *live* demonstrável, cache permitido), tratamento de falhas/timeout/respostas incompletas, normalização dos contratos, persistência local, **idempotência** no reprocessamento, **testes automatizados** nas partes críticas de cálculo/conversão, **README executável em < 5 min**.

> A avaliação prioriza **decisões conscientes e bem justificadas** sobre quantidade de features. O enunciado pede explicitamente para documentar **onde e como IA generativa foi usada** no desenvolvimento — registrar isso ao longo do trabalho.

## Regras de colaboração (obrigatórias)

### 1. Nunca commitar automaticamente
- **NUNCA** rode `git commit`, `git push`, `git merge` ou qualquer operação que altere o histórico sem **solicitação explícita** do usuário.
- Quando o trabalho estiver pronto para commit, **avise e proponha** a mensagem — mas espere a confirmação do usuário antes de executar.
- Isso vale também para criação de PRs, tags e branches remotos.

### 2. Metodologia: Spec-Driven Development

Toda funcionalidade do projeto passa **obrigatoriamente** por três fases, nesta ordem:

**Fase 1 — Elaboração do plano (spec)**
- Antes de escrever qualquer código de produção, elaborar um **plano de implementação** por escrito para a funcionalidade.
- O plano define: o comportamento esperado, os contratos/interfaces, os casos de borda, as regras de negócio envolvidas e a estratégia de testes.
- O plano deve ser aprovado pelo usuário antes de prosseguir.

**Fase 2 — Desenvolvimento com TDD**
- Implementar seguindo **Test-Driven Development**: teste que falha → código mínimo que passa → refatoração.
- Os testes cobrem primeiro as partes críticas de cálculo e conversão (regras de payable/receivable, fallback de data, alertas, rastreabilidade).
- Nada de escrever implementação antes do teste correspondente.

**Fase 3 — Revisão adversarial com o agente `lv10-dev`**
- Concluída a implementação de uma funcionalidade, submetê-la ao agente **`lv10-dev`** para revisão adversarial.
- O `lv10-dev` assume que o design está errado e tenta provar isso: caça falhas silenciosas, piores casos e cenários onde a convenção poderia introduzir bugs.
- Tratar os achados antes de considerar a funcionalidade concluída.

> Nenhuma funcionalidade é considerada "pronta" sem ter passado pelas três fases.

## Stack e arquitetura (decidido)

- **Linguagem:** Python 3.12+ (`Decimal` para dinheiro — nunca `float`).
- **Bibliotecas (em uso):** `pydantic`/`pydantic-settings` (modelagem/normalização/config), `httpx` (HTTP com timeout), `SQLAlchemy` + `PyMySQL` (persistência), `typer` (CLI), `pytest` (TDD). `FastAPI` + `uvicorn` seriam a base da API REST — diferencial não implementado.
- **Entrega (estado atual):** CLI + relatório de console + JSON exportado + persistência MySQL — **implementado**. API REST + front-end web são **diferencial não implementado** (planejados como Fatia 8; o enunciado trata front-end como diferencial, não requisito).
- **Arquitetura:** **monólito modular** com estilo **Hexagonal (Ports & Adapters)**. Regra de dependência inviolável: `adapters → application → domain`; o **domínio é puro** (sem I/O, sem framework) e não conhece as bordas. Ports (interfaces `Protocol`) são definidas em termos do domínio; adapters as implementam. DI manual no `composition_root.py`. Microsserviços são fora de escopo (over-engineering para o prazo e prejudica o "roda em < 5 min").
- **Execução (estado atual):** o **MySQL roda em container** (Docker Compose); a **aplicação roda do venv local** orquestrada pelo `Makefile` (`make install` + `make run`). O `README.md` documenta esse caminho e roda em < 5 min. O `docker compose up` de **caminho único com três containers** (backend + frontend + MySQL) é o **objetivo da Fatia 8** (diferencial), ainda não implementado.
- **Entrypoint:** `Makefile` como porta de entrada única. Alvos de dev (`make install`, `make test`) usam o venv; `make up`/`down`/`logs` orquestram o container MySQL; `make migrate`/`run`/`run-live`/`seed`/`test-integration` combinam o MySQL (container) com a app (venv). `make run` sobe o MySQL, aplica o schema e roda a CLI uma vez com os defaults (cache-first); `make run-live` faz o mesmo consultando as APIs ao vivo.
- **Persistência:** **MySQL 8** em container próprio como store de registro (idempotência via `UPSERT`/chave natural `data_referência + hash_do_conjunto`; reprocessamento por data), acessado por adapter atrás do port `resultado_repository`. Driver: **SQLAlchemy Core + PyMySQL**. Schema criado por `create_all` (migrações versionadas/Alembic fora de escopo) + healthcheck/espera do DB no compose. JSON exportado em `data/output/` (com um exemplo versionado em `examples/`) permanece como relatório/entregável (requisito de exemplo de output).
- **Front-end (diferencial não implementado — Fatia 8):** planejado como HTML + JS puro em container próprio (servidor estático leve, ex. nginx) consumindo a API do backend, com **CORS** habilitado.
- **Configuração:** defaults em arquivo versionado (thresholds de alerta, timeouts, modo live/cache) sobrescritíveis por env var / flag de CLI. Atende o requisito "limite configurável".

## Escopo — fora (explícito)

Autenticação/autorização · multiusuário/concorrência · banco de produção ou cloud · cotações em tempo real/streaming · suporte a moedas fora do conjunto das fontes (tratado e documentado, não implementado) · alta disponibilidade/escalabilidade horizontal.

Estrutura:

```
src/motor_cambial/
  domain/        # PURO: models, enums, rules/ (selecao_taxa, fallback_data, alertas), services/ (conversor, consolidador)
  ports/         # interfaces: cotacao_provider, resultado_repository
  application/   # use_cases/: consolidar_exposicoes, reprocessar_por_data
  adapters/
    inbound/     # cli/ (api/ = Fatia 8, não implementado)
    outbound/    # ptax/, frankfurter/, cache/, persistence/
  config.py      # thresholds (alerta configuravel), timeouts, modo live/cache
  composition_root.py
tests/           # unit (dominio, alvo do TDD) | integration (APIs + MySQL reais, opt-in)
examples/        # exemplo de output versionado
frontend/        # front-end web (Fatia 8, não implementado)
data/            # exposicoes.json (entrada) + output/ (resultados, gerado) + cache/ (gerado)
```

Rastreabilidade (fonte, data efetiva, tipo de taxa, se houve fallback) é atributo da model `Conversao` no domínio — segue o dado, não a borda.

## Skills e agentes de IA (evidência de uso)

O uso de IA generativa neste projeto é **rastreado explicitamente** em `.claude/skills/` (o enunciado cobra "onde e como você usou IA generativa? seja específico"). Ver `.claude/skills/README.md` para o índice de skills/agentes adotados e em que fase cada um entra. A metodologia spec-driven está codificada no skill de projeto `desenvolvimento-de-fatia`.

## Convenções
- Comunicação com o usuário em **português**.
- Decisões técnicas e financeiras relevantes devem ser documentadas (para README e apresentação final).
- **Documentação de entrega (versionada):** `README.md` (instalação/execução, < 5 min) e `DECISOES.md` (decisões técnicas/financeiras — roteiro da apresentação, cobre os itens 8 e 9 do enunciado). As specs internas de trabalho ficam em `docs/` (material de trabalho, **não versionado** por decisão do usuário).
