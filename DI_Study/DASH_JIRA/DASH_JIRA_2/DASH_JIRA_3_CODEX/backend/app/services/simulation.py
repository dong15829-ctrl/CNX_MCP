from __future__ import annotations

from pathlib import Path
from typing import List

from ..config import SIMULATION_MAX_BATCH, TEST_DATA_FILE
from .data_loader import JiraDataRepository, repository


class TestDatasetSimulator:
    def __init__(self, repository: JiraDataRepository, dataset_path: Path | str = TEST_DATA_FILE) -> None:
        self._repository = repository
        self._dataset_path = Path(dataset_path)
        self._df = JiraDataRepository.load_dataset(self._dataset_path)
        self._total = len(self._df)
        self._cursor = 0
        self._last_batch: List[str] = []
        self._last_batch_details: List[dict] = []

    def reset(self) -> None:
        self._cursor = 0
        self._last_batch = []
        self._last_batch_details = []

    def ingest_next(self, batch: int = 1) -> List[str]:
        if self._df.empty:
            return []
        batch = max(1, min(batch, SIMULATION_MAX_BATCH))
        ingested: List[str] = []
        details: List[dict] = []
        while len(ingested) < batch and self._cursor < self._total:
            row = self._df.iloc[self._cursor]
            self._cursor += 1
            record = row.to_dict()
            issue_key = record.get("issue_key")
            if issue_key:
                self._repository.upsert_issue(record)
                ingested.append(issue_key)
                enriched = {
                    "issue_key": issue_key,
                    "summary": record.get("summary"),
                    "status": record.get("status"),
                    "priority": record.get("priority"),
                    "region": record.get("region"),
                    "category": record.get("category"),
                }
                # 간단한 분석 결과를 포함해 신규 티켓 내용/번역을 바로 볼 수 있도록 한다.
                try:
                    if self._repository._analysis_engine:
                        analysis = self._repository.get_issue_analysis(issue_key, refresh=True)
                        translation = analysis.get("translation", {}) if isinstance(analysis, dict) else {}
                        summary = analysis.get("summary", {}) if isinstance(analysis, dict) else {}
                        cases = analysis.get("case_recommendations", []) if isinstance(analysis, dict) else []
                        assignment = analysis.get("assignment") if isinstance(analysis, dict) else None
                        notifications = analysis.get("notifications") if isinstance(analysis, dict) else None
                        summary_text = (
                            translation.get("summary_translated")
                            or translation.get("summary_original")
                            or record.get("summary")
                        )
                        desc_text = (
                            translation.get("description_translated")
                            or translation.get("description_original")
                            or record.get("description")
                        )
                        enriched["translation"] = {
                            "summary": summary_text,
                            "description": desc_text,
                            "summary_original": translation.get("summary_original") or record.get("summary"),
                            "description_original": translation.get("description_original") or record.get("description"),
                        }
                        enriched["summary_outline"] = summary.get("description_summary")
                        enriched["summary_structured"] = {
                            "overview": summary.get("overview"),
                            "requirements": summary.get("requirements"),
                            "risks": summary.get("risks"),
                            "sla": summary.get("sla"),
                            "recommended_org": summary.get("recommended_org"),
                        }
                        enriched["recommended_org"] = summary.get("recommended_org")
                        enriched["cases"] = cases
                        enriched["assignment"] = assignment
                        enriched["notifications"] = notifications
                except Exception:
                    pass
                details.append(enriched)
        self._last_batch = ingested
        self._last_batch_details = details
        return ingested

    def get_state(self) -> dict:
        remaining = max(0, self._total - self._cursor)
        return {
            "total": self._total,
            "processed": self._cursor,
            "remaining": remaining,
            "last_ingested": self._last_batch,
            "last_ingested_details": self._last_batch_details,
            "dataset_path": str(self._dataset_path),
        }


simulator = TestDatasetSimulator(repository=repository)
