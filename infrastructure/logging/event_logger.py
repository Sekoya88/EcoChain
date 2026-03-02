"""EcoChain AI — Event Logger for Real-Time Agent Monitoring.

Système de logging asynchrone basé sur asyncio.Queue pour diffuser
les événements des agents en temps réel via SSE.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class EventType(str, Enum):
    """Types d'événements du pipeline."""

    PIPELINE_START = "pipeline_start"
    PIPELINE_COMPLETE = "pipeline_complete"
    AGENT_START = "agent_start"
    AGENT_COMPLETE = "agent_complete"
    LLM_CALL = "llm_call"
    LLM_RESPONSE = "llm_response"
    VALIDATION = "validation"
    CALCULATION = "calculation"
    RECOMMENDATION = "recommendation"
    ERROR = "error"
    INFO = "info"


@dataclass
class AgentEvent:
    """Événement émis par un agent.

    Attributes:
        event_type: Type d'événement.
        agent_name: Nom de l'agent émetteur.
        message: Description de l'événement.
        timestamp: Timestamp Unix.
        data: Données additionnelles.
        duration_ms: Durée de l'opération en ms (si applicable).
    """

    event_type: EventType
    agent_name: str
    message: str
    timestamp: float = field(default_factory=time.time)
    data: dict[str, Any] = field(default_factory=dict)
    duration_ms: float | None = None

    def to_dict(self) -> dict[str, Any]:
        """Sérialise l'événement en dictionnaire."""
        return {
            "type": self.event_type.value,
            "agent": self.agent_name,
            "message": self.message,
            "timestamp": self.timestamp,
            "data": self.data,
            "duration_ms": self.duration_ms,
        }


class EventLogger:
    """Logger d'événements asynchrone pour le monitoring temps réel.

    Utilise une asyncio.Queue pour découpler la production et la
    consommation d'événements. Supporte plusieurs consumers SSE simultanés.

    Attributes:
        _subscribers: Liste des queues de souscription SSE.
        _history: Historique borné des derniers événements.
    """

    def __init__(self, max_history: int = 200) -> None:
        """Initialise le logger.

        Args:
            max_history: Nombre max d'événements conservés en mémoire.
        """
        self._subscribers: list[asyncio.Queue[AgentEvent]] = []
        self._history: list[AgentEvent] = []
        self._max_history = max_history

    async def emit(self, event: AgentEvent) -> None:
        """Émet un événement vers tous les souscripteurs.

        Args:
            event: Événement à diffuser.
        """
        self._history.append(event)
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history :]

        dead_subscribers: list[int] = []
        for i, queue in enumerate(self._subscribers):
            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:
                dead_subscribers.append(i)

        for i in reversed(dead_subscribers):
            self._subscribers.pop(i)

    def subscribe(self) -> asyncio.Queue[AgentEvent]:
        """Crée une nouvelle souscription SSE.

        Returns:
            Queue dédiée à ce souscripteur.
        """
        queue: asyncio.Queue[AgentEvent] = asyncio.Queue(maxsize=500)
        self._subscribers.append(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue[AgentEvent]) -> None:
        """Retire une souscription.

        Args:
            queue: Queue à retirer.
        """
        if queue in self._subscribers:
            self._subscribers.remove(queue)

    def get_history(self) -> list[dict[str, Any]]:
        """Retourne l'historique des événements sérialisé.

        Returns:
            Liste de dictionnaires d'événements.
        """
        return [e.to_dict() for e in self._history]

    def clear(self) -> None:
        """Efface l'historique."""
        self._history.clear()


# Singleton global
_event_logger: EventLogger | None = None


def get_event_logger() -> EventLogger:
    """Retourne le singleton EventLogger.

    Returns:
        Instance unique d'EventLogger.
    """
    global _event_logger
    if _event_logger is None:
        _event_logger = EventLogger()
    return _event_logger
