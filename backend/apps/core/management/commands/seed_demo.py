"""
Seed the database with a demo analyst account and the sample transaction batch
(scored by the fraud engine) so the dashboard is populated for screenshots.

    python manage.py seed_demo            # create demo user + import sample CSV
    python manage.py seed_demo --reset    # wipe existing transactions first
"""
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from apps.fraud.models import Alert
from apps.fraud.services.engine import FraudEngine
from apps.transactions.models import Transaction, TransactionBatch
from apps.transactions.services.csv_importer import import_file

User = get_user_model()

DEMO_USERNAME = "analyst"
DEMO_PASSWORD = "analyst123"
SAMPLE_CSV = Path(settings.BASE_DIR) / "data" / "sample_transactions.csv"


class Command(BaseCommand):
    help = "Seed a demo analyst user and a scored sample transaction batch."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete existing transactions, batches and alerts first.",
        )

    def handle(self, *args, **options):
        if options["reset"]:
            Alert.objects.all().delete()
            Transaction.objects.all().delete()
            TransactionBatch.objects.all().delete()
            self.stdout.write(self.style.WARNING("Cleared existing transaction data."))

        user, created = User.objects.get_or_create(
            username=DEMO_USERNAME,
            defaults={"email": "analyst@example.com", "role": User.Role.ANALYST},
        )
        if created:
            user.set_password(DEMO_PASSWORD)
            user.save()
            self.stdout.write(
                self.style.SUCCESS(
                    f"Created demo user '{DEMO_USERNAME}' / '{DEMO_PASSWORD}'."
                )
            )
        else:
            self.stdout.write(f"Demo user '{DEMO_USERNAME}' already exists.")

        if not SAMPLE_CSV.exists():
            self.stderr.write(self.style.ERROR(f"Sample CSV not found: {SAMPLE_CSV}"))
            return

        with SAMPLE_CSV.open("rb") as handle:
            result = import_file(handle, user)

        scoring = FraudEngine().score_batch(result.batch, result.transactions)

        self.stdout.write(
            self.style.SUCCESS(
                f"Imported {result.batch.row_count} transactions; "
                f"flagged {scoring.flagged_count} as alerts."
            )
        )
