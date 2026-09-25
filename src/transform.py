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


def check_required_fields(record):
    """Return a list of error messages for NULL/empty required fields."""
    errors = []
    for field in REQUIRED_FIELDS:
        value = record.get(field)
        if value is None or str(value).strip() == "":
            errors.append(f"{field} is NULL")
    return errors


def validate_amount(transaction_type, amount):
    """Validate the sign of the amount for the given transaction type.

    purchase -> amount > 0
    refund   -> amount < 0

    Returns (is_valid, error_message).
    """
    try:
        value = float(amount)
    except (TypeError, ValueError):
        return False, f"amount '{amount}' is not a number"

    transaction_type = (transaction_type or "").strip().lower()
    if transaction_type == "purchase":
        if value > 0:
            return True, ""
        return False, "purchase amount must be > 0"
    if transaction_type == "refund":
        if value < 0:
            return True, ""
        return False, "refund amount must be < 0"
    return False, f"unknown transaction_type '{transaction_type}'"


def validate_record(record):
    """Return a list of all validation errors for a (cleaned) record."""
    errors = check_required_fields(record)
    ok, message = validate_amount(record.get("transaction_type"), record.get("amount"))
    if not ok:
        errors.append(message)
    return errors


def split_valid_rejected(records):
    """Clean every record and split into (valid, rejected) lists.

    Rejected records get an extra 'rejection_reason' column.
    """
    valid, rejected = [], []
    for raw in records:
        record = clean_record(raw)
        errors = validate_record(record)
        if errors:
            rejected.append({**record, "rejection_reason": "; ".join(errors)})
        else:
            record["amount"] = float(record["amount"])
            valid.append(record)
    return valid, rejected
