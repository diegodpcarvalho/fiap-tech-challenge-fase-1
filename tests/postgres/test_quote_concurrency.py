from __future__ import annotations

import os

import pytest

from scripts.race_double_approval import run_concurrency_check

pytestmark = pytest.mark.postgres
DATABASE_URL = os.getenv("POSTGRES_TEST_DATABASE_URL")


@pytest.mark.skipif(not DATABASE_URL, reason="POSTGRES_TEST_DATABASE_URL nao configurada")
def test_parallel_quote_approval_debits_stock_once():
    result = run_concurrency_check(DATABASE_URL, parallel=20)
    assert result["accepted"] == 1
    assert result["conflicts"] == 19
    assert result["stock"] == 8
    assert result["movements"] == 1
