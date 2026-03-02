"""EcoChain AI — FastAPI Dependencies.

Injection de dependances pour les composants partages :
OrchestratorAgent (singleton), EventLogger, ProcessDocumentUseCase.
"""

from __future__ import annotations

import logging

from application.agents.orchestrator import OrchestratorAgent
from application.use_cases.process_document import ProcessDocumentUseCase
from infrastructure.logging.event_logger import EventLogger, get_event_logger

logger = logging.getLogger(__name__)

_orchestrator: OrchestratorAgent | None = None
_use_case: ProcessDocumentUseCase | None = None


def get_orchestrator() -> OrchestratorAgent:
    """Retourne l'OrchestratorAgent singleton.

    Returns:
        Instance unique de OrchestratorAgent.
    """
    global _orchestrator
    if _orchestrator is None:
        event_logger = get_event_logger()
        _orchestrator = OrchestratorAgent(event_logger=event_logger)
        logger.info("OrchestratorAgent initialise (AGNO agents)")
    return _orchestrator


def get_use_case() -> ProcessDocumentUseCase:
    """Retourne le ProcessDocumentUseCase singleton.

    Returns:
        Instance unique de ProcessDocumentUseCase.
    """
    global _use_case
    if _use_case is None:
        orchestrator = get_orchestrator()
        _use_case = ProcessDocumentUseCase(orchestrator)
        logger.info("ProcessDocumentUseCase initialise")
    return _use_case


def reset_dependencies() -> None:
    """Reinitialise toutes les dependances (pour les tests)."""
    global _orchestrator, _use_case
    _orchestrator = None
    _use_case = None
    logger.info("Dependances reinitialisees")
