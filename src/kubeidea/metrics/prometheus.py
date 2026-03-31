"""Optional Prometheus query adapter."""

from __future__ import annotations

from typing import Any

import httpx
from pydantic import BaseModel


class PrometheusResult(BaseModel):
    """A single result from a Prometheus instant query."""

    metric: dict[str, str]
    value: tuple[float, str]


class PrometheusAdapter:
    """Simple adapter for querying a Prometheus server via HTTP.

    Args:
        base_url: The Prometheus server URL (e.g. ``http://prometheus:9090``).
    """

    def __init__(self, base_url: str) -> None:
        self._base_url = base_url.rstrip("/")

    def instant_query(self, query: str) -> list[PrometheusResult]:
        """Execute a PromQL instant query.

        Args:
            query: PromQL expression.

        Returns:
            A list of ``PrometheusResult`` objects.
        """
        url = f"{self._base_url}/api/v1/query"
        response = httpx.get(url, params={"query": query}, timeout=10.0)
        response.raise_for_status()
        data: dict[str, Any] = response.json()

        results: list[PrometheusResult] = []
        for item in data.get("data", {}).get("result", []):
            results.append(
                PrometheusResult(
                    metric=item.get("metric", {}),
                    value=tuple(item.get("value", (0.0, "0"))),  # type: ignore[arg-type]
                )
            )
        return results
