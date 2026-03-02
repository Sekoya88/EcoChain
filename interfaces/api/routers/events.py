"""EcoChain AI — SSE Events Router.

Endpoint Server-Sent Events pour streamer
les logs des agents en temps réel vers le frontend.
"""

from __future__ import annotations

import asyncio
import json
import logging

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from infrastructure.logging.event_logger import get_event_logger

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/events", tags=["events"])


@router.get(
    "/stream",
    summary="Stream des evenements agents en temps reel",
    description="Endpoint SSE pour recevoir les logs des agents au format Server-Sent Events.",
)
async def event_stream() -> StreamingResponse:
    """Stream SSE des événements pipeline.

    Returns:
        StreamingResponse au format text/event-stream.
    """
    event_logger = get_event_logger()
    queue = event_logger.subscribe()

    async def generate():
        """Générateur async pour le stream SSE."""
        try:
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=30.0)
                    data = json.dumps(event.to_dict(), ensure_ascii=False)
                    yield f"data: {data}\n\n"
                except asyncio.TimeoutError:
                    # Heartbeat pour garder la connexion active
                    yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            event_logger.unsubscribe(queue)

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get(
    "/history",
    summary="Historique des evenements recents",
    description="Retourne les derniers evenements du pipeline.",
)
async def event_history() -> dict:
    """Retourne l'historique des événements.

    Returns:
        Dictionnaire avec les événements récents.
    """
    event_logger = get_event_logger()
    return {"events": event_logger.get_history()}
