NexGuard test fixtures
======================

These CSV files are **synthetic test fixtures only**, not customer or production data.

- `fixtures/transactions_review_signals.csv`: includes high-value transfers and labelled examples for validating detection behavior.
- `fixtures/transactions_normal.csv`: small ordinary-activity fixture.

The ingestion API requires every `from_account` and `to_account` UUID to already exist in the configured account master data. The current in-memory app starts with no account master records, so these fixtures are for test harnesses or a database seeded with matching account IDs. Do not upload real customer data unless you are authorized and have configured secure persistence.

Required CSV columns: `from_account,to_account,amount,currency,timestamp,channel`. Optional columns include `id,device_id,ip_address,label`.
