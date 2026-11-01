# Roteiro do vídeo — máximo 15 minutos

Meta sugerida: 12 a 14 minutos, deixando margem para pausas.

## 00:00–00:45 — identificação e proposta

- apresentar integrantes, curso SOAT e Fase 1;
- resumir o problema da oficina e o objetivo do MVP;
- mostrar o commit/tag da versão demonstrada.

## 00:45–02:30 — arquitetura e banco

- abrir o README e o diagrama de componentes;
- explicar o monólito em camadas e a independência do domínio;
- justificar PostgreSQL por ACID, integridade e bloqueio do estoque.

## 02:30–04:30 — DDD e Event Storming

- mostrar os três fluxos do Event Storming;
- citar ator, comando, evento, política e agregado;
- mostrar bounded contexts, linguagem ubíqua, objetos de valor e máquina de estados;
- relacionar `WorkOrderAggregate` ao diagrama.

## 04:30–05:20 — execução e Swagger

- mostrar `docker compose up --build` já concluído;
- abrir `/docs` e o health check;
- autenticar em `/auth/token` e usar **Authorize**.

## 05:20–10:30 — fluxo funcional completo

1. criar cliente por CPF/CNPJ;
2. criar serviço e peça com estoque;
3. criar OS com veículo, serviço e peça;
4. destacar cálculo automático e código de acompanhamento;
5. iniciar diagnóstico e enviar orçamento;
6. consultar pela API pública via `POST`, com CPF/CNPJ no corpo;
7. aprovar orçamento;
8. mostrar mudança automática para `EM_EXECUCAO` e baixa do estoque;
9. finalizar e entregar;
10. consultar o tempo médio de execução.

Se houver tempo, mostre rapidamente uma transição inválida retornando 409.

## 10:30–12:30 — testes e qualidade

- executar `pytest` e mostrar 28 testes, incluindo a corrida em PostgreSQL;
- explicar um teste unitário da máquina de estados;
- explicar os testes de estoque insuficiente e aprovação concorrente;
- mostrar Ruff, Bandit e pip-audit sem achados.

## 12:30–13:30 — segurança e encerramento

- citar JWT, scrypt, segredo fora do Git, usuário não-root e transação de estoque;
- mostrar a documentação da API e estrutura do repositório;
- encerrar reforçando que documentação, código e vídeo usam o mesmo commit.

## Checklist antes de gravar

- limpar ou preparar o banco com poucos dados;
- fechar notificações e ocultar `.env`;
- aumentar fonte do terminal e navegador;
- deixar abas abertas na ordem do roteiro;
- ensaiar os JSONs no Swagger;
- conferir áudio e cronômetro;
- não mostrar senha, token completo ou segredo;
- publicar como **público**, não “não listado”, conforme o enunciado.

