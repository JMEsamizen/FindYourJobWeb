from dataclasses import dataclass

import httpx
from bs4 import BeautifulSoup


@dataclass(frozen=True)
class VacancySourceItem:
    external_id: str
    title: str
    text: str
    date: str
    source: str
    source_url: str
    channel: str


def fetch_channel(channel: str, timeout: int = 20) -> list[VacancySourceItem]:
    channel = channel.strip().lstrip("@")
    if not channel:
        return []
    response = httpx.get(
        f"https://t.me/s/{channel}",
        timeout=timeout,
        follow_redirects=True,
        headers={"User-Agent": "FindYourJob/1.0"},
    )
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    items = []
    for message in soup.select("div.tgme_widget_message[data-post]"):
        text_node = message.select_one("div.tgme_widget_message_text")
        date_link = message.select_one("a.tgme_widget_message_date")
        if not text_node or not date_link:
            continue
        text = text_node.get_text(" ", strip=True)
        source_url = date_link.get("href", "").strip()
        external_id = message.get("data-post", "").strip()
        if not text or not source_url or not external_id:
            continue
        date_node = date_link.select_one("time")
        items.append(VacancySourceItem(
            external_id=external_id,
            title=text.split("\n", 1)[0][:240],
            text=text,
            date=date_node.get("datetime", "") if date_node else "",
            source="Telegram",
            source_url=source_url,
            channel=channel,
        ))
    return items