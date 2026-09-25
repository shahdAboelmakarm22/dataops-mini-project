"""DataOps mini project: transaction data pipeline."""

import csv
from pathlib import Path

REQUIRED_FIELDS = ("transaction_id", "user_id", "transaction_date")


def clean_country(country):
    """Standardise a country value, e.g. ' egypt ' -> 'EGYPT'."""
    if country is None:
        return ""
    return country.strip().upper()


def read_transactions(path):
    """Read the raw CSV file into a list of dicts."""
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def clean_record(record):
    """Return a copy of the record with whitespace stripped and country cleaned."""
    cleaned = {k: (v.strip() if isinstance(v, str) else v) for k, v in record.items()}
    cleaned["country"] = clean_country(record.get("country"))
    cleaned["transaction_type"] = (cleaned.get("transaction_type") or "").lower()
    return cleaned
