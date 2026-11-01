# Diagramas DDD e arquitetura

## Bounded Contexts

```mermaid
flowchart LR
  ID[Identidade e Acesso<br/>JWT e administrador] --> OS
  CAD[Cadastro<br/>Cliente e Veículo] --> OS[Ordens de Serviço<br/>Core Domain]
  CAT[Catálogo<br/>Serviços e preços] --> OS
  INV[Estoque<br/>Peças e movimentos] <--> OS
```

- **Ordens de Serviço** é o Core Domain.
- **Cadastro**, **Catálogo** e **Estoque** são contextos de suporte.
- **Identidade e Acesso** é um subdomínio genérico.
- No MVP eles vivem no mesmo deploy e no mesmo banco, com separação lógica. Não são
  microsserviços.

## Agregados, entidades e objetos de valor

```mermaid
classDiagram
  class WorkOrderAggregate {
    +id
    +tracking_code
    +status
    +quote_status
    +quote_total
    +start_diagnosis()
    +send_quote()
    +decide_quote()
    +finish()
    +deliver()
  }
  class WorkOrderItem {
    +reference_id
    +description
    +unit_price
    +quantity
    +subtotal()
  }
  class Document { +value +kind }
  class LicensePlate { +value }
  class Money { +value +multiply() }
  WorkOrderAggregate "1" *-- "1..*" WorkOrderItem
  WorkOrderItem --> Money
  Document ..> WorkOrderAggregate : identifica cliente
  LicensePlate ..> WorkOrderAggregate : identifica veículo
```

O agregado `WorkOrderAggregate` é a fronteira de consistência das transições. A peça
é outra raiz de consistência para estoque; sua atualização é coordenada com a OS pela
transação do caso de uso de aprovação.

## Máquina de estados

```mermaid
stateDiagram-v2
  [*] --> RECEBIDA: criar OS
  RECEBIDA --> EM_DIAGNOSTICO: iniciar diagnóstico
  EM_DIAGNOSTICO --> AGUARDANDO_APROVACAO: enviar orçamento
  AGUARDANDO_APROVACAO --> EM_DIAGNOSTICO: rejeitar e revisar itens
  AGUARDANDO_APROVACAO --> EM_EXECUCAO: aprovar + baixar estoque
  EM_EXECUCAO --> FINALIZADA: finalizar serviço
  FINALIZADA --> ENTREGUE: entregar veículo
  ENTREGUE --> [*]
```

## Componentes do monólito

```mermaid
flowchart TB
  Client[Swagger / aplicativo do cliente] --> API[Presentation<br/>FastAPI]
  API --> APP[Application<br/>GarageApplication]
  APP --> DOM[Domain<br/>Aggregate e Value Objects]
  APP --> INF[Infrastructure<br/>SQLAlchemy e JWT]
  INF --> PG[(PostgreSQL)]
```

## Modelo de dados resumido

```mermaid
erDiagram
  CUSTOMER ||--o{ VEHICLE : possui
  CUSTOMER ||--o{ WORK_ORDER : solicita
  VEHICLE ||--o{ WORK_ORDER : recebe
  WORK_ORDER ||--|{ WORK_ORDER_SERVICE_ITEM : inclui
  CATALOG_SERVICE ||--o{ WORK_ORDER_SERVICE_ITEM : referencia
  WORK_ORDER ||--o{ WORK_ORDER_PART_ITEM : inclui
  PART ||--o{ WORK_ORDER_PART_ITEM : referencia
  PART ||--o{ STOCK_MOVEMENT : movimenta
  WORK_ORDER ||--o{ STOCK_MOVEMENT : origina
```

