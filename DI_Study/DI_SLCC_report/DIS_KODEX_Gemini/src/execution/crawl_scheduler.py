from __future__ import annotations

import argparse
import asyncio
import json
import logging
import random
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Awaitable, Callable, Dict, List, Optional

from src.crawler.google_crawler import GoogleCrawler
from src.crawler.google_advanced import AdvancedGoogleCrawler
from src.crawler.naver_crawler import NaverCrawler
from src.crawler.naver_advanced import AdvancedNaverCrawler
from src.crawler.stock_community_crawlers import (
    DCInsideCrawler,
    MiraeassetCrawler,
)
from src.crawler.youtube_crawler import YouTubeCrawler
from src.crawler.youtube_ultra_stealth import YouTubeCrawlerUltraStealth

CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "crawl_targets.json"


@dataclass(frozen=True)
class JobConfig:
    """Represents a job definition loaded from the config file."""

    id: str
    source: str
    keywords: List[str]
    params: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True


@dataclass(frozen=True)
class CrawlTask:
    """Concrete crawl task for a single keyword within a job."""

    job: JobConfig
    keyword: str

    @property
    def source(self) -> str:
        return self.job.source


async def run_google_basic(keyword: str, params: Dict[str, Any]) -> Any:
    crawler = GoogleCrawler(output_dir=params.get("output_dir", "data/raw/google"))
    max_results = params.get("max_results", 10)
    return await crawler.search(keyword, max_results=max_results)


async def run_google_advanced(keyword: str, params: Dict[str, Any]) -> Any:
    crawler = AdvancedGoogleCrawler()
    max_results = params.get("max_results", 10)
    return await crawler.search(keyword, max_results=max_results)


async def run_naver_blog_mobile(keyword: str, params: Dict[str, Any]) -> Any:
    crawler = NaverCrawler(output_dir=params.get("output_dir", "data/raw/naver"))
    max_posts = params.get("max_posts", 10)
    return await crawler.search_blog(keyword, max_posts=max_posts)


async def run_naver_cafe_mobile(keyword: str, params: Dict[str, Any]) -> Any:
    crawler = NaverCrawler(output_dir=params.get("output_dir", "data/raw/naver"))
    max_posts = params.get("max_posts", 10)
    return await crawler.search_cafe(keyword, max_posts=max_posts)


async def run_naver_blog_advanced(keyword: str, params: Dict[str, Any]) -> Any:
    crawler = AdvancedNaverCrawler()
    max_posts = params.get("max_posts", 20)
    return await crawler.search_blog(keyword, max_posts=max_posts)


async def run_naver_cafe_advanced(keyword: str, params: Dict[str, Any]) -> Any:
    crawler = AdvancedNaverCrawler()
    max_posts = params.get("max_posts", 20)
    return await crawler.search_cafe(keyword, max_posts=max_posts)


async def run_naver_stock_cafe(keyword: str, params: Dict[str, Any]) -> Any:
    crawler = AdvancedNaverCrawler()
    max_posts = params.get("max_posts", 20)
    return await crawler.search_stock_cafe(keyword, max_posts=max_posts)


async def run_youtube_standard(keyword: str, params: Dict[str, Any]) -> Any:
    crawler = YouTubeCrawler(output_dir=params.get("output_dir", "data/raw/youtube"))
    return await crawler.search_and_crawl(
        keyword,
        max_videos=params.get("max_videos", 10),
        collect_comments=params.get("collect_comments", True),
        max_comments_per_video=params.get("max_comments_per_video", 50),
    )


async def run_youtube_ultra(keyword: str, params: Dict[str, Any]) -> Any:
    crawler = YouTubeCrawlerUltraStealth(
        output_dir=params.get("output_dir", "data/raw/youtube")
    )
    return await crawler.search_and_crawl(
        keyword,
        max_videos=params.get("max_videos", 10),
        collect_comments=params.get("collect_comments", True),
        max_comments_per_video=params.get("max_comments_per_video", 50),
    )


async def run_dcinside(keyword: str, params: Dict[str, Any]) -> Any:
    crawler = DCInsideCrawler()
    max_posts = params.get("max_posts", 20)
    return await crawler.crawl_gallery(keyword=keyword, max_posts=max_posts)


async def run_miraeasset(keyword: str, params: Dict[str, Any]) -> Any:
    crawler = MiraeassetCrawler()
    max_items = params.get("max_items", 25)
    return await crawler.crawl_etf_info(keyword=keyword, max_items=max_items)


SOURCE_RUNNERS: Dict[str, Callable[[str, Dict[str, Any]], Awaitable[Any]]] = {
    "google_basic": run_google_basic,
    "google_advanced": run_google_advanced,
    "naver_blog_mobile": run_naver_blog_mobile,
    "naver_cafe_mobile": run_naver_cafe_mobile,
    "naver_blog_advanced": run_naver_blog_advanced,
    "naver_cafe_advanced": run_naver_cafe_advanced,
    "naver_stock_cafe": run_naver_stock_cafe,
    "youtube_standard": run_youtube_standard,
    "youtube_ultra": run_youtube_ultra,
    "dcinside_stock": run_dcinside,
    "miraeasset_etf": run_miraeasset,
}


class CrawlOrchestrator:
    """Coordinates multi-source crawling runs."""

    def __init__(
        self,
        config: Dict[str, Any],
        *,
        concurrency_override: Optional[int] = None,
        retry_override: Optional[int] = None,
    ) -> None:
        self.config = config
        self._jobs: List[JobConfig] = self._parse_jobs(config.get("jobs", []))
        global_cfg = config.get("global", {})
        self.max_concurrency = concurrency_override or global_cfg.get(
            "max_concurrency", 2
        )
        self.retry_limit = retry_override if retry_override is not None else global_cfg.get(
            "retry_limit", 2
        )
        backoff_range = global_cfg.get("retry_backoff_seconds", [5, 20])
        if len(backoff_range) != 2:
            backoff_range = [5, 20]
        self.backoff_min, self.backoff_max = sorted(backoff_range)

        self.logger = logging.getLogger("crawl_orchestrator")

    @staticmethod
    def _parse_jobs(job_items: List[Dict[str, Any]]) -> List[JobConfig]:
        jobs: List[JobConfig] = []
        for item in job_items:
            try:
                job = JobConfig(
                    id=item["id"],
                    source=item["source"],
                    keywords=item.get("keywords", []),
                    params=item.get("params", {}),
                    enabled=item.get("enabled", True),
                )
                jobs.append(job)
            except KeyError as exc:
                logging.warning("Skipping invalid job config missing key %s: %s", exc, item)
        return jobs

    def collect_tasks(
        self,
        job_ids: Optional[List[str]] = None,
        sources: Optional[List[str]] = None,
    ) -> List[CrawlTask]:
        job_filter = set(job_ids) if job_ids else None
        source_filter = set(sources) if sources else None
        tasks: List<CrawlTask] = []

        for job in self._jobs:
            if not job.enabled:
                continue
            if job_filter and job.id not in job_filter:
                continue
            if source_filter and job.source not in source_filter:
                continue
            for keyword in job.keywords:
                keyword_clean = keyword.strip()
                if not keyword_clean:
                    continue
                tasks.append(CrawlTask(job=job, keyword=keyword_clean))
        return tasks

    async def run_tasks(self, tasks: List[CrawlTask]) -> Dict[str, Any]:
        if not tasks:
            self.logger.warning("No crawl tasks to run. Check your filters/config.")
            return {"total": 0, "success": 0, "failed": 0, "skipped": 0}

        semaphore = asyncio.Semaphore(self.max_concurrency)
        self.logger.info(
            "Starting crawl run: %d tasks | concurrency=%d | retry_limit=%d",
            len(tasks),
            self.max_concurrency,
            self.retry_limit,
        )

        async def runner(task: CrawlTask) -> Dict[str, Any]:
            async with semaphore:
                return await self._execute_with_retry(task)

        results = await asyncio.gather(*(runner(task) for task in tasks))

        summary = {
            "total": len(results),
            "success": sum(1 for r in results if r["status"] == "success"),
            "failed": sum(1 for r in results if r["status"] == "failed"),
            "skipped": sum(1 for r in results if r["status"] == "skipped"),
        }
        self.logger.info(
            "Crawl run completed: %s",
            summary,
        )
        return summary

    async def _execute_with_retry(self, task: CrawlTask) -> Dict[str, Any]:
        runner = SOURCE_RUNNERS.get(task.source)
        if runner is None:
            self.logger.error(
                "No runner registered for source '%s' (job=%s)",
                task.source,
                task.job.id,
            )
            return {"status": "skipped", "task": task, "reason": "unknown_source"}

        attempt = 0
        while True:
            attempt += 1
            try:
                start = time.perf_counter()
                payload = await runner(task.keyword, task.job.params)
                duration = time.perf_counter() - start
                item_count = len(payload) if isinstance(payload, list) else None
                self.logger.info(
                    "[SUCCESS] job=%s source=%s keyword='%s' items=%s duration=%.1fs",
                    task.job.id,
                    task.source,
                    task.keyword,
                    item_count if item_count is not None else "-",
                    duration,
                )
                return {"status": "success", "task": task, "items": item_count}
            except Exception as exc:  # noqa: BLE001
                self.logger.exception(
                    "[FAIL] job=%s source=%s keyword='%s' attempt=%d/%d error=%s",
                    task.job.id,
                    task.source,
                    task.keyword,
                    attempt,
                    self.retry_limit + 1,
                    exc,
                )
                if attempt > self.retry_limit:
                    return {"status": "failed", "task": task, "error": str(exc)}
                wait_time = self._backoff_seconds(attempt)
                self.logger.info(
                    "Retrying job=%s keyword='%s' in %.1fs...",
                    task.job.id,
                    task.keyword,
                    wait_time,
                )
                await asyncio.sleep(wait_time)

    def _backoff_seconds(self, attempt: int) -> float:
        base = random.uniform(self.backoff_min, self.backoff_max)
        jitter = random.uniform(0, 1)
        return base * (1 + (attempt - 1) * 0.3) + jitter

    @staticmethod
    def describe_tasks(tasks: List[CrawlTask]) -> List[str]:
        lines = []
        for task in tasks:
            lines.append(
                f"{task.job.id} [{task.source}] -> '{task.keyword}' "
                f"(params={task.job.params})"
            )
        return lines


def load_config(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Crawl config not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="KODEX multi-source crawl orchestrator",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=CONFIG_PATH,
        help="Path to crawl target configuration (JSON).",
    )
    parser.add_argument(
        "--jobs",
        nargs="*",
        help="Specific job IDs to run.",
    )
    parser.add_argument(
        "--sources",
        nargs="*",
        help="Specific source keys to run (see config).",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        help="Override max concurrency.",
    )
    parser.add_argument(
        "--retry-limit",
        type=int,
        help="Override retry limit per task.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned tasks and exit without running Playwright.",
    )
    return parser.parse_args(argv)


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


def main(argv: Optional[List[str]] = None) -> None:
    args = parse_args(argv)
    configure_logging()

    try:
        config = load_config(args.config)
    except FileNotFoundError as exc:
        logging.error(exc)
        sys.exit(1)

    orchestrator = CrawlOrchestrator(
        config,
        concurrency_override=args.concurrency,
        retry_override=args.retry_limit,
    )

    tasks = orchestrator.collect_tasks(job_ids=args.jobs, sources=args.sources)

    if args.dry_run:
        lines = orchestrator.describe_tasks(tasks)
        if not lines:
            logging.info("No tasks selected for dry-run.")
            return
        logging.info("Planned tasks (%d):", len(lines))
        for line in lines:
            logging.info(" - %s", line)
        return

    asyncio.run(orchestrator.run_tasks(tasks))


if __name__ == "__main__":
    main()
