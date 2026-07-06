# Skills e agentes de IA usados neste projeto

Este diretório **evidencia o uso de IA generativa** no desenvolvimento — resposta
direta à pergunta da apresentação: *"Onde e como você usou IA generativa? Seja
específico."*

Aqui registramos **quais** capacidades de IA foram adotadas, **em que fase** da
metodologia cada uma entra e **por quê**. O skill de projeto
[`desenvolvimento-de-fatia`](desenvolvimento-de-fatia/SKILL.md) codifica o nosso
fluxo spec-driven de forma reutilizável.

## Metodologia (spec-driven, 3 fases)

Cada funcionalidade ("fatia") passa por: **1) plano → 2) TDD → 3) revisão
adversarial**. Ver `CLAUDE.md` e o skill de projeto.

## Skills externas adotadas

| Skill | Fase | Para quê |
|---|---|---|
| `superpowers:brainstorming` | 1 — Plano | Explorar intenção/requisitos antes de projetar cada fatia |
| `superpowers:writing-plans` | 1 — Plano | Escrever o plano de implementação da fatia |
| `superpowers:test-driven-development` | 2 — Dev | Ciclo red-green-refactor nas partes críticas de cálculo/conversão |
| `superpowers:requesting-code-review` | 3 — Revisão | Solicitar revisão ao concluir a fatia |
| `superpowers:receiving-code-review` | 3 — Revisão | Incorporar feedback com rigor técnico (verificar, não concordar por reflexo) |
| `superpowers:verification-before-completion` | 3 — Revisão | Exigir evidência (testes rodando) antes de declarar "pronto" |
| `superpowers:systematic-debugging` | qualquer | Depurar falhas de forma sistemática |
| `frontend-design` | fatia de front | Design intencional do dashboard (evitar template genérico) |
| `dataviz` | fatia de front | Gráficos de divergência PTAX×Frankfurter, top 3, posição líquida |
| `context7` (MCP) | qualquer | Docs atualizadas de pydantic, FastAPI, SQLAlchemy, Docker, httpx |

## Agentes usados

| Agente | Papel |
|---|---|
| `lv10-dev` | **Revisão adversarial obrigatória (Fase 3)** — assume que o design está errado e caça falhas silenciosas e piores casos |
| `Plan` | Desenho de planos de implementação por fatia |
| `Explore` | Buscas amplas read-only no código |
| `architect-analyst` | Avaliação de decisões arquiteturais (limites, direção de dependência) |
| `dev-analyst` | Análise concreta de implementação e casos de borda |

## Registro por fatia

Conforme cada fatia avança, registramos aqui quais skills/agentes foram de fato
acionados (para a apresentação ser específica).

- **Fatia 1 — Modelagem do domínio:** `writing-plans` + agente `Plan` (plano);
  `test-driven-development` (implementação); agente `lv10-dev` (revisão).
