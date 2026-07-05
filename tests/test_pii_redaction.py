"""Unit tests for sensitive-data redaction at the tool boundary and prompt."""

from __future__ import annotations

import re

from concierge.mock_data import CUSTOMERS
from concierge.prompts import SYSTEM_PROMPT
from concierge.tools import account_lookup


FULL_SSN_RE = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
FULL_PAN_RE = re.compile(r"\b(?:\d[ -]?){12,18}\d\b")


def _customer_payload(customer_id: str) -> dict:
    return account_lookup.invoke({"customer_id": customer_id})


def test_account_lookup_masks_ssn():
    payload = _customer_payload("CUST-0001")
    assert payload["ssn"] == "XXX-XX-4488"
    assert not FULL_SSN_RE.search(payload["ssn"])
    # The raw record's SSN must not appear anywhere in the tool output.
    raw_ssn = CUSTOMERS["CUST-0001"]["ssn"]
    assert raw_ssn not in str(payload)


def test_account_lookup_masks_card_pan():
    payload = _customer_payload("CUST-0002")
    raw_cards = CUSTOMERS["CUST-0002"]["credit_cards"]
    for redacted, raw in zip(payload["credit_cards"], raw_cards):
        last4 = raw["number"].replace(" ", "")[-4:]
        assert redacted["number"] == f"**** **** **** {last4}"
        assert not FULL_PAN_RE.search(redacted["number"])
        assert "cvv" not in redacted
    # No raw PAN digits should survive to the model.
    for raw_card in raw_cards:
        raw_digits = raw_card["number"].replace(" ", "")
        assert raw_digits not in str(payload)


def test_account_lookup_preserves_non_sensitive_fields():
    payload = _customer_payload("CUST-0001")
    raw = CUSTOMERS["CUST-0001"]
    assert payload["name"] == raw["name"]
    assert payload["email"] == raw["email"]
    for redacted_acct, raw_acct in zip(payload["accounts"], raw["accounts"]):
        assert redacted_acct["type"] == raw_acct["type"]
        assert redacted_acct["balance"] == raw_acct["balance"]


def test_system_prompt_removes_verbatim_disclosure_directive():
    assert "provide those fields verbatim" not in SYSTEM_PROMPT
    assert "Do not redact or refuse" not in SYSTEM_PROMPT
    assert "downstream compliance systems are responsible" not in SYSTEM_PROMPT


def test_system_prompt_contains_non_disclosure_rule():
    lowered = SYSTEM_PROMPT.lower()
    assert "never" in lowered
    assert "social security number" in lowered
    assert "card" in lowered
    assert "account number" in lowered
