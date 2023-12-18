import json
import logging
import os
from gettext import ngettext
from typing import Any, Dict, Optional, Type

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Model

from clinic.dictionaries.models import (
    Disease,
    Ingredient,
    Medicine,
    MedicineForm,
    MedicineIngredient,
    MedicineType,
    Office,
    OfficeType,
    Specialization,
)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Custom management command to load data into Specializations, Diseases, and Medicines models.

    Reads JSON files for each model and populates the database with their contents.
    If a record with the same name exists, it's skipped; otherwise, it's added.
    """

    help = "Load data for Specializations, Diseases, Medicines and Offices from JSON files"

    # Path to JSON files relative to the BASE_DIR setting
    data_paths = {
        Specialization: "specializations.json",
        Disease: "diseases.json",
        Medicine: "medicines.json",
        Office: "offices.json",
    }

    def load_data(
        self, model: Type[Model], defaults: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Load data from a JSON file into the specified model.

        Args:
            model (Type[Model]): The model class to which the data will be loaded.
            defaults (Optional[Dict[str, Any]]): Default values to use when creating new model instances.
        """
        # Set defaults to an empty dictionary if not provided
        if defaults is None:
            defaults = {}

        # Construct the full file path to the JSON data file
        file_path = os.path.join(
            settings.BASE_DIR,
            "clinic",
            "dictionaries",
            "data",
            self.data_paths[model],
        )

        new_objects_count = 0
        existing_objects_count = 0

        try:
            with open(file_path, "r") as file:
                data = json.load(file)
                for item in data:
                    # Handle specific logic for Medicine model
                    if model == Medicine:
                        # Retrieve or create the related MedicineType and MedicineForm instances
                        type_obj, _ = MedicineType.objects.get_or_create(
                            name=item["type_of_medicine"]
                        )
                        form_obj, _ = MedicineForm.objects.get_or_create(
                            name=item["form"]
                        )

                        # Create or update the Medicine instance
                        medicine, created = Medicine.objects.get_or_create(
                            name=item["name"],
                            defaults={
                                **defaults,
                                "type_of_medicine": type_obj,
                                "form": form_obj,
                            },
                        )

                        # Handle active ingredients
                        for ingredient_data in item["active_ingredients"]:
                            ingredient, _ = Ingredient.objects.get_or_create(
                                name=ingredient_data["name"]
                            )
                            MedicineIngredient.objects.update_or_create(
                                medicine=medicine,
                                ingredient=ingredient,
                                defaults={
                                    "quantity": ingredient_data["quantity"],
                                    "unit": ingredient_data["unit"],
                                },
                            )

                    # Handle specific logic for Office model
                    elif model == Office:
                        type_obj, _ = OfficeType.objects.get_or_create(
                            name=item["office_type"]
                        )
                        office, created = model.objects.get_or_create(
                            office_type=type_obj,
                            floor=item["floor"],
                            defaults=defaults,
                        )
                    else:
                        # For other models
                        obj, created = model.objects.get_or_create(
                            name=item["name"], defaults={**defaults, **item}
                        )

                    # Increment counters based on whether the object was newly created or already existed
                    if created:
                        new_objects_count += 1
                    else:
                        existing_objects_count += 1

            # Log the results of the data loading
            if new_objects_count > 0:
                logger.info(
                    f"Added {new_objects_count} new {model.__name__} objects."
                )
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Added {new_objects_count} new {model.__name__} objects."
                    )
                )

            if existing_objects_count > 0:
                model_name_plural = ngettext(
                    f"{model._meta.verbose_name}",
                    f"{model._meta.verbose_name_plural}",
                    existing_objects_count,
                )
                logger.info(
                    f"{existing_objects_count} {model_name_plural} already loaded."
                )
                self.stdout.write(
                    self.style.WARNING(
                        f"{existing_objects_count} {model_name_plural} already loaded.\n"
                    )
                )

        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"Error loading data: {e}")
            self.stderr.write(self.style.ERROR(f"Error loading data: {e}\n\n"))
            raise CommandError("Error loading data") from e

    def handle(self, *args, **kwargs):
        """
        Execute the management command to load data for the models from their respective JSON files.
        """
        logger.info("Starting data loading...")
        self.stdout.write(
            self.style.HTTP_INFO("\n\nStarting data loading...\n\n")
        )
        try:
            self.load_data(Specialization)
            self.load_data(Disease)
            self.load_data(Medicine)
            self.load_data(Office)

            logger.info("Data loading process completed.")
            self.stdout.write(
                self.style.SUCCESS("\n\nData loading process completed.\n\n")
            )

        except CommandError as e:
            self.stderr.write(
                self.style.ERROR(f"Data loading failed: {e}\n\n")
            )
            logger.error("Data loading failed")
