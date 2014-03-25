"""
Management wrapper for running textmetrics build processes
(see tm/build/pipeline.py)
"""

from django.core.management.base import BaseCommand

from apps.tm.build.pipeline import dispatch


class Command(BaseCommand):
    help = 'Run build processes for textmetrics data'

    def handle(self, *args, **options):
        dispatch()
