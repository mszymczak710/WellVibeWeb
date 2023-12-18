from django.db import connection, models


class AutoIncrementField(models.PositiveIntegerField):
    """
    A custom field that provides auto-increment functionality for Django models using a PostgreSQL sequence.

    This field is a positive integer field that automatically generates a unique
    sequence number upon saving a new model instance. It uses a PostgreSQL sequence
    to ensure the number is incremented atomically.

    The sequence name is derived from the model's table name and the field's attribute name,
    ensuring that each field has its own dedicated sequence.

    If the field's value is already set, or if the instance is not new (i.e., add=False),
    the field's value is not altered and the default `pre_save` behavior is used.
    """

    def pre_save(self, model_instance, add):
        """
        Determines the value of the field just before saving the model instance.

        Args:
            model_instance: The instance of the model where the field is defined.
            add: A boolean indicating whether this is a new instance being added.

        Returns:
            The value to be saved for this field.
        """
        if add and not getattr(model_instance, self.attname):
            # Generate the next value in the sequence if this is a new instance
            # and the field isn't already populated.
            with connection.cursor() as cursor:
                sequence_name = (
                    f"{model_instance._meta.db_table}_{self.attname}_seq"
                )
                cursor.execute(f"SELECT nextval('{sequence_name}')")
                value = cursor.fetchone()[0]
                setattr(model_instance, self.attname, value)
                return value
        else:
            # For existing instances or if the field is already set, use the default behavior.
            return super().pre_save(model_instance, add)
