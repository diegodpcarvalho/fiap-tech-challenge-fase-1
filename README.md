# Oficina API — FIAP Tech Challenge Fase 1

Back-end monolítico para gerenciar clientes, veículos, catálogo de serviços, peças,
estoque e o ciclo completo de uma Ordem de Serviço (OS). A solução foi construída em
Python com FastAPI, DDD pragmático e arquitetura em camadas.

**Grupo 147 — integrante:** Diego de Paula Carvalho — RM 377208 — Discord `diego_oak`  
**Contato:** diegodpcarvalho@gmail.com

> Links da entrega: substitua os campos `PREENCHER` em
> [`docs/entrega/entrega-template.md`](docs/entrega/entrega-template.md) antes de publicar.

## Objetivo e solução

O MVP substitui anotações e planilhas da oficina por uma API que:

- identifica o cliente por CPF/CNPJ e cadastra ou reutiliza seu veículo;
- adiciona serviços, peças e insumos, preservando os preços usados no orçamento;
- calcula o orçamento automaticamente;
- controla as transições `RECEBIDA → EM_DIAGNOSTICO → AGUARDANDO_APROVACAO →
  EM_EXECUCAO → FINALIZADA → ENTREGUE`;
- permite ao cliente acompanhar e aprovar/rejeitar o orçamento usando código da OS
  e CPF/CNPJ enviado no corpo da requisição, sem dado pessoal na URL;
- baixa o estoque somente quando o orçamento é aprovado;
- oferece CRUDs e métrica de tempo médio para a administração;
- protege todas as rotas administrativas com JWT.

## Arquitetura

O sistema é um monólito em camadas:

```text
HTTP / FastAPI (presentation)
        ↓
Casos de uso e transações (application)
        ↓
Regras, entidades e objetos de valor (domain)
        ↓
SQLAlchemy, PostgreSQL e JWT (infrastructure)
```

A camada de domínio não importa FastAPI nem SQLAlchemy. A aplicação coordena os
casos de uso e a transação; a infraestrutura persiste o estado; a apresentação faz
validação de formato, autenticação e conversão HTTP.

O modelo rico está concentrado no Core Domain da Ordem de Serviço. Cliente, veículo,
catálogo e peça são subdomínios de suporte implementados como CRUDs simples sobre os
modelos persistentes. `WorkOrderItem` é um objeto de valor imutável usado como snapshot
do orçamento, não uma entidade independente.

Documentação detalhada:

- [Visão DDD e diagramas](docs/ddd/diagramas.md)
- [Event Storming](docs/ddd/event-storming.md)
- [Event Storming exportado em PDF](docs/ddd/event-storming.pdf)
- [Diagramas exportados em PDF](docs/ddd/diagramas.pdf)
- [Linguagem ubíqua](docs/ddd/linguagem-ubiqua.md)
- [Relação entre DDD e código](docs/ddd/relacao-implementacao.md)
- [Plano de estudo em três dias](docs/PLANO-DE-ESTUDO-3-DIAS.md)

## Tecnologias

- Python 3.12+;
- FastAPI e OpenAPI/Swagger;
- SQLAlchemy 2;
- PostgreSQL 17 em produção local e no teste de concorrência; SQLite em memória nos
  testes rápidos;
- PyJWT, hash de senha com `scrypt` da biblioteca padrão;
- Pytest e pytest-cov;
- Docker e Docker Compose;
- Ruff, Bandit e pip-audit.

## Por que PostgreSQL

O PostgreSQL foi escolhido por oferecer transações ACID, restrições de integridade,
índices e bloqueio de linhas com `SELECT ... FOR UPDATE`. Na aprovação, a aplicação
bloqueia primeiro a OS e depois as peças em ordem determinística. Assim, duas decisões
concorrentes não podem aprovar a mesma OS nem consumir o estoque duas vezes. SQLite
permanece somente nos testes rápidos; a concorrência é verificada em PostgreSQL real.

## Pré-requisitos

- Docker Desktop com Docker Compose, para o caminho recomendado; ou
- Python 3.12+ e PostgreSQL, para execução sem Docker;
- Git para versionamento.

## Execução com Docker

1. Instale o projeto e gere automaticamente o ambiente local:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -e ".[dev]"
   python scripts/setup_local_environment.py
   ```

   O script gera os segredos sem exibi-los e salva a credencial de demonstração em
   `.demo-credentials`; ambos os arquivos ficam fora do Git.

2. Como alternativa manual, copie `.env.example` para `.env`, gere o hash da senha
   com o comando abaixo e complete todas as variáveis obrigatórias:

   ```powershell
   python scripts/generate_password_hash.py
   ```

3. Execute:

   ```powershell
   docker compose up --build
   ```

4. Acesse:

   - Swagger UI: <http://localhost:8000/docs>
   - OpenAPI JSON: <http://localhost:8000/openapi.json>
   - Health check: <http://localhost:8000/api/v1/health>

Para encerrar, use `docker compose down`. Os dados permanecem no volume
`postgres_data`. Use `docker compose down -v` apenas se quiser apagar o banco local.

## Execução somente com Python

Crie o ambiente, instale o projeto e defina as variáveis antes de iniciar:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
$env:DATABASE_URL = "sqlite:///./garage.db"
$env:JWT_SECRET = "substitua-por-um-segredo-com-32-ou-mais-caracteres"
$env:ADMIN_USERNAME = "admin"
$env:ADMIN_PASSWORD_HASH = "cole-o-hash-gerado"
uvicorn garage.main:app --reload
```

O SQLite dessa opção facilita a demonstração, mas o compose com PostgreSQL é a
configuração recomendada para a entrega.

## Autenticação e demonstração

Não há senha gravada no repositório. O avaliador deve usar o usuário configurado em
`ADMIN_USERNAME` e a senha usada para gerar `ADMIN_PASSWORD_HASH`.

No Swagger:

1. execute `POST /api/v1/auth/token` com usuário e senha;
2. copie `access_token` da resposta;
3. clique em **Authorize** e informe apenas o token;
4. use os endpoints administrativos.

A consulta `POST /api/v1/public/work-orders/{tracking_code}` simula o aplicativo do
cliente e recebe o CPF/CNPJ no corpo JSON. O documento não aparece na URL nem no access
log padrão. A decisão do orçamento também usa `POST` com corpo JSON.

## Testes e cobertura

```powershell
pytest
```

Resultado verificado em 31/10/2026:

```text
27 passed, 1 skipped sem a URL do banco de teste
28 passed no CI, incluindo concorrência em PostgreSQL
89.47% de cobertura nas camadas de domínio e aplicação nos testes rápidos
```

Para gerar evidências adicionais:

```powershell
pytest --cov-report=html --cov-report=xml
ruff check src tests scripts
ruff format --check src tests scripts
bandit -q -r src
pip-audit -r requirements.txt --progress-spinner off
```

O relatório da análise está em [docs/security/vulnerability-analysis.md](docs/security/vulnerability-analysis.md).

## Fluxo de demonstração

1. Autenticar o administrador.
2. Criar cliente, serviço e peça com estoque.
3. Criar uma OS; o veículo é criado caso a placa ainda não exista.
4. Iniciar diagnóstico e enviar orçamento.
5. Consultar a OS pela rota pública e aprovar.
6. Mostrar a baixa do estoque.
7. Finalizar e entregar a OS.
8. Consultar a métrica de tempo médio.

O roteiro completo de até 15 minutos está em [docs/entrega/roteiro-video.md](docs/entrega/roteiro-video.md).

## Estrutura principal

```text
src/garage/
├── domain/          # regras puras, estados, CPF/CNPJ, placa e dinheiro
├── application/     # casos de uso e fronteiras transacionais
├── infrastructure/  # modelos SQLAlchemy, banco, senha e JWT
├── presentation/    # schemas, dependências e rotas FastAPI
└── main.py           # composição e tratamento global de erros
tests/
├── unit/             # regras de domínio
├── integration/      # API e banco em memória
└── postgres/         # concorrência e bloqueio de linhas no banco real
docs/
├── ddd/              # Event Storming, diagramas, SVGs e PDFs exportados
├── entrega/          # template do PDF e roteiro do vídeo
└── security/         # análise de vulnerabilidades
```

## Decisões importantes

- valores monetários usam `Decimal`, nunca `float`;
- itens da OS guardam descrição e preço em snapshot, então uma alteração posterior
  no catálogo não muda um orçamento já criado;
- exclusão de serviços e peças é lógica (`active=false`) para preservar histórico;
- estoque é validado novamente no instante da aprovação e baixado na mesma transação;
- a OS é bloqueada antes das peças, impedindo aprovação concorrente em duplicidade;
- orçamento rejeitado pode ser revisado ou encerrado com devolução sem execução;
- cliente ou veículo com OS não pode ser excluído;
- segredos falham de forma explícita na inicialização e ficam fora do Git.

## Links finais

- Repositório: <https://github.com/diegodpcarvalho/fiap-tech-challenge-fase-1>
- Branch da entrega: `main`
- Tag/hash da entrega: **PREENCHER APÓS O MERGE FINAL**
- Documentação DDD pública: <https://github.com/diegodpcarvalho/fiap-tech-challenge-fase-1/tree/main/docs/ddd>
- Vídeo público no YouTube: **PREENCHER**

