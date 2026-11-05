NexGuard test fixtures
======================

These files are **synthetic test fixtures only**. They are isolated under `test/fixtures/` and must never be presented as real customer or production data.

Files:
- `customers.csv` and `accounts.csv`: matching master records required by transaction foreign-key validation.
- `transactions_review_signals.csv`: a small set of normal and high-value labelled transactions for testing ingestion and detection.
- `transactions_normal.csv`: a small ordinary-activity fixture.

To use the fixtures with PostgreSQL, configure `REPOSITORY_BACKEND=postgres` and `DATABASE_URL`, then from the `backend` directory run:

```powershell
python -m scripts.seed_demo_data --data-dir ..\test\fixtures --skip-transactions
```

Then upload `test/fixtures/transactions_review_signals.csv` in Transaction Monitoring and run detection. The in-memory backend starts empty and has no account-master import endpoint, so CSV ingestion there correctly rejects unknown account IDs. For real use, load authorized account master data into your configured database first.

Required transaction CSV columns: `from_account,to_account,amount,currency,timestamp,channel`. Optional columns: `id,device_id,ip_address,label`.
