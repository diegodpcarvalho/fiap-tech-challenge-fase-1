# Plano de estudo e execução em três dias

O código já está funcional, mas a apresentação precisa mostrar domínio do que foi
construído. Use este plano como estudo guiado, sempre executando os exemplos no
Swagger e relacionando o comportamento aos arquivos indicados.

## Dia 1 — domínio e DDD

### Fase 1: entender o problema

Leia o desafio e explique, com suas palavras:

- por que a Ordem de Serviço é o agregado principal;
- por que preço e descrição são copiados para a OS;
- por que estoque só é baixado após aprovação;
- quais transições de status seriam perigosas se fossem livres.

Arquivos para estudar:

- `src/garage/domain/entities.py`
- `src/garage/domain/value_objects.py`
- `src/garage/domain/enums.py`
- `docs/ddd/event-storming.md`

### Fase 2: executar testes unitários

```powershell
pytest tests/unit -v
```

Exercício: escolha o teste `test_complete_work_order_lifecycle`, desenhe os estados
em papel e explique por que `finish()` falha antes de `decide_quote(True)`.

### O que você deve conseguir explicar ao fim do dia

“DDD não é separar pastas. Primeiro modelamos linguagem, eventos, comandos, regras e
limites do domínio; depois o código da classe `WorkOrderAggregate` protege essas
regras sem depender do framework.”

## Dia 2 — API, banco, segurança e fluxo completo

### Fase 3: subir a aplicação

Siga o README e abra `/docs`. Gere um token e execute o fluxo:

1. criar cliente;
2. criar serviço;
3. criar peça com estoque;
4. criar OS;
5. iniciar diagnóstico;
6. enviar orçamento;
7. aprovar pela rota pública;
8. conferir estoque;
9. finalizar e entregar.

Arquivos para estudar:

- `src/garage/presentation/router.py`
- `src/garage/application/services.py`
- `src/garage/infrastructure/models.py`
- `src/garage/infrastructure/security.py`

### Fase 4: seguir uma requisição

Use `POST /work-orders/{id}/quote` e siga a chamada:

```text
router.send_quote
  → GarageApplication.send_quote
  → WorkOrderAggregate.send_quote
  → _sync_aggregate
  → commit no banco
```

Exercício: tente finalizar uma OS antes da aprovação e explique o HTTP 409. Depois
procure `InvalidTransitionError` no código.

### O que você deve conseguir explicar ao fim do dia

- JWT autentica rotas administrativas; hash de senha e JWT são coisas diferentes;
- a API usa 404 para recurso ausente, 409 para conflito de estado e 422 para dado de
  domínio inválido;
- a transação de aprovação bloqueia primeiro a OS e depois as peças, verifica saldo,
  baixa estoque e atualiza a OS de forma atômica;
- o CPF/CNPJ da consulta pública segue no corpo de um `POST`, não na URL ou query string.

## Dia 3 — qualidade, evidências e apresentação

### Fase 5: testes e segurança

```powershell
pytest
ruff check src tests scripts
bandit -q -r src
pip-audit -r requirements.txt --progress-spinner off
```

Compare testes unitários e de integração:

- unitário: testa a regra sem HTTP e sem banco;
- integração rápida: envia requisições e usa o banco SQLite em memória;
- concorrência: executa 20 decisões paralelas em PostgreSQL real, pois SQLite ignora
  `SELECT ... FOR UPDATE`;
- cobertura: mede linhas e desvios executados, mas não substitui bons cenários.

Exercício: leia `test_insufficient_stock_prevents_approval...` e explique por que ele
protege uma regra financeira real, não apenas uma linha de código.

### Fase 6: ensaio da entrega

- complete `docs/entrega/entrega-template.md`;
- publique o repositório sem `.env`;
- proteja a branch `main` e integre por Pull Request;
- crie tag de entrega e anote branch + hash;
- exporte os documentos DDD para PDF;
- ensaie `docs/entrega/roteiro-video.md` e grave em até 15 minutos;
- abra todos os links em janela anônima antes de enviar.

### Perguntas que o avaliador pode fazer

1. Por que PostgreSQL? Transações, integridade e bloqueio concorrente do estoque.
2. Onde está o DDD? Na linguagem, agregado, objetos de valor, eventos levantados e
   regras de transição — não apenas na estrutura de diretórios.
3. Por que snapshot de preço? Para preservar o orçamento aceito.
4. O que impede estoque negativo? Validação sob bloqueio e constraint no banco.
5. O que falta para produção? Migrações, provedor real de identidade, rate limiting,
   observabilidade, mensageria de notificações e gestão externa de segredos.

