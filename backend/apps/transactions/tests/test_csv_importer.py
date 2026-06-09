"""Tests for the CSV import service."""
import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.transactions.models import Transaction
from apps.transactions.services.csv_importer import CsvImportError, import_file

HEADER = "external_id,timestamp,amount,currency,merchant,category,country,channel,card_last4,customer_id"


def _csv(rows):
    body = "\n".join([HEADER, *rows]).encode("utf-8")
    return SimpleUploadedFile("test.csv", body, content_type="text/csv")


@pytest.mark.django_db
def test_import_creates_transactions(analyst):
    upload = _csv(
        [
            "TX1,2026-05-01T12:00:00,42.50,USD,Starbucks,coffee,US,pos,4821,CUST1",
            "TX2,2026-05-02T13:00:00,120.00,USD,Amazon,retail,US,online,4821,CUST1",
        ]
    )
    result = import_file(upload, analyst)

    assert result.batch.row_count == 2
    assert len(result.transactions) == 2
    assert Transaction.objects.count() == 2
    txn = Transaction.objects.get(external_id="TX1")
    assert txn.amount == 42.50
    assert txn.country == "US"


@pytest.mark.django_db
def test_missing_required_column_raises(analyst):
    bad = SimpleUploadedFile(
        "bad.csv", b"external_id,amount\nTX1,10", content_type="text/csv"
    )
    with pytest.raises(CsvImportError, match="Missing required column"):
        import_file(bad, analyst)


@pytest.mark.django_db
def test_invalid_amount_raises(analyst):
    upload = _csv(["TX1,2026-05-01T12:00:00,notanumber,USD,M,retail,US,pos,1111,C1"])
    with pytest.raises(CsvImportError, match="invalid amount"):
        import_file(upload, analyst)


@pytest.mark.django_db
def test_negative_amount_raises(analyst):
    upload = _csv(["TX1,2026-05-01T12:00:00,-5,USD,M,retail,US,pos,1111,C1"])
    with pytest.raises(CsvImportError, match="must be positive"):
        import_file(upload, analyst)


@pytest.mark.django_db
def test_empty_data_rows_raises(analyst):
    upload = _csv([])
    with pytest.raises(CsvImportError, match="no data rows"):
        import_file(upload, analyst)
