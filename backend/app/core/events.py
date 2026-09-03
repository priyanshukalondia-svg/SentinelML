"""
A very small in-process pub/sub hub used to push real-time events
(alerts, health changes, recovery workflow progress) out over WebSocket
to the dashboard (SYSTEM_REQUIREMENTS.md Section 44a).

Kept intentionally simple: a single process, in-memory list of connected
clients. This is sufficient for a local/portfolio deployment; a real
multi-worker deployment would replace this with Redis pub/sub.
"""
from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from typing import Any, Dict, List

from fastapi import WebSocket


class EventBus:
    def __init__(self) -> None:
        self._connections: List[WebSocket] = []
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._connections.append(websocket)

    async def disconnect(self, websocket: WebSocket) -> None:
        async with self._lock:
            if websocket in self._connections:
                self._connections.remove(websocket)

    async def broadcast(self, event_type: str, payload: Dict[str, Any]) -> None:
        message = json.dumps(
            {
                "type": event_type,
                "payload": payload,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            default=str,
        )
        dead: List[WebSocket] = []
        async with self._lock:
            connections = list(self._connections)
        for ws in connections:
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)
        if dead:
            async with self._lock:
                for ws in dead:
                    if ws in self._connections:
                        self._connections.remove(ws)

    def broadcast_sync(self, event_type: str, payload: Dict[str, Any]) -> None:
        """Fire-and-forget helper for use from sync/background-task code paths."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.ensure_future(self.broadcast(event_type, payload))
            else:
                loop.run_until_complete(self.broadcast(event_type, payload))
        except RuntimeError:
            # No event loop in this thread (e.g. background thread) - safe to skip.
            pass


event_bus = EventBus()
