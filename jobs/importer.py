import logging
import os

import httpx
from django.db import transaction

from .models import Vacancy
from .sources.telegram import VacancySourceItem, fetch_channel

logger = logging.getLogger(__name__)


def import_item(item: VacancySourceItem) -> tuple[Vacancy, bool]:
    lookup = {"source": item.source, "external_id": item.external_id}
    vacancy = Vacancy.objects.filter(**lookup).first() or Vacancy.objects.filter(source_url=item.source_url).first()
    defaults = {
        "url": item.source_url,
        "source_url": item.source_url,
        "title": item.title,
        "text": item.text,
        "date": item.date,
        "channel": item.channel,
        "source": item.source,
        "external_id": item.external_id,
        "is_demo": False,
    }
    with transaction.atomic():
        if vacancy:
            for field, value in defaults.items():
                setattr(vacancy, field, value)
            vacancy.save()
            return vacancy, False
        return Vacancy.objects.create(**defaults), True


def import_telegram_channels(channels: list[str] | None = None) -> tuple[int, int, list[str]]:
    configured = channels or os.getenv("TELEGRAM_CHANNELS", "kasbim_uz,job_react,ayti_jobs,smmprtashkent").split(",")
    created = updated = 0
    errors = []
    for channel in configured:
        try:
            for item in fetch_channel(channel):
                _, was_created = import_item(item)
                created += int(was_created)
                updated += int(not was_created)
        except (httpx.HTTPError, ValueError) as error:
            logger.exception("Telegram source failed: %s", channel)
            errors.append(f"{channel}: {error}")
    return created, updated, errors