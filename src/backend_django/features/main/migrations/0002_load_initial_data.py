import json
import os

from django.db import migrations


def load_data(apps, schema_editor):
    # 1. Load Categories
    Category = apps.get_model("main", "Category")
    load_fixture(Category, "initial_categories.json", ["slug"])

    # 2. Load Service Groups (depends on Category)
    ServiceGroup = apps.get_model("main", "ServiceGroup")
    load_fixture(ServiceGroup, "initial_groups.json", ["pk"])

    # 3. Load Services (depends on Category and Group)
    Service = apps.get_model("main", "Service")
    load_fixture(Service, "initial_services.json", ["slug"])

    # 4. Load Portfolio Images (depends on Service)
    PortfolioImage = apps.get_model("main", "PortfolioImage")
    load_fixture(PortfolioImage, "initial_portfolio.json", ["pk"])


def load_fixture(model_class, filename, lookup_fields):
    """
    Generic function to load data from a JSON fixture.
    Handles ForeignKey fields by appending '_id' if value is an integer.
    """
    fixture_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),  # features/main
        "fixtures",
        filename,
    )

    if not os.path.exists(fixture_path):
        print(f"Fixture not found: {fixture_path}")
        return

    # Identify ForeignKey fields in the model
    fk_fields = {f.name for f in model_class._meta.get_fields() if f.is_relation and f.many_to_one and f.related_model}

    with open(fixture_path, encoding="utf-8") as f:
        data = json.load(f)

        for item in data:
            fields = item["fields"]
            pk = item.get("pk")

            # Prepare data for update_or_create
            # We need to handle ForeignKeys: if JSON has "category": 3, Django needs "category_id": 3
            processed_fields = {}
            for key, value in fields.items():
                if key in fk_fields and isinstance(value, int):
                    processed_fields[f"{key}_id"] = value
                else:
                    processed_fields[key] = value

            # Prepare lookup kwargs
            lookup = {}
            for field in lookup_fields:
                if field == "pk":
                    lookup["pk"] = pk
                else:
                    # Check if lookup field was renamed to _id
                    if field in fk_fields and isinstance(fields.get(field), int):
                        lookup[f"{field}_id"] = fields.get(field)
                    else:
                        lookup[field] = fields.get(field)

            # Remove lookup keys from defaults to avoid "duplicate key" issues in update
            defaults = processed_fields.copy()
            for key in lookup:
                if key in defaults:
                    del defaults[key]

            # We use update_or_create to ensure idempotency
            model_class.objects.update_or_create(defaults=defaults, **lookup)
            print(f"Loaded {model_class.__name__}: {lookup}")


def reverse_func(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("main", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(load_data, reverse_func),
    ]
