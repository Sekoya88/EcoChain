"""EcoChain AI — Document Processing API Router.

Routes :
- POST /api/v1/documents/process — Traite un document individuel
- GET  /api/v1/documents/{document_id}/results — Récupère les résultats
- POST /api/v1/documents/batch — Traitement parallèle de N documents
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from domain.models import (
    CarbonReport,
    DocumentType,
    LogisticsDocument,
    ProcessingError,
)
from application.use_cases.process_document import (
    ProcessDocumentError,
    ProcessDocumentUseCase,
)
from interfaces.api.dependencies import get_use_case

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])

# Store en mémoire pour les résultats (POC — en production, utiliser une DB)
_results_store: dict[str, CarbonReport] = {}


class DocumentProcessRequest(BaseModel):
    """Requête de traitement d'un document.

    Attributes:
        document_type: Type de document logistique.
        raw_content: Contenu brut JSON simulant l'OCR.
        source_filename: Nom du fichier source.
    """

    document_type: DocumentType = Field(
        default=DocumentType.INVOICE,
        description="Type de document",
    )
    raw_content: dict[str, Any] = Field(
        description="Contenu brut JSON du document",
    )
    source_filename: str = Field(
        default="uploaded_document.json",
        description="Nom du fichier source",
    )


class BatchProcessRequest(BaseModel):
    """Requête de traitement batch.

    Attributes:
        documents: Liste de documents à traiter en parallèle.
    """

    documents: list[DocumentProcessRequest] = Field(
        min_length=1,
        max_length=50,
        description="Documents à traiter (1-50)",
    )


class ProcessResponse(BaseModel):
    """Réponse de traitement avec le rapport carbone.

    Attributes:
        success: Indique si le traitement a réussi.
        report: Rapport carbone complet.
        error: Erreur éventuelle.
    """

    success: bool = Field(description="Traitement réussi")
    report: CarbonReport | None = Field(default=None, description="Rapport carbone")
    error: ProcessingError | None = Field(default=None, description="Erreur éventuelle")


class BatchProcessResponse(BaseModel):
    """Réponse de traitement batch.

    Attributes:
        success: Indique si le batch a été traité.
        total_documents: Nombre total de documents.
        successful: Nombre de documents traités avec succès.
        reports: Liste des rapports.
        total_co2_kg: Total CO2 du batch.
    """

    success: bool = Field(description="Batch traité")
    total_documents: int = Field(description="Nombre total")
    successful: int = Field(description="Nombre de succès")
    reports: list[CarbonReport] = Field(description="Rapports individuels")
    total_co2_kg: float = Field(description="Total CO2 kgCO2e")


@router.post(
    "/process",
    response_model=ProcessResponse,
    status_code=status.HTTP_200_OK,
    summary="Traite un document logistique",
    description="Ingère un document JSON, extrait les données, calcule le CO2 et génère des recommandations.",
)
async def process_document(
    request: DocumentProcessRequest,
    use_case: ProcessDocumentUseCase = Depends(get_use_case),
) -> ProcessResponse:
    """Traite un document logistique individuel.

    Args:
        request: Document à traiter.
        use_case: UseCase injecté.

    Returns:
        ProcessResponse avec le CarbonReport ou l'erreur.

    Raises:
        HTTPException: En cas d'erreur serveur interne.
    """
    document = LogisticsDocument(
        document_type=request.document_type,
        raw_content=request.raw_content,
        source_filename=request.source_filename,
    )

    try:
        report = await use_case.execute(document)

        # Stocker le résultat pour récupération ultérieure
        _results_store[document.document_id] = report

        logger.info(
            "Document %s traité — CO2: %.1f kgCO2e",
            document.document_id,
            report.total_co2_kg,
        )

        return ProcessResponse(success=True, report=report)

    except ProcessDocumentError as e:
        logger.error("Erreur de traitement: %s", e.error.message)
        return ProcessResponse(success=False, error=e.error)

    except Exception as e:
        logger.error("Erreur inattendue: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur interne: {str(e)}",
        ) from e


@router.get(
    "/{document_id}/results",
    response_model=ProcessResponse,
    summary="Récupère les résultats d'un document traité",
    description="Retourne le CarbonReport d'un document précédemment traité.",
)
async def get_results(document_id: str) -> ProcessResponse:
    """Récupère les résultats d'un document traité.

    Args:
        document_id: ID du document.

    Returns:
        ProcessResponse avec le CarbonReport.

    Raises:
        HTTPException: Si le document n'est pas trouvé.
    """
    report = _results_store.get(document_id)
    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} non trouvé. Traitez-le d'abord via POST /process.",
        )

    return ProcessResponse(success=True, report=report)


@router.post(
    "/batch",
    response_model=BatchProcessResponse,
    status_code=status.HTTP_200_OK,
    summary="Traitement parallèle de plusieurs documents",
    description="Traite N documents en parallèle via asyncio.gather.",
)
async def process_batch(
    request: BatchProcessRequest,
    use_case: ProcessDocumentUseCase = Depends(get_use_case),
) -> BatchProcessResponse:
    """Traite un lot de documents en parallèle.

    Args:
        request: Lot de documents à traiter.
        use_case: UseCase injecté.

    Returns:
        BatchProcessResponse avec tous les rapports.
    """
    documents = [
        LogisticsDocument(
            document_type=doc.document_type,
            raw_content=doc.raw_content,
            source_filename=doc.source_filename,
        )
        for doc in request.documents
    ]

    try:
        reports = await use_case.execute_batch(documents)

        # Stocker les résultats
        for doc, report in zip(documents, reports, strict=False):
            _results_store[doc.document_id] = report

        successful = sum(1 for r in reports if r.total_co2_kg > 0)
        total_co2 = sum(r.total_co2_kg for r in reports)

        logger.info(
            "Batch de %d documents traité — %d succès, Total CO2: %.1f kgCO2e",
            len(documents),
            successful,
            total_co2,
        )

        return BatchProcessResponse(
            success=True,
            total_documents=len(documents),
            successful=successful,
            reports=reports,
            total_co2_kg=round(total_co2, 2),
        )

    except Exception as e:
        logger.error("Erreur batch: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur batch: {str(e)}",
        ) from e
