from django.core.management.base import BaseCommand

from jobs.importer import import_telegram_channels


class Command(BaseCommand):
    help = "Import and update real vacancy posts from configured public sources."

    def add_arguments(self, parser):
        parser.add_argument("channels", nargs="*", help="Telegram usernames without @")

    def handle(self, *args, **options):
        created, updated, errors = import_telegram_channels(options["channels"] or None)
        self.stdout.write(self.style.SUCCESS(f"Imported {created} new and updated {updated} real vacancy posts."))
        for error in errors:
            self.stderr.write(self.style.WARNING(f"Source unavailable: {error}"))