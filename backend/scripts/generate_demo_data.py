"""Generate a deterministic synthetic FraudNet AI demo dataset.

The output is a 5,000-row transaction CSV with a ground-truth ``label`` column,
plus matching customer and account master files. Fraud patterns are injected
explicitly rather than sampled randomly:

* circular transfers (money returns to its origin)
* fan-in (many sources consolidate into one mule)
* fan-out (one source disperses funds to many accounts)
* rapid-fire small transfers (velocity/succession abuse)
* large transfers (value threshold)
* shared devices/IPs across related accounts

All names, accounts, and identifiers are synthetic. IP addresses come from the
RFC 5737 documentation ranges.

Usage:
    python -m scripts.generate_demo_data
    python -m scripts.generate_demo_data --seed 7 --output-dir data
"""

from __future__ import annotations

import argparse
import csv
import math
import random
import uuid
from collections import Counter
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_DIR = REPO_ROOT / "data"
ID_NAMESPACE = uuid.UUID("b8f9f2b1-6f1f-4a2e-9f6b-0f4f2f7d8c11")

CUSTOMER_COUNT = 220
ACCOUNT_COUNT = 320
FRAUD_TRANSACTION_COUNT = 500
TEST_NET_PREFIXES = ("192.0.2", "198.51.100", "203.0.113")
FIRST_NAMES = (
    "Aarav", "Amelia", "Arjun", "Ava", "Benjamin", "Camila", "Chen", "Chloe",
    "Daniel", "Diya", "Elena", "Ethan", "Fatima", "Gabriel", "Grace", "Hana",
    "Harper", "Ibrahim", "Isabella", "James", "Jia", "Jonah", "Kavya", "Layla",
    "Leo", "Liam", "Lucas", "Maya", "Mia", "Noah", "Olivia", "Omar", "Priya",
    "Ravi", "Riya", "Santiago", "Sara", "Sofia", "Tariq", "Theo", "Uma", "Vera",
    "William", "Yara", "Zara", "Zoe",
)
LAST_NAMES = (
    "Ahmed", "Andersen", "Bennett", "Chen", "Costa", "Davis", "Fernandez",
    "Garcia", "Gupta", "Hughes", "Iyer", "Johnson", "Khan", "Kim", "Kumar",
    "Lee", "Martin", "Mehta", "Miller", "Nair", "Nguyen", "Patel", "Rao",
    "Reed", "Rossi", "Shah", "Singh", "Smith", "Suzuki", "Taylor", "Thomas",
    "Walker", "Wang", "Williams", "Wilson", "Young",
)
CHANNELS_NORMAL = ("mobile", "web", "api", "atm", "branch", "wire", "upi")
CHANNEL_WEIGHTS_NORMAL = (34, 30, 18, 6, 3, 2, 7)
MINUTE_WEIGHTS = tuple(
    1.0 if 6 <= minute // 60 <= 22 else 0.35 for minute in range(24 * 60)
)


@dataclass(slots=True)
class DemoCustomer:
    id: str
    external_id: str
    full_name: str
    email: str
    phone: str
    country: str
    risk_level: str


@dataclass(slots=True)
class DemoAccount:
    id: str
    customer_id: str
    account_number: str
    account_type: str
    currency: str
    status: str
    balance: float
    opened_at: date
    primary_device: str
    primary_ip: str


@dataclass(slots=True)
class DemoTransaction:
    from_account: str
    to_account: str
    amount: float
    timestamp: datetime
    device_id: str
    ip_address: str
    channel: str
    label: int
    pattern: str


def _new_id(kind: str, index: int) -> str:
    return str(uuid.uuid5(ID_NAMESPACE, f"fraudnet/{kind}/{index}"))


def _device_id(rng: random.Random) -> str:
    return f"dev_{rng.getrandbits(48):012x}"


def _ip(rng: random.Random) -> str:
    return f"{rng.choice(TEST_NET_PREFIXES)}.{rng.randint(1, 254)}"


def _round_amount(value: float) -> float:
    return round(max(0.01, value), 2)


def _random_recent_timestamp(
    rng: random.Random,
    end: datetime,
    *,
    days: int,
) -> datetime:
    # Slight daytime bias keeps normal traffic looking realistic without
    # eliminating overnight activity.
    offset_days = rng.uniform(0, days)
    offset_minutes = rng.choices(
        population=range(24 * 60),
        weights=MINUTE_WEIGHTS,
        k=1,
    )[0]
    candidate = (end - timedelta(days=offset_days)).replace(
        hour=offset_minutes // 60,
        minute=offset_minutes % 60,
        second=rng.randint(0, 59),
        microsecond=0,
    )
    return min(candidate, end - timedelta(minutes=1))


def _build_customers_and_accounts(
    rng: random.Random,
) -> tuple[list[DemoCustomer], list[DemoAccount]]:
    customers: list[DemoCustomer] = []
    for index in range(CUSTOMER_COUNT):
        first = rng.choice(FIRST_NAMES)
        last = rng.choice(LAST_NAMES)
        sequence = index + 1
        customers.append(
            DemoCustomer(
                id=_new_id("customer", index),
                external_id=f"CUST-{sequence:04d}",
                full_name=f"{first} {last}",
                email=f"customer{sequence:04d}@example.com",
                phone=f"+1-202-555-{rng.randint(0, 9999):04d}",
                country="US",
                risk_level=rng.choices(
                    ("low", "medium", "high"), weights=(88, 10, 2), k=1
                )[0],
            )
        )

    accounts: list[DemoAccount] = []
    account_types = ("checking", "savings", "credit", "business", "wallet")
    account_type_weights = (48, 24, 12, 10, 6)
    for index in range(ACCOUNT_COUNT):
        customer = customers[index % CUSTOMER_COUNT]
        sequence = index + 1
        accounts.append(
            DemoAccount(
                id=_new_id("account", index),
                customer_id=customer.id,
                account_number=f"9000{sequence:08d}",
                account_type=rng.choices(
                    account_types, weights=account_type_weights, k=1
                )[0],
                currency="USD",
                status="active",
                balance=_round_amount(rng.lognormvariate(8.0, 1.1)),
                opened_at=date.today() - timedelta(days=rng.randint(180, 2200)),
                primary_device=_device_id(rng),
                primary_ip=_ip(rng),
            )
        )
    return customers, accounts


def _transaction(
    *,
    source: DemoAccount,
    destination: DemoAccount,
    amount: float,
    timestamp: datetime,
    channel: str,
    label: int,
    pattern: str,
    device_id: str | None = None,
    ip_address: str | None = None,
) -> DemoTransaction:
    return DemoTransaction(
        from_account=source.id,
        to_account=destination.id,
        amount=_round_amount(amount),
        timestamp=timestamp,
        device_id=device_id or source.primary_device,
        ip_address=ip_address or source.primary_ip,
        channel=channel,
        label=label,
        pattern=pattern,
    )


def _normal_transactions(
    rng: random.Random,
    accounts: list[DemoAccount],
    count: int,
    end: datetime,
) -> list[DemoTransaction]:
    transactions: list[DemoTransaction] = []
    for _ in range(count):
        source, destination = rng.sample(accounts, 2)
        amount = math.exp(rng.normalvariate(4.0, 0.9))
        if rng.random() < 0.025:
            amount *= rng.uniform(4.0, 12.0)
        amount = min(amount, 24_000)
        if rng.random() < 0.33:
            amount = round(amount)

        device = source.primary_device
        ip = source.primary_ip
        if rng.random() < 0.08:
            device = _device_id(rng)
        if rng.random() < 0.06:
            ip = _ip(rng)

        transactions.append(
            _transaction(
                source=source,
                destination=destination,
                amount=amount,
                timestamp=_random_recent_timestamp(rng, end, days=90),
                channel=rng.choices(
                    CHANNELS_NORMAL, weights=CHANNEL_WEIGHTS_NORMAL, k=1
                )[0],
                label=0,
                pattern="normal",
                device_id=device,
                ip_address=ip,
            )
        )
    return transactions


def _circular_transactions(
    rng: random.Random,
    accounts: list[DemoAccount],
    end: datetime,
) -> list[DemoTransaction]:
    transactions: list[DemoTransaction] = []
    ring_sizes = (3, 3, 3, 3, 4, 4, 4, 4, 5, 5, 5, 5)
    for ring_index, ring_size in enumerate(ring_sizes):
        ring = rng.sample(accounts, ring_size)
        start = _random_recent_timestamp(rng, end, days=45)
        base_amount = rng.uniform(2_500, 9_500)
        ring_device = (
            _device_id(rng) if ring_index % 3 == 0 else ring[0].primary_device
        )
        ring_ip = _ip(rng) if ring_index % 2 == 0 else ring[0].primary_ip

        for position in range(ring_size):
            source = ring[position]
            destination = ring[(position + 1) % ring_size]
            # Slight value decay mimics layering fees while preserving a cycle.
            amount = base_amount * (1 - 0.012 * position)
            timestamp = start + timedelta(
                minutes=18 * position + rng.randint(0, 7)
            )
            transactions.append(
                _transaction(
                    source=source,
                    destination=destination,
                    amount=amount,
                    timestamp=timestamp,
                    channel=rng.choice(("api", "wire", "web")),
                    label=1,
                    pattern="circular",
                    device_id=ring_device,
                    ip_address=ring_ip,
                )
            )
    return transactions


def _fan_in_transactions(
    rng: random.Random,
    accounts: list[DemoAccount],
    end: datetime,
) -> tuple[list[DemoTransaction], list[DemoAccount]]:
    transactions: list[DemoTransaction] = []
    mules: list[DemoAccount] = []
    for _ in range(10):
        mule = rng.choice(accounts)
        while mule in mules:
            mule = rng.choice(accounts)
        mules.append(mule)

        candidates = [account for account in accounts if account.id != mule.id]
        sources = rng.sample(candidates, 8)
        exits = [
            account
            for account in accounts
            if account.id != mule.id
            and account.id not in {source.id for source in sources}
        ]
        exit_account = rng.choice(exits)
        start = _random_recent_timestamp(rng, end, days=45)
        consolidation_amount = 0.0

        for position, source in enumerate(sources):
            amount = rng.uniform(650, 2_600)
            consolidation_amount += amount
            transactions.append(
                _transaction(
                    source=source,
                    destination=mule,
                    amount=amount,
                    timestamp=start
                    + timedelta(minutes=7 * position + rng.randint(0, 5)),
                    channel=rng.choice(("mobile", "web", "api", "upi")),
                    label=1,
                    pattern="fan_in",
                )
            )

        transactions.append(
            _transaction(
                source=mule,
                destination=exit_account,
                amount=consolidation_amount * 0.96,
                timestamp=start + timedelta(hours=2, minutes=rng.randint(0, 20)),
                channel="wire",
                label=1,
                pattern="fan_in_consolidation",
            )
        )
    return transactions, mules


def _fan_out_transactions(
    rng: random.Random,
    accounts: list[DemoAccount],
    end: datetime,
    preferred_sources: list[DemoAccount],
) -> list[DemoTransaction]:
    transactions: list[DemoTransaction] = []
    sources = preferred_sources[:5]
    existing_ids = {source.id for source in sources}
    while len(sources) < 10:
        candidate = rng.choice(accounts)
        if candidate.id not in existing_ids:
            sources.append(candidate)
            existing_ids.add(candidate.id)

    for source in sources:
        candidates = [account for account in accounts if account.id != source.id]
        destinations = rng.sample(candidates, 8)
        start = _random_recent_timestamp(rng, end, days=45)
        source_device = _device_id(rng)
        source_ip = _ip(rng)
        for position, destination in enumerate(destinations):
            transactions.append(
                _transaction(
                    source=source,
                    destination=destination,
                    amount=rng.uniform(550, 2_200),
                    timestamp=start
                    + timedelta(minutes=11 * position + rng.randint(0, 8)),
                    channel=rng.choice(("web", "api", "mobile", "wire")),
                    label=1,
                    pattern="fan_out",
                    device_id=source_device,
                    ip_address=source_ip,
                )
            )
    return transactions


def _rapid_fire_transactions(
    rng: random.Random,
    accounts: list[DemoAccount],
    end: datetime,
) -> list[DemoTransaction]:
    transactions: list[DemoTransaction] = []
    for _ in range(10):
        source = rng.choice(accounts)
        candidates = [account for account in accounts if account.id != source.id]
        destinations = rng.sample(candidates, 8)
        start = _random_recent_timestamp(rng, end, days=45)
        compromised_device = _device_id(rng)
        compromised_ip = _ip(rng)
        for position, destination in enumerate(destinations):
            transactions.append(
                _transaction(
                    source=source,
                    destination=destination,
                    amount=rng.uniform(25, 400),
                    timestamp=start
                    + timedelta(
                        seconds=17 * position + rng.randint(0, 12)
                    ),
                    channel=rng.choice(("mobile", "web", "upi")),
                    label=1,
                    pattern="rapid_fire",
                    device_id=compromised_device,
                    ip_address=compromised_ip,
                )
            )
    return transactions


def _large_transactions(
    rng: random.Random,
    accounts: list[DemoAccount],
    end: datetime,
) -> list[DemoTransaction]:
    transactions: list[DemoTransaction] = []
    for _ in range(52):
        source, destination = rng.sample(accounts, 2)
        transactions.append(
            _transaction(
                source=source,
                destination=destination,
                amount=rng.uniform(15_000, 95_000),
                timestamp=_random_recent_timestamp(rng, end, days=45),
                channel=rng.choice(("wire", "api")),
                label=1,
                pattern="large",
                device_id=_device_id(rng),
                ip_address=_ip(rng),
            )
        )
    return transactions


def _shared_identity_transactions(
    rng: random.Random,
    accounts: list[DemoAccount],
    end: datetime,
) -> list[DemoTransaction]:
    transactions: list[DemoTransaction] = []
    for _ in range(25):
        cluster = rng.sample(accounts, 3)
        shared_device = _device_id(rng)
        shared_ip = _ip(rng)
        start = _random_recent_timestamp(rng, end, days=45)

        for account_index, source in enumerate(cluster):
            candidates = [
                account
                for account in accounts
                if account.id not in {member.id for member in cluster}
            ]
            destinations = rng.sample(candidates, 2)
            for transfer_index, destination in enumerate(destinations):
                transactions.append(
                    _transaction(
                        source=source,
                        destination=destination,
                        amount=rng.uniform(400, 4_200),
                        timestamp=start
                        + timedelta(
                            hours=2 * account_index + transfer_index,
                            minutes=rng.randint(0, 50),
                        ),
                        channel=rng.choice(("mobile", "web", "api")),
                        label=1,
                        pattern="shared_identity",
                        device_id=shared_device,
                        ip_address=shared_ip,
                    )
                )
    return transactions


def build_transactions(
    rng: random.Random,
    accounts: list[DemoAccount],
    total: int,
    end: datetime,
) -> list[DemoTransaction]:
    fraud: list[DemoTransaction] = []
    fraud.extend(_circular_transactions(rng, accounts, end))

    fan_in, mules = _fan_in_transactions(rng, accounts, end)
    fraud.extend(fan_in)

    fraud.extend(_fan_out_transactions(rng, accounts, end, mules))
    fraud.extend(_rapid_fire_transactions(rng, accounts, end))
    fraud.extend(_large_transactions(rng, accounts, end))
    fraud.extend(_shared_identity_transactions(rng, accounts, end))

    if len(fraud) != FRAUD_TRANSACTION_COUNT:
        raise RuntimeError(
            f"Expected {FRAUD_TRANSACTION_COUNT} fraud rows, generated {len(fraud)}"
        )
    if total < len(fraud):
        raise ValueError(
            f"--transactions must be at least {len(fraud)}, got {total}"
        )

    normal = _normal_transactions(rng, accounts, total - len(fraud), end)
    transactions = normal + fraud
    transactions.sort(key=lambda transaction: transaction.timestamp)
    return transactions


def _write_customers(path: Path, customers: list[DemoCustomer]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "id",
                "external_id",
                "full_name",
                "email",
                "phone",
                "country",
                "risk_level",
            ]
        )
        for customer in customers:
            writer.writerow(
                [
                    customer.id,
                    customer.external_id,
                    customer.full_name,
                    customer.email,
                    customer.phone,
                    customer.country,
                    customer.risk_level,
                ]
            )


def _write_accounts(path: Path, accounts: list[DemoAccount]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "id",
                "customer_id",
                "account_number",
                "account_type",
                "currency",
                "status",
                "balance",
                "opened_at",
            ]
        )
        for account in accounts:
            writer.writerow(
                [
                    account.id,
                    account.customer_id,
                    account.account_number,
                    account.account_type,
                    account.currency,
                    account.status,
                    f"{account.balance:.2f}",
                    account.opened_at.isoformat(),
                ]
            )


def _write_transactions(path: Path, transactions: list[DemoTransaction]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "id",
                "from_account",
                "to_account",
                "amount",
                "currency",
                "timestamp",
                "device_id",
                "ip_address",
                "channel",
                "label",
            ]
        )
        for index, transaction in enumerate(transactions):
            writer.writerow(
                [
                    _new_id("transaction", index),
                    transaction.from_account,
                    transaction.to_account,
                    f"{transaction.amount:.2f}",
                    "USD",
                    transaction.timestamp.astimezone(UTC)
                    .isoformat()
                    .replace("+00:00", "Z"),
                    transaction.device_id,
                    transaction.ip_address,
                    transaction.channel,
                    transaction.label,
                ]
            )


def _validate(
    customers: list[DemoCustomer],
    accounts: list[DemoAccount],
    transactions: list[DemoTransaction],
) -> None:
    account_ids = {account.id for account in accounts}
    customer_ids = {customer.id for customer in customers}
    if len(account_ids) != len(accounts):
        raise RuntimeError("Duplicate account IDs generated")
    if any(account.customer_id not in customer_ids for account in accounts):
        raise RuntimeError("Account references an unknown customer")
    if any(
        transaction.from_account not in account_ids
        or transaction.to_account not in account_ids
        for transaction in transactions
    ):
        raise RuntimeError("Transaction references an unknown account")
    if any(
        transaction.from_account == transaction.to_account
        for transaction in transactions
    ):
        raise RuntimeError("Self-transfer generated")
    if any(transaction.amount <= 0 for transaction in transactions):
        raise RuntimeError("Non-positive amount generated")
    if any(transaction.timestamp.tzinfo is None for transaction in transactions):
        raise RuntimeError("Naive transaction timestamp generated")

    fraud_count = sum(transaction.label for transaction in transactions)
    if fraud_count != FRAUD_TRANSACTION_COUNT:
        raise RuntimeError("Unexpected ground-truth fraud count")


def generate_dataset(
    *,
    seed: int = 42,
    total_transactions: int = 5_000,
    end: datetime | None = None,
) -> tuple[list[DemoCustomer], list[DemoAccount], list[DemoTransaction]]:
    """Build a validated demo dataset without touching the filesystem."""

    reference_end = end or datetime.now(UTC).replace(microsecond=0)
    rng = random.Random(seed)
    customers, accounts = _build_customers_and_accounts(rng)
    transactions = build_transactions(
        rng, accounts, total_transactions, reference_end
    )
    _validate(customers, accounts, transactions)
    return customers, accounts, transactions


def parse_end_date(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory for generated CSV files (default: repository /data)",
    )
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--transactions",
        type=int,
        default=5_000,
        help="Total transaction count; 500 injected fraud rows are included",
    )
    parser.add_argument(
        "--end-date",
        type=parse_end_date,
        default=datetime.now(UTC).replace(microsecond=0),
        help="Latest timestamp, ISO-8601 (default: now)",
    )
    args = parser.parse_args()

    if args.transactions < FRAUD_TRANSACTION_COUNT:
        parser.error(
            f"--transactions must be at least {FRAUD_TRANSACTION_COUNT}"
        )

    customers, accounts, transactions = generate_dataset(
        seed=args.seed,
        total_transactions=args.transactions,
        end=args.end_date,
    )

    output_dir: Path = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_customers(output_dir / "customers.csv", customers)
    _write_accounts(output_dir / "accounts.csv", accounts)
    _write_transactions(output_dir / "sample_transactions.csv", transactions)

    pattern_counts = Counter(transaction.pattern for transaction in transactions)
    fraud_count = sum(transaction.label for transaction in transactions)
    print(f"Generated {len(transactions):,} transactions")
    print(
        f"Fraud ground truth: {fraud_count:,} / {len(transactions):,} "
        f"({fraud_count / len(transactions):.1%})"
    )
    print(f"Customers: {len(customers):,} | Accounts: {len(accounts):,}")
    print("Patterns:")
    for pattern, count in sorted(pattern_counts.items()):
        print(f"  {pattern:<24} {count:>5,}")
    print(f"Files written to {output_dir}")


if __name__ == "__main__":
    main()
