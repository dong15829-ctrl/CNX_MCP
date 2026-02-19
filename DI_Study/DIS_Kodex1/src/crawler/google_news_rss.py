import html
import logging
from dataclasses import dataclass
from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import List, Dict
from urllib.parse import quote

import requests


LOGGER = logging.getLogger("google_news_rss")


@dataclass
class GoogleNewsRSSCrawler:
    """
    Lightweight RSS fallback for Google SERP crawling.
    Uses the public Google News RSS endpoint which is much
    less aggressive about bot-detection compared to the
    interactive SERP.
    """

    base_url: str = "https://news.google.com/rss/search"

    def __post_init__(self) -> None:
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                "Accept": "application/rss+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            }
        )

    def search(self, keyword: str, max_results: int = 10) -> List[Dict]:
        params = {
            "q": keyword,
            "hl": "ko",
            "gl": "KR",
            "ceid": "KR:ko",
        }
        try:
            response = self.session.get(
                self.base_url, params=params, timeout=15
            )
            response.raise_for_status()
        except Exception as exc:  # noqa: BLE001
            LOGGER.warning("Google RSS request failed: %s", exc)
            return []

        try:
            # RSS feed does not depend on XML namespaces, so ElementTree is sufficient.
            import xml.etree.ElementTree as ET

            root = ET.fromstring(response.text)
        except Exception as exc:  # noqa: BLE001
            LOGGER.warning("Google RSS parsing failed: %s", exc)
            return []

        items = []
        for item in root.findall(".//item"):
            link = (item.findtext("link") or "").strip()
            title = html.unescape((item.findtext("title") or "").strip())
            description = html.unescape((item.findtext("description") or "").strip())
            pub_date_raw = item.findtext("pubDate")

            if not title or not link:
                continue

            published_at = ""
            if pub_date_raw:
                try:
                    dt = parsedate_to_datetime(pub_date_raw)
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=datetime.now().astimezone().tzinfo)
                    published_at = dt.astimezone().isoformat()
                except Exception:  # noqa: BLE001
                    published_at = ""

            items.append(
                {
                    "keyword": keyword,
                    "title": title,
                    "url": link,
                    "snippet": description,
                    "source": "google_news_rss",
                    "published_at": published_at,
                    "crawled_at": datetime.now().isoformat(),
                }
            )

            if len(items) >= max_results:
                break

        return items

