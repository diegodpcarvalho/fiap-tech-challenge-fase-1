from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

from garage.domain.exceptions import ValidationError

_NON_DIGITS = re.compile(r"\D")
_OLD_PLATE = re.compile(r"^[A-Z]{3}\d{4}$")
_MERCOSUL_PLATE = re.compile(r"^[A-Z]{3}\d[A-Z]\d{2}$")


def _has_repeated_digits(value: str) -> bool:
    return len(set(value)) == 1


def _is_valid_cpf(value: str) -> bool:
    if len(value) != 11 or _has_repeated_digits(value):
        return False
    for size in (9, 10):
        total = sum(int(value[index]) * (size + 1 - index) for index in range(size))
        digit = (total * 10 % 11) % 10
        if digit != int(value[size]):
            return False
    return True


def _is_valid_cnpj(value: str) -> bool:
    if len(value) != 14 or _has_repeated_digits(value):
        return False
    for size, weights in (
        (12, (5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2)),
        (13, (6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2)),
    ):
        remainder = sum(int(value[index]) * weights[index] for index in range(size)) % 11
        digit = 0 if remainder < 2 else 11 - remainder
        if digit != int(value[size]):
            return False
    return True


@dataclass(frozen=True, slots=True)
class Document:
    value: str

    def __post_init__(self) -> None:
        normalized = _NON_DIGITS.sub("", self.value)
        if not (_is_valid_cpf(normalized) or _is_valid_cnpj(normalized)):
            raise ValidationError("CPF ou CNPJ invalido.")
        object.__setattr__(self, "value", normalized)

    @property
    def kind(self) -> str:
        return "CPF" if len(self.value) == 11 else "CNPJ"


@dataclass(frozen=True, slots=True)
class LicensePlate:
    value: str

    def __post_init__(self) -> None:
        normalized = re.sub(r"[^A-Za-z0-9]", "", self.value).upper()
        if not (_OLD_PLATE.fullmatch(normalized) or _MERCOSUL_PLATE.fullmatch(normalized)):
            raise ValidationError("Placa invalida. Use o formato ABC1234 ou ABC1D23.")
        object.__setattr__(self, "value", normalized)


@dataclass(frozen=True, slots=True)
class Money:
    value: Decimal

    def __init__(self, value: Decimal | str | int | float) -> None:
        try:
            decimal_value = Decimal(str(value)).quantize(Decimal("0.01"), ROUND_HALF_UP)
        except (InvalidOperation, ValueError) as exc:
            raise ValidationError("Valor monetario invalido.") from exc
        if decimal_value < 0:
            raise ValidationError("Valor monetario nao pode ser negativo.")
        object.__setattr__(self, "value", decimal_value)

    def __add__(self, other: Money) -> Money:
        return Money(self.value + other.value)

    def multiply(self, quantity: int) -> Money:
        if quantity <= 0:
            raise ValidationError("A quantidade deve ser maior que zero.")
        return Money(self.value * quantity)
