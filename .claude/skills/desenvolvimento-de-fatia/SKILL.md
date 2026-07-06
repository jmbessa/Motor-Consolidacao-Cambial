---
name: desenvolvimento-de-fatia
description: Use ao implementar qualquer funcionalidade ("fatia") do Motor de Consolidação Cambial. Codifica a metodologia spec-driven do projeto em três fases — plano, TDD e revisão adversarial — e aponta quais skills/agentes usar em cada uma.
---

# Desenvolvimento de fatia (spec-driven)

Metodologia obrigatória deste projeto (ver `CLAUDE.md`). **Nenhuma fatia é "pronta"
sem passar pelas três fases.** Toda fatia respeita a arquitetura Hexagonal: o
domínio é puro; I/O e frameworks vivem em adapters.

## Fase 1 — Elaboração do plano (spec)

Antes de qualquer código de produção:

1. Explorar intenção e requisitos com `superpowers:brainstorming`.
2. Escrever o plano com `superpowers:writing-plans` (ou o agente `Plan`). O plano
   define: comportamento esperado, contratos/interfaces, casos de borda, regras de
   negócio envolvidas e a estratégia de testes.
3. **Obter aprovação do usuário antes de prosseguir.**

## Fase 2 — Desenvolvimento com TDD

Seguir `superpowers:test-driven-development` à risca:

- Teste que falha primeiro → assistir falhar → código mínimo que passa → refatorar.
- Cobrir primeiro as partes críticas: cálculo/conversão, regras de payable/
  receivable, fallback de data, alertas, rastreabilidade.
- Dinheiro sempre em `Decimal`; nunca `float`. Rejeitar `NaN`/`Infinity`.
- Domínio testado sem rede nem arquivo.

## Fase 3 — Revisão adversarial

- Submeter a implementação ao agente **`lv10-dev`** (assume que o design está
  errado e prova; caça falhas silenciosas e piores casos).
- Incorporar o feedback com `superpowers:receiving-code-review` (verificar cada
  ponto, não concordar por reflexo).
- Confirmar conclusão com `superpowers:verification-before-completion` (evidência:
  testes rodando e verdes) antes de declarar "pronto".

## Regras invioláveis

- **Nunca commitar automaticamente.** Ao final, propor a mensagem de commit e
  aguardar a aprovação do usuário.
- Registrar as skills/agentes efetivamente usados em `.claude/skills/README.md`
  (evidência de uso de IA para a apresentação).
