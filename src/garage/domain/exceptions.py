class DomainError(Exception):
    """Erro conhecido e seguro para apresentar ao consumidor da API."""


class ValidationError(DomainError):
    pass


class NotFoundError(DomainError):
    pass


class ConflictError(DomainError):
    pass


class InvalidTransitionError(ConflictError):
    pass


class InsufficientStockError(ConflictError):
    pass
