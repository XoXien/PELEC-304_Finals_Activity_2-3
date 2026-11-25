from importlib import import_module

from django.apps import apps
from django.core.management.base import BaseCommand
from django.db import router, transaction

from catalog.models import Product


class Command(BaseCommand):
    help = "Restore missing example products while preserving existing catalog edits."

    def handle(self, *args, **options):
        database = router.db_for_write(Product)
        original_examples = import_module("catalog.migrations.0002_sample_products")
        with transaction.atomic(using=database):
            before = Product.objects.using(database).count()
            original_examples.seed_catalog(apps, database)
            created = Product.objects.using(database).count() - before
        self.stdout.write(self.style.SUCCESS(f"Added {created} missing example products."))
