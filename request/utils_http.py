from __future__ import annotations

import asyncio
import random
from typing import Dict, Any, Optional

import httpx

from request.logger_setup import logger


TRANSIENT_STATUS_CODES = {429, 500, 502, 503, 504}


async def post_json_with_retries(
    client: httpx.AsyncClient,
    url: str,
    json: Dict[str, Any],
    headers: Optional[Dict[str, str]] = None,
    max_retries: int = 2,
    backoff_base: float = 0.8,
) -> httpx.Response:
    attempt = 0
    headers = headers or {"content-type": "application/json"}

    while True:
        try:
            response = await client.post(url, json=json, headers=headers)
            if response.status_code in TRANSIENT_STATUS_CODES and attempt < max_retries:
                delay = backoff_base * (2 ** attempt) + random.uniform(0, 0.2)
                logger.info(
                    "Transient response %s, retrying in %.2fs (attempt %s/%s)",
                    response.status_code,
                    delay,
                    attempt + 1,
                    max_retries,
                )
                await asyncio.sleep(delay)
                attempt += 1
                continue
            return response
        except (httpx.TimeoutException, httpx.TransportError, httpx.RequestError) as exc:
            if attempt >= max_retries:
                raise
            delay = backoff_base * (2 ** attempt) + random.uniform(0, 0.2)
            logger.info(
                "HTTP error %s, retrying in %.2fs (attempt %s/%s)",
                type(exc).__name__,
                delay,
                attempt + 1,
                max_retries,
            )
            await asyncio.sleep(delay)
            attempt += 1



