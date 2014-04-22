"""
Management wrapper for running textmetrics build processes
(see tm/build/pipeline.py)
"""

from django.core.management.base import BaseCommand
from apps.tm.build.test.antedatings import full_text_stats


class Command(BaseCommand):
    help = 'Run antedatings test process using textmetrics data'

    def handle(self, *args, **options):
        full_text_stats()
