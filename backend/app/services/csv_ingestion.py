"""CSV parsing and row-level validation for transaction ingestion."""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import uuid4

from pydantic import ValidationError

from app.core.errors import AppError
from app.models.transaction import (
    IngestRowError,
    Transaction,
    TransactionCsvRow,
)

REQUIRED_COLUMNS = frozenset(
    {
        "from_account",
        "to_account",
        "amount",
        "currency",
        "timestamp",
        "channel",
    }
)
MAX_REPORTED_ERRORS = 200


@dataclass(slots=True)
class ParsedTransactionCsv:
    transactions: list[Transaction]
    row_count: int
    filename: str


def _structural_error(
    *, code: str, message: str, details: Any | None = None
) -> AppError:
    return AppError(
        code=code,
        message=message,
        status_code=422,
        details=details,
    )


def _validation_errors(exc: ValidationError, row_number: int) -> list[IngestRowError]:
    errors: list[IngestRowError] = []
    for error in exc.errors():
        location = [str(part) for part in error.get("loc", ())]
        field = ".".join(location) or None
        errors.append(
            IngestRowError(
                row=row_number,
                field=field,
                message=str(error.get("msg", "Invalid value")),
            )
        )
    return errors


def parse_transactions_csv(
    content: bytes,
    *,
    filename: str,
    max_rows: int,
) -> ParsedTransactionCsv:
    """Parse all-or-nothing CSV content into typed transactions.

    A batch is rejected if any row fails validation, if an ID appears twice in
    the file, or if the file exceeds configured limits.
    """

    safe_filename = Path(filename or "upload.csv").name
    if not content:
        raise _structural_error(
            code="empty_csv",
            message="The uploaded CSV file is empty",
        )

    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise _structural_error(
            code="invalid_csv_encoding",
            message="CSV must be UTF-8 encoded",
        ) from exc

    try:
        reader = csv.DictReader(io.StringIO(text, newline=""))
    except csv.Error as exc:
        raise _structural_error(
            code="invalid_csv",
            message="Unable to parse CSV file",
            details=str(exc),
        ) from exc

    if not reader.fieldnames:
        raise _structural_error(
            code="empty_csv",
            message="The CSV file has no header row",
        )

    normalized_headers = [
        header.strip().lower() for header in reader.fieldnames if header
    ]
    if len(normalized_headers) != len(set(normalized_headers)):
        raise _structural_error(
            code="duplicate_csv_columns",
            message="CSV header contains duplicate columns",
        )

    missing = sorted(REQUIRED_COLUMNS - set(normalized_headers))
    if missing:
        raise _structural_error(
            code="csv_missing_columns",
            message="CSV is missing required columns",
            details={"missing": missing, "required": sorted(REQUIRED_COLUMNS)},
        )

    transactions: list[Transaction] = []
    errors: list[IngestRowError] = []
    ids_seen: dict[Any, int] = {}
    data_rows = 0

    for row_number, raw_row in enumerate(reader, start=2):
        if raw_row is None:
            continue
        normalized_row: dict[str, Any] = {}
        for key, value in raw_row.items():
            if key is None:
                continue
            normalized_key = key.strip().lower()
            if isinstance(value, str):
                value = value.strip()
            normalized_row[normalized_key] = value

        if not any(
            value not in (None, "") for value in normalized_row.values()
        ):
            continue

        data_rows += 1
        if data_rows > max_rows:
            raise _structural_error(
                code="too_many_rows",
                message=f"CSV exceeds the {max_rows:,}-row ingestion limit",
                details={"max_rows": max_rows},
            )

        try:
            parsed = TransactionCsvRow.model_validate(normalized_row)
        except ValidationError as exc:
            errors.extend(_validation_errors(exc, row_number))
            continue

        transaction_id = parsed.id or uuid4()
        if transaction_id in ids_seen:
            errors.append(
                IngestRowError(
                    row=row_number,
                    field="id",
                    message=(
                        "Duplicate transaction id in file "
                        f"(first seen on line {ids_seen[transaction_id]})"
                    ),
                )
            )
            continue
        ids_seen[transaction_id] = row_number

        transactions.append(
            Transaction(
                id=transaction_id,
                from_account=parsed.from_account,
                to_account=parsed.to_account,
                amount=parsed.amount,
                currency=parsed.currency,
                timestamp=parsed.timestamp,
                device_id=parsed.device_id,
                ip_address=parsed.ip_address,
                channel=parsed.channel,
                label=parsed.label,
            )
        )

    if errors:
        raise _structural_error(
            code="csv_validation_failed",
            message="CSV contains invalid transaction rows",
            details={
                "errors": errors[:MAX_REPORTED_ERRORS],
                "error_count": len(errors),
                "row_count": data_rows,
            },
        )

    if not transactions:
        raise _structural_error(
            code="empty_csv",
            message="CSV contains no transaction rows",
        )

    return ParsedTransactionCsv(
        transactions=transactions,
        row_count=data_rows,
        filename=safe_filename,
    )
