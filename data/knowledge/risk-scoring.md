# How FraudNet AI combines rule and model risk

FraudNet AI produces a 0–100 risk score. The score is an investigation
prioritization signal, not a verdict.

## Rule layer

Configurable rules evaluate context around a transaction:

- **Large transfer** compares the amount with a configured threshold. Higher
  multiples raise severity and contribution.
- **High frequency** counts transfers from the same account within a rolling
  window.
- **Rapid succession** measures the minimum gap between transfers in a burst.

Each rule returns a structured hit with a code, severity, score contribution,
human-readable explanation, and evidence. Contributions are capped so that no
combination can push the rule layer above 100.

## Model layer

An IsolationForest is trained on engineered transaction features including
log amount, time of day, transaction velocity, distinct counterparties, amount
relative to the account baseline, device-sharing count, IP-sharing count, and
round-amount behavior. The raw anomaly score is normalized against training
quantiles into a 0–100 model score. The model is unsupervised; the demo ground
truth is never used during fitting.

## Combination

```text
risk_score = 0.60 × rule_score + 0.40 × ml_score
```

The weights are configurable. An alert is opened when the combined score meets
the configured threshold or a critical rule triggers. The explanation and
evidence snapshot are stored with the alert so later model changes do not
rewrite history.

## Limitations

- Thresholds must be tuned to the institution, product, and customer segment.
- IsolationForest reports novelty, not intent. It can flag legitimate unusual
  behavior and miss fraud that looks statistically normal.
- Shared-device evidence must be treated carefully; households and shared
  terminals create benign collisions.
- Ground-truth labels in the demo dataset are for evaluation only and are not
  used to train the model.
