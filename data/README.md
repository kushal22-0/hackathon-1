# Demo data

This directory contains synthetic data for local demos and evaluation. It does
not contain real customers, accounts, or transactions.

## Files

| File | Contents |
| --- | --- |
| `customers.csv` | 220 synthetic customers (IDs align with `accounts.csv`) |
| `accounts.csv` | 320 synthetic accounts tied to customers |
| `sample_transactions.csv` | 5,000 transactions; 500 labeled fraud (10%) |
| `knowledge/*.md` | Source material for the later RAG/Copilot phase |

The transaction CSV matches the ingestion contract:

```text
id,from_account,to_account,amount,currency,timestamp,device_id,ip_address,channel,label
```

`label` is nullable ground truth for **demo evaluation only**. Do not expose or
use ground-truth labels in production inference paths.

## Injected fraud patterns

| Pattern | Rows | What it exercises |
| --- | ---: | --- |
| Circular transfers | 48 | NetworkX cycle detection |
| Fan-in + consolidation | 90 | Many-to-one flows, fan-in detection |
| Fan-out | 80 | One-to-many disbursement, fan-out detection |
| Rapid-fire small transfers | 80 | Frequency and succession rules |
| Large transfers | 52 | Value-threshold rule |
| Shared device/IP clusters | 150 | Identity-linked anomaly features |

Fraud rows are spread over the most recent 45 days; normal rows span 90 days.
Names, account numbers, and device IDs are synthetic. IPs come from RFC 5737
documentation ranges (`192.0.2.0/24`, `198.51.100.0/24`, `203.0.113.0/24`).

## Regenerate

From `backend/` with the virtualenv active:

```bash
python -m scripts.generate_demo_data --seed 42
```

The generator validates account references, self-transfers, positive amounts,
and the exact 500-row fraud ground truth before writing files.
