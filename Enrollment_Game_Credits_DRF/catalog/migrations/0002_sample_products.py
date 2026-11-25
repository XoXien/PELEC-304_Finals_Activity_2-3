"""Twenty-four sample products for Finals Activity #3.

Denominations identify example products; prices and stock are classroom data.
Existing catalog rows are preserved when seed_products is run again.
"""
from decimal import Decimal

from django.db import migrations


GAME_DATA = [
    ("valorant", "VALORANT", "VAL", "VP", "coral", [
        (475, "199.00"), (1000, "399.00"), (2050, "799.00"),
        (3650, "1399.00"), (5350, "1999.00"), (11000, "3999.00"),
    ]),
    ("mobile-legends", "Mobile Legends: Bang Bang", "MLBB", "Diamonds", "gold", [
        (56, "65.00"), (112, "125.00"), (223, "250.00"),
        (336, "375.00"), (570, "625.00"), (1163, "1250.00"),
    ]),
    ("genshin-impact", "Genshin Impact", "GI", "Genesis Crystals", "mint", [
        (60, "59.00"), (330, "279.00"), (1090, "849.00"),
        (2240, "1699.00"), (3880, "2799.00"), (8080, "5599.00"),
    ]),
    ("honkai-star-rail", "Honkai: Star Rail", "HSR", "Oneiric Shards", "violet", [
        (60, "59.00"), (330, "279.00"), (1090, "849.00"),
        (2240, "1699.00"), (3880, "2799.00"), (8080, "5599.00"),
    ]),
]


def seed_catalog(apps, database):
    Game = apps.get_model("catalog", "Game")
    Product = apps.get_model("catalog", "Product")
    for game_index, (slug, name, short, unit, theme, packages) in enumerate(GAME_DATA):
        game, _ = Game.objects.using(database).get_or_create(slug=slug, defaults={
            "name": name, "short_name": short, "credit_unit": unit, "theme": theme,
        })
        for index, (credits, price) in enumerate(packages):
            Product.objects.using(database).get_or_create(sku=f"{short}-{credits:05d}", defaults={
                "game": game,
                "name": f"{name} — {credits:,} {unit}",
                "description": (
                    f"A {credits:,} {unit} package for {name}. "
                    "Sample catalog item for this classroom activity; no real credits are delivered."
                ),
                "credit_amount": credits, "price": Decimal(price),
                "stock": 0 if (game_index, index) == (3, 5) else 120 - index * 14,
                "featured": (game_index, index) in {(0, 1), (1, 4), (2, 1), (3, 2)},
            })


def forwards(apps, schema_editor):
    seed_catalog(apps, schema_editor.connection.alias)


class Migration(migrations.Migration):
    dependencies = [("catalog", "0001_initial")]
    operations = [migrations.RunPython(forwards, migrations.RunPython.noop)]
