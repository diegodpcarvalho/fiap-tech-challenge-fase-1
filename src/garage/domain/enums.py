from enum import StrEnum


class WorkOrderStatus(StrEnum):
    RECEIVED = "RECEBIDA"
    IN_DIAGNOSIS = "EM_DIAGNOSTICO"
    WAITING_APPROVAL = "AGUARDANDO_APROVACAO"
    IN_PROGRESS = "EM_EXECUCAO"
    COMPLETED = "FINALIZADA"
    DELIVERED = "ENTREGUE"


class QuoteStatus(StrEnum):
    DRAFT = "RASCUNHO"
    PENDING = "PENDENTE"
    APPROVED = "APROVADO"
    REJECTED = "REJEITADO"


class StockMovementType(StrEnum):
    ENTRY = "ENTRADA"
    EXIT = "SAIDA"
