"""Shared pytest fixtures: put src on the path and give each test a clean store."""

import os
import sys
import pytest

SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from fastapi.testclient import TestClient  # noqa: E402
import storage  # noqa: E402
from app import app  # noqa: E402

FIXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")


@pytest.fixture(autouse=True)
def clean_store():
    storage.reset()
    yield
    storage.reset()


@pytest.fixture
def client():
    return TestClient(app)


def valid_ticket(**overrides):
    base = {
        "customer_id": "CUST-1",
        "customer_email": "jane@example.com",
        "customer_name": "Jane Doe",
        "subject": "Cannot log in to account",
        "description": "I cannot log in after resetting my password, this is blocking my work.",
        "category": "account_access",
        "priority": "high",
    }
    base.update(overrides)
    return base
