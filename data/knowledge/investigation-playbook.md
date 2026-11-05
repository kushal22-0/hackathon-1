# Fraud investigation playbook

## 1. Triage the alert

Read the alert explanation before looking at raw data. Record the triggering
rules, the model score, and the combined risk score. Distinguish high-confidence
rule evidence (for example a transfer above a configured threshold) from
model-only anomaly signals, which require more context.

## 2. Establish the account baseline

Review the account's typical amount, transaction velocity, active channels,
known devices, known IPs, and prior alerts. A transaction that is unusual for
one account may be routine for another. Compare the alert transaction with the
last 30 and 90 days of activity.

## 3. Trace the funds

Trace at least two hops forward and backward where legally permitted. Identify:

- immediate sources of funds and destinations;
- circular flows that return value to the origin;
- fan-in consolidation accounts and fan-out disbursement accounts;
- cash-out or external transfer endpoints;
- timing relationships between hops.

Document each hop with transaction IDs, timestamps, amounts, and currencies.

## 4. Test alternative explanations

Consider payroll, merchant settlement, family transfers, refunds, loan
disbursement, and treasury movements. A shared device can be a household; a
large transfer can be a property purchase. Look for corroborating context
before concluding fraud.

## 5. Preserve evidence

Attach the alert snapshot, relevant transactions, account ownership details,
device/IP links, and notes to the case. Use immutable evidence entries and
record the investigator and timestamp.

## 6. Decide and document

Choose an outcome of fraud, legitimate, or inconclusive. Write a short rationale
that a reviewer can follow without re-running the investigation. If the case is
fraudulent, record the recovery or escalation action. If legitimate, record the
specific evidence that resolved the alert.

## Escalation triggers

- confirmed mule behavior or coordinated accounts;
- onward transfer to a sanctioned or high-risk destination;
- law-enforcement or regulatory reporting thresholds;
- repeated alerts across related accounts;
- evidence of account takeover or credential compromise.
