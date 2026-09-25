import csv

import pytest

from transform import (
    aggregate,
    clean_country,
    run_pipeline,
    split_valid_rejected,
    validate_amount,
)


def make_record(**overrides):
    record = {
        "transaction_id": "1",
        "user_id": "U001",
        "country": "Egypt",
        "transaction_date": "2026-09-01",
        "transaction_type": "purchase",
        "amount": "100",
    }
    record.update(overrides)
    return record


# Test 1 - country cleaning
@pytest.mark.parametrize(
    "raw, expected",
    [(" egypt ", "EGYPT"), ("Egypt", "EGYPT"), (" uae ", "UAE"), ("Saudi Arabia", "SAUDI ARABIA")],
)
def test_clean_country(raw, expected):
    assert clean_country(raw) == expected


# Test 2 - null user_id is rejected
def test_null_user_id_is_rejected():
    valid, rejected = split_valid_rejected([make_record(user_id="")])
    assert valid == []
    assert len(rejected) == 1
    assert "user_id is NULL" in rejected[0]["rejection_reason"]


@pytest.mark.parametrize("field", ["transaction_id", "transaction_date"])
def test_other_null_required_fields_are_rejected(field):
    valid, rejected = split_valid_rejected([make_record(**{field: ""})])
    assert valid == []
    assert f"{field} is NULL" in rejected[0]["rejection_reason"]


# Test 3 - purchase with negative amount fails
def test_purchase_with_negative_amount_fails():
    ok, message = validate_amount("purchase", -100)
    assert ok is False
    assert "purchase" in message


# Test 4 - refund with positive amount fails
def test_refund_with_positive_amount_fails():
    ok, message = validate_amount("refund", 100)
    assert ok is False
    assert "refund" in message


def test_valid_amounts_pass():
    assert validate_amount("purchase", 200) == (True, "")
    assert validate_amount("refund", -50) == (True, "")


# Test 5 - aggregation produces the correct total amount
def test_aggregation_total_amount():
    records = [
        make_record(transaction_id="1", user_id="U001", country=" egypt ", amount="200"),
        make_record(transaction_id="2", user_id="U002", country="Egypt", amount="150"),
        make_record(transaction_id="3", user_id="U001", country="EGYPT",
                    transaction_type="refund", amount="-50"),
        make_record(transaction_id="4", user_id="U003", country="UAE", amount="350"),
    ]
    valid, rejected = split_valid_rejected(records)
    assert rejected == []

    summary = {(r["country"], r["transaction_date"]): r for r in aggregate(valid)}
    egypt = summary[("EGYPT", "2026-09-01")]
    assert egypt["total_amount"] == 300
    assert egypt["number_of_transactions"] == 3
    assert egypt["number_of_users"] == 2
    assert summary[("UAE", "2026-09-01")]["total_amount"] == 350


def test_run_pipeline_writes_outputs(tmp_path):
    input_file = tmp_path / "input.csv"
    rows = [
        make_record(transaction_id="1", amount="200"),
        make_record(transaction_id="2", user_id="", amount="300"),
    ]
    with open(input_file, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    result = run_pipeline(input_file, tmp_path / "out")

    assert result["valid"] == 1
    assert result["rejected"] == 1
    for name in ("clean_transactions.csv", "rejected_records.csv", "summary.csv"):
        assert (tmp_path / "out" / name).exists()
