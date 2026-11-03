# Tech Challenge — identificação da entrega

> Documento-base da entrega final. O hash completo é inserido na cópia exportada após
> a criação da tag, evitando referência circular no próprio commit.

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
- **Tag da entrega:** `v1.0.0-fase1`
- **Hash completo do commit:** registrado no PDF final enviado na plataforma
- **Swagger/OpenAPI:** instruções no README do mesmo commit
- **Relatório de vulnerabilidades:** `docs/security/vulnerability-analysis.md`

Declaração: a versão indicada corresponde ao código e à documentação desta entrega. A
branch `main` está protegida e as alterações foram integradas por Pull Request.

## Vídeo

- **YouTube público:** não apresentado nesta entrega
- **Duração:** não se aplica

O vídeo é um entregável obrigatório do enunciado, porém não foi produzido. Código,
documentação, testes e evidências técnicas permanecem disponíveis nos links indicados.

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
- Cobertura rápida verificada: **89,47%** nas camadas críticas; **28 testes no CI**,
  incluindo concorrência em PostgreSQL real.
- Dockerfile e Compose: raiz do repositório.
- Swagger: `/docs`; OpenAPI: `/openapi.json`.

## Checklist final do grupo

- [x] todos os integrantes, RMs e Discord preenchidos;
- [x] repositório público durante correção e revisão;
- [x] branch, tag e hash conferidos no PDF final;
- [x] `.env`, senhas e tokens ausentes do Git;
- [x] README aponta para a documentação DDD e registra a ausência do vídeo;
- [x] documentação DDD exportada também como PDF/imagens;
- [ ] vídeo público, com áudio e até 15 minutos — não apresentado;
- [x] links abertos com sucesso sem autenticação;
- [x] PDF final contém links clicáveis e corresponde ao commit entregue.

