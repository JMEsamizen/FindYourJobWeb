import os
import httpx
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from ашду.findyourjob_portal.jobs.models import Vacancy


class Command(BaseCommand):
    help = "Fetch public Telegram channel posts into Vacancy records."

    def add_arguments(self, parser):
        parser.add_argument("channels", nargs="*", help="Telegram usernames without @")

    def handle(self, *args, **options):
        channels = options["channels"] or os.getenv("TELEGRAM_CHANNELS", "kasbim_uz,job_react,ayti_jobs,smmprtashkent,testjobs4224").split(",")
        total = 0
        for channel in channels:
            response = httpx.get(f"https://t.me/s/{channel.strip()}", timeout=20, follow_redirects=True, headers={"User-Agent": "FindYourJob/1.0"})
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            for message in soup.select("div.tgme_widget_message[data-post]"):
                text_node = message.select_one("div.tgme_widget_message_text")
                date_link = message.select_one("a.tgme_widget_message_date")
                if not text_node or not date_link:
                    continue
                text = text_node.get_text(" ", strip=True)
                url = date_link.get("href", "")
                if not text or not url:
                    continue
                date_node = date_link.select_one("time")
                Vacancy.objects.update_or_create(url=url, defaults={"title": text.split("\n", 1)[0][:240], "text": text, "date": date_node.get("datetime", "") if date_node else "", "channel": channel.strip()})
                total += 1
        self.stdout.write(self.style.SUCCESS(f"Imported {total} vacancy posts."))
