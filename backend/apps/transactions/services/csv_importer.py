"""
CSV import service.

Parses an uploaded transactions CSV, validates each row, and persists a
`TransactionBatch` with its `Transaction` rows in a single transaction.
Scoring is performed separately by the fraud engine (see the upload view).

Expected columns (header row, order-independent):

    external_id, timestamp, amount, currency, merchant, category,
    country, channel, card_last4, customer_id

`timestamp` is parsed as ISO-8601. `amount` must be a positive decimal.
"""
import csv
import io
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from django.db import transaction as db_transaction
from django.utils.dateparse import parse_datetime
from django.utils.timezone import make_aware, is_naive

from ..models import Transaction, TransactionBatch

REQUIRED_COLUMNS = {"external_id", "timestamp", "amount"}

OPTIONAL_COLUMNS = {
    "currency",
    "merchant",
    "category",
    "country",
    "channel",
    "card_last4",
    "customer_id",
}


class CsvImportError(Exception):
    """Raised when the uploaded file cannot be parsed into transactions."""


@dataclass
class ImportResult:
    batch: TransactionBatch
    transactions: list[Transaction]


def _parse_timestamp(raw: str, row_num: int):
    dt = parse_datetime(raw.strip())
    if dt is None:
        raise CsvImportError(f"Row {row_num}: invalid timestamp '{raw}'.")
    if is_naive(dt):
        dt = make_aware(dt)
    return dt


def _parse_amount(raw: str, row_num: int) -> Decimal:
    try:
        amount = Decimal(raw.strip())
    except (InvalidOperation, AttributeError) as exc:
        raise CsvImportError(f"Row {row_num}: invalid amount '{raw}'.") from exc
    if amount <= 0:
        raise CsvImportError(f"Row {row_num}: amount must be positive.")
    return amount


def import_file(uploaded_file, user) -> ImportResult:
    """Parse `uploaded_file` and persist a batch of transactions for `user`."""
    try:
        text = uploaded_file.read().decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise CsvImportError("File must be UTF-8 encoded text.") from exc

    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames is None:
        raise CsvImportError("CSV file is empty.")

    header = {name.strip() for name in reader.fieldnames}
    missing = REQUIRED_COLUMNS - header
    if missing:
        raise CsvImportError(f"Missing required column(s): {', '.join(sorted(missing))}.")

    with db_transaction.atomic():
        batch = TransactionBatch.objects.create(
            uploaded_by=user,
            filename=getattr(uploaded_file, "name", "upload.csv"),
        )

        rows: list[Transaction] = []
        for i, row in enumerate(reader, start=2):  # row 1 is the header
            rows.append(
                Transaction(
                    batch=batch,
                    external_id=(row.get("external_id") or "").strip(),
                    timestamp=_parse_timestamp(row.get("timestamp", ""), i),
                    amount=_parse_amount(row.get("amount", ""), i),
                    currency=(row.get("currency") or "USD").strip()[:3].upper(),
                    merchant=(row.get("merchant") or "").strip(),
                    category=(row.get("category") or "").strip().lower(),
                    country=(row.get("country") or "").strip().upper()[:2],
                    channel=(row.get("channel") or "").strip().lower(),
                    card_last4=(row.get("card_last4") or "").strip()[-4:],
                    customer_id=(row.get("customer_id") or "").strip(),
                )
            )

        if not rows:
            raise CsvImportError("CSV file contains no data rows.")

        Transaction.objects.bulk_create(rows)
        batch.row_count = len(rows)
        batch.save(update_fields=["row_count"])

    return ImportResult(batch=batch, transactions=rows)
