"""EcoChain AI — Process Document Use Case.

Orchestre le pipeline complet via OrchestratorAgent.
"""

from __future__ import annotations

import logging
from typing import Any

from application.agents.orchestrator import OrchestratorAgent
from domain.models import CarbonReport, LogisticsDocument, ProcessingError

logger = logging.getLogger(__name__)


class ProcessDocumentError(Exception):
    """Erreur lors du traitement d'un document.

    Attributes:
        error: Erreur structuree.
    """

    def __init__(self, error: ProcessingError) -> None:
        """Init.

        Args:
            error: Erreur structuree.
        """
        super().__init__(error.message)
        self.error = error


class ProcessDocumentUseCase:
    """Use case principal pour le traitement de documents.

    Attributes:
        orchestrator: Agent orchestrateur.
    """

    def __init__(self, orchestrator: OrchestratorAgent) -> None:
        """Init.

        Args:
            orchestrator: Agent orchestrateur configure.
        """
        self.orchestrator = orchestrator

    async def execute(self, document: LogisticsDocument) -> CarbonReport:
        """Traite un document logistique.

        Args:
            document: Document a traiter.

        Returns:
            CarbonReport complet.

        Raises:
            ProcessDocumentError: En cas d'erreur de traitement.
        """
        try:
            return await self.orchestrator.process_document(document)
        except Exception as e:
            logger.error("Pipeline failed: %s", str(e))
            raise ProcessDocumentError(
                ProcessingError(
                    error_code="PIPELINE_ERROR",
                    message=f"Pipeline processing failed: {str(e)}",
                    details=type(e).__name__,
                )
            ) from e

    async def execute_batch(
        self, documents: list[LogisticsDocument]
    ) -> list[CarbonReport]:
        """Traite un lot de documents.

        Args:
            documents: Liste de documents.

        Returns:
            Liste de CarbonReport.
        """
        return await self.orchestrator.process_batch(documents)
