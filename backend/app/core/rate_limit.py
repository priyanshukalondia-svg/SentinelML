"""
Minimal in-memory sliding-window rate limiter (Section 38a).

For a portfolio/local deployment a full Redis-backed limiter (slowapi,
etc.) is unnecessary; this protects the /predict and /simulation
endpoints from accidental runaway loops during a demo.
"""
from __future__ import annotations

import time
from collections import defaultdict, deque
from typing import Deque, Dict

from fastapi import HTTPException, Request, status


class RateLimiter:
    def __init__(self) -> None:
        self._hits: Dict[str, Deque[float]] = defaultdict(deque)

    def check(self, key: str, limit_per_minute: int) -> None:
        now = time.time()
        window = self._hits[key]
        while window and now - window[0] > 60:
            window.popleft()
        if len(window) >= limit_per_minute:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "RATE_LIMIT_EXCEEDED",
                    "message": f"Limit of {limit_per_minute} requests/minute exceeded for '{key}'.",
                },
            )
        window.append(now)


rate_limiter = RateLimiter()


def client_key(request: Request) -> str:
    return request.client.host if request.client else "unknown"
