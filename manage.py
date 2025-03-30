#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
import random

# Set settings early.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'service_platform.settings')

from django.contrib.gis.db.models import PointField
from django_seed.guessers import FieldTypeGuesser
from django_seed import guessers
from django.utils import timezone
from django.db.models import PositiveSmallIntegerField

# --- Patch for FieldTypeGuesser: handle Review.rating and PointField ---
_original_guess_format = FieldTypeGuesser.guess_format

def custom_guess_format(self, field):
    # Check if the field belongs to a model named "Review" and its name is "rating".
    if field.model.__name__ == "Review" and field.name == "rating":
        # Return a lambda that accepts one argument and returns a random integer between 1 and 5.
        return lambda x: random.randint(1, 5)
    # If the field is a PointField, bypass it by returning a lambda that returns None.
    if isinstance(field, PointField):
        return lambda x: None
    return _original_guess_format(self, field)

FieldTypeGuesser.guess_format = custom_guess_format

# --- Patch for timezone formatting: remove unsupported is_dst parameter ---
def new_timezone_format(value):
    return timezone.make_aware(value, timezone.get_current_timezone())

guessers._timezone_format = new_timezone_format

def main():
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and available on your PYTHONPATH? "
            "Did you forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()
