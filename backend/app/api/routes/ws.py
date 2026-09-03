from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.events import event_bus

router = APIRouter(tags=["realtime"])


@router.websocket("/api/v1/ws/events")
async def websocket_events(websocket: WebSocket):
    await event_bus.connect(websocket)
    try:
        while True:
            # We don't expect inbound messages, but reading keeps the
            # connection alive and lets us detect disconnects promptly.
            await websocket.receive_text()
    except WebSocketDisconnect:
        await event_bus.disconnect(websocket)
    except Exception:
        await event_bus.disconnect(websocket)
