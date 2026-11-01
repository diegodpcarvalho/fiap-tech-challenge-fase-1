# Tech Challenge — identificação da entrega

> Substitua todos os campos `PREENCHER`, exporte este documento para PDF e teste cada
> link em janela anônima. Não envie este template incompleto.

## Identificação

- **Curso:** SOAT — Software Architecture
- **Fase:** 1
- **Grupo:** 147
- **Integrantes e RMs:**
  - DIEGO DE PAULA CARVALHO — RM 377208 — Discord diego_oak
- **E-mail:** diegodpcarvalho@gmail.com
- **Linguagem:** Python
- **Tecnologias principais:** FastAPI, SQLAlchemy, PostgreSQL, Pytest, Docker e JWT

## Repositório

- **URL pública completa:** https://github.com/diegodpcarvalho/fiap-tech-challenge-fase-1
- **Branch da entrega:** main
- **Tag da entrega:** PREENCHER
- **Hash completo do commit:** PREENCHER
- **Swagger/OpenAPI:** instruções no README do mesmo commit
- **Relatório de vulnerabilidades:** `docs/security/vulnerability-analysis.md`

Declaração: a versão indicada corresponde ao código demonstrado no vídeo e à
documentação desta entrega. A branch `main` está protegida e as alterações foram
integradas por Pull Request.

## Vídeo

- **YouTube público:** PREENCHER
- **Duração:** PREENCHER (máximo de 15 minutos)

O vídeo demonstra proposta, arquitetura, banco, Event Storming, DDD, criação e
acompanhamento da OS, serviços, peças, orçamento, aprovação, status, JWT, Swagger,
testes, cobertura e análise de vulnerabilidades.

## Documentação DDD

- **Documentação equivalente, acesso público:** https://github.com/diegodpcarvalho/fiap-tech-challenge-fase-1/tree/main/docs/ddd
- **Event Storming no repositório:** `docs/ddd/event-storming.md`
- **Diagramas no repositório:** `docs/ddd/diagramas.md`
- **Event Storming exportado:** `docs/ddd/event-storming.pdf`
- **Diagramas exportados:** `docs/ddd/diagramas.pdf`
- **Linguagem ubíqua:** `docs/ddd/linguagem-ubiqua.md`
- **Relação documentação/código:** `docs/ddd/relacao-implementacao.md`

## Evidências técnicas

- Monólito em camadas e APIs RESTful: README e `src/garage/`.
- Autenticação JWT: `infrastructure/security.py` e `/api/v1/auth/token`.
- CPF/CNPJ e placa: `domain/value_objects.py`.
- Transições da OS: `domain/entities.py::WorkOrderAggregate`.
- Estoque transacional: `application/services.py::decide_quote`.
- Testes unitários e de integração: `tests/`.
- Cobertura verificada: **90,16%** nas camadas críticas, **25 testes aprovados**.
- Dockerfile e Compose: raiz do repositório.
- Swagger: `/docs`; OpenAPI: `/openapi.json`.

## Checklist final do grupo

- [ ] todos os integrantes, RMs e Discord preenchidos;
- [ ] repositório público durante correção e revisão;
- [ ] branch, tag e hash conferidos;
- [ ] `.env`, senhas e tokens ausentes do Git;
- [ ] README aponta para DDD e vídeo;
- [ ] documentação DDD exportada também como PDF/imagens;
- [ ] vídeo público, com áudio e até 15 minutos;
- [ ] links abertos com sucesso em janela anônima;
- [ ] PDF final contém links clicáveis e corresponde ao commit entregue.

