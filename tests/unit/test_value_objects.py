from decimal import Decimal

import pytest

from garage.domain.exceptions import ValidationError
from garage.domain.value_objects import Document, LicensePlate, Money


@pytest.mark.parametrize(
    ("raw", "normalized", "kind"),
    [
        ("529.982.247-25", "52998224725", "CPF"),
        ("11.222.333/0001-81", "11222333000181", "CNPJ"),
    ],
)
def test_document_accepts_valid_values(raw, normalized, kind):
    document = Document(raw)
    assert document.value == normalized
    assert document.kind == kind


@pytest.mark.parametrize("raw", ["111.111.111-11", "123", "11.111.111/1111-11"])
def test_document_rejects_invalid_values(raw):
    with pytest.raises(ValidationError, match="invalido"):
        Document(raw)


@pytest.mark.parametrize("raw", ["ABC-1234", "ABC1D23"])
def test_plate_accepts_old_and_mercosul_formats(raw):
    assert LicensePlate(raw).value == raw.replace("-", "").upper()


def test_plate_rejects_invalid_value():
    with pytest.raises(ValidationError, match="Placa"):
        LicensePlate("123-ABCD")


def test_money_rounds_and_calculates():
    price = Money("10.005")
    assert price.value == Decimal("10.01")
    assert price.multiply(3).value == Decimal("30.03")
    assert (price + Money("1.99")).value == Decimal("12.00")


@pytest.mark.parametrize("value", ["invalid", -1])
def test_money_rejects_invalid_or_negative_values(value):
    with pytest.raises(ValidationError):
        Money(value)


def test_money_rejects_non_positive_quantity():
    with pytest.raises(ValidationError, match="quantidade"):
        Money(10).multiply(0)
