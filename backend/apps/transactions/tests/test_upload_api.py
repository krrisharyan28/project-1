"""End-to-end test of the CSV upload endpoint (import + scoring)."""
import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.fraud.models import Alert

HEADER = "external_id,timestamp,amount,currency,merchant,category,country,channel,card_last4,customer_id"


def _csv(rows):
    body = "\n".join([HEADER, *rows]).encode("utf-8")
    return SimpleUploadedFile("upload.csv", body, content_type="text/csv")


@pytest.mark.django_db
def test_upload_imports_and_scores(auth_client):
    upload = _csv(
        [
            "TX1,2026-05-10T11:00:00,15000,USD,Rolex,jewelry,US,pos,4821,C1",  # flagged
            "TX2,2026-05-01T13:00:00,42,USD,Cafe,coffee,US,pos,4821,C1",       # clean
        ]
    )
    resp = auth_client.post(
        "/api/transactions/upload/", {"file": upload}, format="multipart"
    )
    assert resp.status_code == 201
    assert resp.data["imported"] == 2
    assert resp.data["flagged"] == 1
    assert Alert.objects.count() == 1


@pytest.mark.django_db
def test_upload_requires_file(auth_client):
    resp = auth_client.post("/api/transactions/upload/", {}, format="multipart")
    assert resp.status_code == 400


@pytest.mark.django_db
def test_upload_requires_auth(api_client):
    upload = _csv(["TX1,2026-05-01T13:00:00,42,USD,Cafe,coffee,US,pos,4821,C1"])
    resp = api_client.post(
        "/api/transactions/upload/", {"file": upload}, format="multipart"
    )
    assert resp.status_code == 401
