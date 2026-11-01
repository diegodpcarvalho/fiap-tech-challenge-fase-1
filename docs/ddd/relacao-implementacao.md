# Relação entre modelagem DDD e implementação

| Elemento DDD | Decisão | Implementação |
|---|---|---|
| Core Domain | Ciclo da Ordem de Serviço | `domain/entities.py::WorkOrderAggregate` |
| Agregado | Protege orçamento e transições | `WorkOrderAggregate` e seus métodos |
| Objeto de valor | Snapshot imutável de referência, preço, descrição e quantidade | `WorkOrderItem` |
| Objeto de valor | CPF/CNPJ válido e normalizado | `domain/value_objects.py::Document` |
| Objeto de valor | Placa antiga ou Mercosul normalizada | `LicensePlate` |
| Objeto de valor | Dinheiro decimal, não negativo e com centavos | `Money` |
| Política | Rejeição permite revisar e recalcular | `replace_items` |
| Política | Aprovação exige estoque e faz baixa atômica | `application/services.py::decide_quote` |
| Evento levantado | Diagnóstico iniciado | `start_diagnosis` altera estado e instante |
| Evento levantado | Orçamento aprovado/rejeitado | `decide_quote` altera decisão e status |
| Repositório/adaptador | Persistência relacional | `infrastructure/models.py` |
| Serviço de aplicação | Coordena domínio, banco e transação | `GarageApplication` |
| Interface | REST e OpenAPI | `presentation/router.py` e `schemas.py` |

## DDD pragmático nos subdomínios de suporte

O modelo rico fica no Core Domain da Ordem de Serviço, onde existem transições e
invariantes relevantes. `Customer`, `Vehicle`, `CatalogService` e `Part` não possuem
classes de domínio paralelas: cadastro, catálogo e estoque usam diretamente os modelos
do ORM como CRUDs de suporte. Essa é uma decisão explícita para evitar abstrações sem
comportamento.

O estoque também não é apresentado como um agregado rico em código. Suas regras de
saldo, bloqueio e movimento são coordenadas pelo serviço de aplicação e protegidas por
constraints e bloqueios do PostgreSQL.

## Nota sobre eventos

O Event Storming identifica eventos no passado, mas a Fase 1 pede um monólito em
camadas, não uma arquitetura dirigida a eventos. O MVP registra seus efeitos no mesmo
banco e transação. Eventuais integrações futuras podem usar Outbox Pattern para
publicar os eventos sem perda de consistência.

## Consistência e transações

- criação da OS grava veículo novo, OS e itens na mesma transação;
- aprovação bloqueia primeiro a OS e depois as peças em ordem determinística, valida
  todos os saldos, registra movimentos, baixa estoque e muda o status antes do commit;
- a serialização é coberta por teste com 20 aprovações paralelas em PostgreSQL real;
- qualquer exceção impede o commit da requisição;
- constraints do banco oferecem uma segunda barreira contra valores inválidos.

