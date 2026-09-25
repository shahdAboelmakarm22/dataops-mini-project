# DataOps Mini Project

Automated transaction data pipeline with **pytest**, **Docker**, **GitHub Actions** and **Terraform**.

![CI](https://github.com/ShahdAboelmakaram22/dataops-mini-project/actions/workflows/ci.yml/badge.svg)

---

## Project Overview

A company receives daily transaction data (`transaction_id, user_id, country, transaction_date, transaction_type, amount`).
The raw data is messy: country names have inconsistent casing/whitespace, some required fields are missing, and some amounts have the wrong sign.

This project turns that raw CSV into clean, validated and aggregated data — and wraps the whole thing in a DataOps workflow:

- every change is **tested automatically** in CI,
- the pipeline runs inside a **reproducible Docker container**,
- the container is created and managed as **Infrastructure as Code** with Terraform.

---

## Data Pipeline Architecture

```text
CSV (data/transactions.csv)
 ↓
Python Pipeline (src/transform.py)
 ↓
Data Validation   – transaction_id / user_id / transaction_date not NULL
                  – purchase → amount > 0, refund → amount < 0
 ↓
Transformation    – country cleaning: " egypt " → "EGYPT"
 ↓
Aggregation       – per country + transaction_date
 ↓
Processed Data (output/)
```

Outputs written to `output/`:

| File | Content |
|---|---|
| `clean_transactions.csv` | valid, cleaned records |
| `rejected_records.csv` | invalid records + a `rejection_reason` column |
| `summary.csv` | `country, transaction_date, number_of_transactions, number_of_users, total_amount` |

Example run on the sample dataset (16 rows → 10 valid, 6 rejected):

```text
country       | date       | txns | users |    total
EGYPT         | 2026-09-01 |    3 |     2 |      450
EGYPT         | 2026-09-02 |    2 |     1 |      200
SAUDI ARABIA  | 2026-09-01 |    1 |     1 |      700
SAUDI ARABIA  | 2026-09-02 |    1 |     1 |      300
UAE           | 2026-09-01 |    2 |     2 |      750
UAE           | 2026-09-02 |    1 |     1 |     -100
```

---

## Container Architecture

```text
Python Project
      ↓
Dockerfile   (python:3.12-slim → copy requirements.txt → pip install → copy project → run transform.py)
      ↓
Docker Image      dataops-pipeline:latest
      ↓
Docker Container  dataops-pipeline-container
```

## Infrastructure Architecture

```text
Terraform
    ↓
Docker Provider (kreuzwerker/docker)
    ↓
docker_image.pipeline        – built from ../Dockerfile, rebuilt when src/, data/, Dockerfile or requirements.txt change
    ↓
docker_container.pipeline    – runs the pipeline once
    ├── docker_network.pipeline       (bonus)
    ├── bind mount ../output → /app/output   (bonus)
    ├── env vars INPUT_PATH / OUTPUT_DIR / PIPELINE_ENV   (bonus)
    └── memory limit (bonus)
```

## CI Architecture

```text
Git Push / Pull Request
    ↓
GitHub Actions (.github/workflows/ci.yml)
    ↓
Checkout → Setup Python → Install deps → flake8 lint → pytest
    ↓
Docker Build → Run container (smoke test)
    ↓
Setup Terraform → terraform fmt -check → terraform init → terraform validate
```

If **any** step fails, the whole pipeline fails. CI only *validates* Terraform — `terraform apply` is run locally (deployment is kept separate from CI).

---

## Repository Structure

```text
dataops-mini-project/
├── data/transactions.csv
├── src/transform.py
├── tests/test_transform.py
├── output/                    # generated, git-ignored
├── terraform/
│   ├── main.tf                # image, network, container
│   ├── variables.tf
│   ├── outputs.tf
│   ├── versions.tf            # provider + Terraform version
│   └── terraform.tfvars.example
├── .github/workflows/ci.yml
├── Dockerfile
├── .dockerignore
├── requirements.txt
├── pytest.ini
├── README.md
└── .gitignore
```

---

## How to Run the Project

### 1. Python

```bash
pip install -r requirements.txt
python src/transform.py
pytest
```

### 2. Docker (manual)

```bash
docker build -t dataops-pipeline .
docker run --name dataops-pipeline-container dataops-pipeline
docker ps -a
docker logs dataops-pipeline-container
docker rm dataops-pipeline-container      # clean up before using Terraform (same name)
```

### 3. Terraform

Make sure Docker is running: `docker version`.

> **Windows (Docker Desktop):** copy `terraform/terraform.tfvars.example` to `terraform/terraform.tfvars`
> and uncomment `docker_host = "npipe:////./pipe/docker_engine"`.

```bash
cd terraform
terraform init
terraform fmt
terraform validate
terraform plan
terraform apply          # type "yes"
docker ps -a
docker logs dataops-pipeline-container
terraform show           # inspect the state
```

After `apply`, Terraform prints:

```text
container_id   = "93e0bea676f5..."
container_name = "dataops-pipeline-container"
image_id       = "sha256:e9300e0fbbc7..."
image_name     = "dataops-pipeline:latest"
network_name   = "dataops-network"
```

and the pipeline output appears in the project's `output/` folder (bind mount).

### 4. Make an infrastructure change

Edit `container_name` default in `variables.tf` to `dataops-pipeline-v2` (or pass `-var container_name=dataops-pipeline-v2`):

```bash
terraform plan    # ~ name = "dataops-pipeline-container" -> "dataops-pipeline-v2"  # forces replacement
                  # Plan: 1 to add, 0 to change, 1 to destroy.
terraform apply
docker ps -a      # now shows dataops-pipeline-v2
```

A container name can't be changed in place, so Terraform **destroys the old container and creates a new one**. The image and network are untouched.

### 5. Destroy

```bash
terraform destroy
docker ps -a      # the Terraform-managed container is gone
```

Lifecycle demonstrated: **Write → Plan → Apply → Change → Destroy**.

---

## Terraform State

`terraform apply` writes `terraform.tfstate`, which maps each resource in the code to the real Docker object (IDs, attributes):

```text
Terraform Configuration (*.tf)
        ↓
Terraform State (terraform.tfstate)
        ↓
Actual Docker Infrastructure (image, network, container)
```

On every `plan`, Terraform compares configuration ↔ state ↔ real infrastructure and only proposes the difference. A second `plan` right after `apply` reports *No changes*. The state file is git-ignored because it is machine-specific and can contain sensitive data.

---

## Failed CI Demonstration

Commit history contains an intentional bug:

| Commit | Change | CI |
|---|---|---|
| `Refactor clean_country (introduces bug to demo failing CI)` | `return country.strip()` | ❌ red |
| `Fix failing country cleaning test` | `return country.strip().upper()` | ✅ green |

**Why the first pipeline failed:** `clean_country(" egypt ")` returned `"egypt"` instead of `"EGYPT"`. The failure was in the *Run pytest* step, so the Docker and Terraform steps never ran:

```text
FAILED tests/test_transform.py::test_clean_country[ egypt -EGYPT]
E       AssertionError: assert 'egypt' == 'EGYPT'
FAILED tests/test_transform.py::test_clean_country[Egypt-EGYPT]
FAILED tests/test_transform.py::test_clean_country[ uae -UAE]
FAILED tests/test_transform.py::test_clean_country[Saudi Arabia-SAUDI ARABIA]
FAILED tests/test_transform.py::test_aggregation_total_amount - assert -50 == 300
5 failed, 7 passed
```

**Which tests detected it:** `test_clean_country` (Test 1) directly, and `test_aggregation_total_amount` (Test 5) indirectly — `" egypt "`, `"Egypt"` and `"EGYPT"` were grouped as three different countries, so the EGYPT total was wrong. This shows how a small cleaning bug silently corrupts downstream aggregates.

**Why the second pipeline succeeded:** adding `.upper()` restored the standard format, all 12 tests passed, and every later step (Docker build, Terraform checks) ran and passed.

---

## Tests

| # | Test | Checks |
|---|---|---|
| 1 | `test_clean_country` | `" egypt "` → `EGYPT` (+ other variants) |
| 2 | `test_null_user_id_is_rejected` | null `user_id` goes to rejected records |
| 3 | `test_purchase_with_negative_amount_fails` | `purchase,-100` is invalid |
| 4 | `test_refund_with_positive_amount_fails` | `refund,100` is invalid |
| 5 | `test_aggregation_total_amount` | aggregated total/transactions/users are correct |
| + | `test_other_null_required_fields_are_rejected`, `test_valid_amounts_pass`, `test_run_pipeline_writes_outputs` | extra coverage |

---

## Bonus Items Implemented

- Docker network created by Terraform
- `output/` mounted into the container
- Environment variables passed to the container
- Container memory limit
- Python linting (flake8) in GitHub Actions
- Docker container smoke-test run in CI

## Screenshots

Stored in `screenshots/`:

1. `terraform-plan.png`
2. `terraform-apply.png`
3. `docker-ps.png`
4. `github-actions-failed.png`
5. `github-actions-success.png`
