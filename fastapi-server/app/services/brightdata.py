"""Bright Data scraping service for Amazon product discovery."""

from __future__ import annotations

import asyncio
import json
import os
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Mapping, Optional

import requests

from app.models.schemas import (
    BrightDataDetectionPayload,
    BrightDataProduct,
    BrightDataScrapeRequest,
    BrightDataScrapeResponse,
)

_DEFAULT_BASE_URL = "https://api.brightdata.com/datasets/v3/scrape"


class BrightDataError(RuntimeError):
    """Raised when the Bright Data API responds with a non-success payload."""


@dataclass(frozen=True)
class BrightDataConfig:
    api_key: str
    dataset_id: str
    include_errors: bool = True
    notify: bool = False
    base_url: str = _DEFAULT_BASE_URL
    scrape_type: str = "discover_new"
    discover_by: str = "keyword"

    @staticmethod
    def from_env() -> Optional["BrightDataConfig"]:
        api_key = os.getenv("BRIGHTDATA_API_KEY")
        dataset_id = os.getenv("BRIGHTDATA_DATASET_ID")
        if not api_key or not dataset_id:
            return None
        return BrightDataConfig(api_key=api_key, dataset_id=dataset_id)


class BrightDataAmazonScraper:
    """Tiny client adapter around Bright Data's Amazon keyword discovery."""

    def __init__(self, config: BrightDataConfig) -> None:
        self._config = config
        self._session = requests.Session()
        self._session.headers.update(
            {
                "Authorization": f"Bearer {config.api_key}",
                "Content-Type": "application/json",
            }
        )

    async def discover_products(self, request: BrightDataScrapeRequest) -> BrightDataScrapeResponse:
        payload = self._build_request_payload(request)

        response_data = await asyncio.to_thread(self._post, payload)
        normalized_results = self._normalize_results(response_data)

        return BrightDataScrapeResponse(
            results=normalized_results,
            raw_response=response_data,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _post(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        params = {
            "dataset_id": self._config.dataset_id,
            "notify": str(self._config.notify).lower(),
            "include_errors": str(self._config.include_errors).lower(),
            "type": self._config.scrape_type,
            "discover_by": self._config.discover_by,
        }

        response = self._session.post(self._config.base_url, params=params, json=payload, timeout=60)
        if response.status_code >= 400:
            raise BrightDataError(
                f"Bright Data request failed: {response.status_code} {response.text[:200]}"
            )

        try:
            return response.json()
        except ValueError:
            ndjson_payload = BrightDataAmazonScraper._try_parse_ndjson(response.text)
            if ndjson_payload is not None:
                return {"results": ndjson_payload}
            return {"raw": response.text}

    @staticmethod
    def _build_request_payload(request: BrightDataScrapeRequest) -> Dict[str, Any]:
        entries: List[Dict[str, str]] = []
        for detection in request.input:
            entries.append({"keyword": BrightDataAmazonScraper._detection_to_keyword(detection)})

        payload: Dict[str, Any] = {"input": entries}
        if request.max_records_per_input is not None:
            payload["limit"] = request.max_records_per_input
        return payload

    @staticmethod
    def _detection_to_keyword(detection: BrightDataDetectionPayload) -> str:
        label = detection.label.strip()
        if detection.is_low and detection.percent_full <= 50:
            return label
        # If the item is not low, append a qualifier so that results still make sense
        return f"{label} restock"

    @staticmethod
    def _normalize_results(response_data: Dict[str, Any]) -> List[BrightDataProduct]:
        results_payload: Iterable[Any] = []
        if isinstance(response_data, dict):
            if isinstance(response_data.get("results"), list):
                results_payload = response_data["results"]
            elif isinstance(response_data.get("data"), list):
                results_payload = response_data["data"]
        elif isinstance(response_data, list):
            results_payload = response_data

        normalized: List[BrightDataProduct] = []
        for item in results_payload:
            product_data = BrightDataAmazonScraper._ensure_mapping(item)
            if product_data is None:
                continue
            normalized.append(BrightDataAmazonScraper._parse_product(product_data))
        return normalized

    @staticmethod
    def _ensure_mapping(item: Any) -> Optional[Dict[str, Any]]:
        if isinstance(item, Mapping):
            return dict(item)
        return None

    @staticmethod
    def _parse_product(item: Dict[str, Any]) -> BrightDataProduct:
        asin = item.get("asin") or item.get("id")
        if not lines:
            return None

        parsed: List[Dict[str, Any]] = []
        for line in lines:
            try:
                parsed_line = json.loads(line)
            except json.JSONDecodeError:
                return None
            if not isinstance(parsed_line, dict):
                return None
            parsed.append(parsed_line)
        return parsed

    @staticmethod
    def _parse_product(item: Dict[str, Any]) -> BrightDataProduct:
        asin = item.get("asin") or item.get("id")
        product = BrightDataProduct(
            asin=asin,
            title=item.get("title"),
            url=item.get("url") or item.get("product_url"),
            price=item.get("price"),
            image=item.get("image") or item.get("main_image"),
            metadata={
                key: value
                for key, value in item.items()
                if key
                not in {
                    "asin",
                    "id",
                    "title",
                    "url",
                    "product_url",
                    "price",
                    "image",
                    "main_image",
                }
            },
        )
        return product


def configure_brightdata_scraper() -> Optional[BrightDataAmazonScraper]:
    config = BrightDataConfig.from_env()
    if not config:
        return None
    return BrightDataAmazonScraper(config)