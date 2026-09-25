"""DataOps mini project: transaction data pipeline."""

import csv
from pathlib import Path

REQUIRED_FIELDS = ("transaction_id", "user_id", "transaction_date")


def clean_country(country):
    """Standardise a country value, e.g. ' egypt ' -> 'EGYPT'."""
    if country is None:
        return ""
    return country.strip()


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


def aggregate(valid_records):
    """Aggregate valid records by (country, transaction_date).

    Returns a list of dicts sorted by country and date with:
    country, transaction_date, number_of_transactions, number_of_users, total_amount
    """
    groups = {}
    for r in valid_records:
        key = (r["country"], r["transaction_date"])
        g = groups.setdefault(key, {"transactions": 0, "users": set(), "total": 0.0})
        g["transactions"] += 1
        g["users"].add(r["user_id"])
        g["total"] += float(r["amount"])

    summary = []
    for (country, date), g in sorted(groups.items()):
        total = round(g["total"], 2)
        summary.append(
            {
                "country": country,
                "transaction_date": date,
                "number_of_transactions": g["transactions"],
                "number_of_users": len(g["users"]),
                "total_amount": int(total) if total.is_integer() else total,
            }
        )
    return summary


def write_csv(path, rows, fieldnames):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def run_pipeline(input_path, output_dir):
    """Run the full pipeline: read -> clean -> validate -> aggregate -> write."""
    output_dir = Path(output_dir)
    raw = read_transactions(input_path)
    valid, rejected = split_valid_rejected(raw)
    summary = aggregate(valid)

    base_cols = ["transaction_id", "user_id", "country", "transaction_date",
                 "transaction_type", "amount"]
    write_csv(output_dir / "clean_transactions.csv", valid, base_cols)
    write_csv(output_dir / "rejected_records.csv", rejected, base_cols + ["rejection_reason"])
    write_csv(output_dir / "summary.csv", summary,
              ["country", "transaction_date", "number_of_transactions",
               "number_of_users", "total_amount"])
    return {"read": len(raw), "valid": len(valid), "rejected": len(rejected),
            "summary": summary}


def main():
    import os

    project_root = Path(__file__).resolve().parent.parent
    input_path = os.environ.get("INPUT_PATH", project_root / "data" / "transactions.csv")
    output_dir = os.environ.get("OUTPUT_DIR", project_root / "output")

    print(f"[pipeline] Reading: {input_path}")
    result = run_pipeline(input_path, output_dir)
    print(f"[pipeline] Records read:     {result['read']}")
    print(f"[pipeline] Valid records:    {result['valid']}")
    print(f"[pipeline] Rejected records: {result['rejected']}")
    print("[pipeline] Summary:")
    print(f"{'country':<14}| {'date':<11}| {'txns':>4} | {'users':>5} | {'total':>8}")
    for row in result["summary"]:
        print(f"{row['country']:<14}| {row['transaction_date']:<11}| "
              f"{row['number_of_transactions']:>4} | {row['number_of_users']:>5} | "
              f"{row['total_amount']:>8}")
    print(f"[pipeline] Output written to: {output_dir}")


if __name__ == "__main__":
    main()
