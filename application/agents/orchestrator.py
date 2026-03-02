"""EcoChain AI — Orchestrator (Pipeline Coordinator).

Orchestre le pipeline complet :
Extraction -> Validation -> Calcul CO2 -> Recommandations.
Utilise les agents AGNO individuellement avec coordination manuelle
pour conserver le controle du flux et le logging granulaire.
pour conserver le contrôle du flux et le logging granulaire.
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

from application.agents.extractor import extract_shipment
from application.agents.validator import validate_shipment
from application.agents.recommender import generate_recommendations
from application.calculators.carbon_calculator import CarbonCalculator
from domain.models import (
    CarbonReport,
    LogisticsDocument,
    ValidationResult,
    ProcessingError,
    ShipmentEntity,
)
from infrastructure.logging.event_logger import (
    AgentEvent,
    EventLogger,
    EventType,
    get_event_logger,
)

logger = logging.getLogger(__name__)


class OrchestratorAgent:
    """Orchestrateur du pipeline multi-agents.

    Coordonne séquentiellement les agents AGNO (Extractor, Validator,
    Recommender) et le calculateur CO2 déterministe.

    Attributes:
        calculator: Calculateur CO2 déterministe.
        event_logger: Logger d'événements temps réel.
    """

    def __init__(self, event_logger: EventLogger | None = None) -> None:
        """Initialise l'orchestrateur.

        Args:
            event_logger: Logger d'événements optionnel.
        """
        self.calculator = CarbonCalculator()
        self.event_logger = event_logger or get_event_logger()

    async def process_document(
        self,
        document: LogisticsDocument,
    ) -> CarbonReport:
        """Traite un document logistique complet.

        Pipeline : Extraction -> Validation -> CO2 -> Recommandations.

        Args:
            document: Document logistique brut.

        Returns:
            CarbonReport complet.

        Raises:
            Exception: Si le pipeline échoue.
        """
        start = time.perf_counter()

        await self.event_logger.emit(AgentEvent(
            event_type=EventType.PIPELINE_START,
            agent_name="Orchestrator",
            message=f"Starting pipeline for {document.source_filename}",
            data={"document_id": document.document_id, "type": document.document_type.value},
        ))

        # Step 1: Extraction
        shipment = await extract_shipment(
            document.raw_content,
            event_logger=self.event_logger,
        )

        # Step 2: Validation
        validation = await validate_shipment(
            shipment,
            use_llm=True,
            event_logger=self.event_logger,
        )

        # Step 3: CO2 Calculation
        await self.event_logger.emit(AgentEvent(
            event_type=EventType.CALCULATION,
            agent_name="CarbonCalculator",
            message=f"Calculating emissions: {shipment.weight_tonnes:.1f}t x {shipment.distance_km}km ({shipment.transport_mode.value})",
        ))

        emission = self.calculator.calculate_emission_from_shipment(shipment)
        comparisons = self.calculator.compare_transport_modes(
            weight_tonnes=shipment.weight_tonnes,
            distance_km=shipment.distance_km,
            current_mode=shipment.transport_mode,
        )
        benchmark = self.calculator.benchmark_vs_sector(emission.co2_kg)

        await self.event_logger.emit(AgentEvent(
            event_type=EventType.CALCULATION,
            agent_name="CarbonCalculator",
            message=f"Emission: {emission.co2_kg:.1f} kgCO2e | Factor: {emission.emission_factor}",
            data={
                "co2_kg": emission.co2_kg,
                "factor": emission.emission_factor,
                "benchmark_ratio": benchmark["ratio_vs_benchmark_pct"],
            },
        ))

        # Step 4: Recommendations
        recommendations = await generate_recommendations(
            shipment,
            emission,
            event_logger=self.event_logger,
        )

        elapsed = (time.perf_counter() - start) * 1000

        report = CarbonReport(
            document_id=document.document_id,
            shipments=[shipment],
            emissions=[emission],
            total_co2_kg=round(emission.co2_kg, 2),
            mode_comparisons=comparisons,
            recommendations=recommendations,
            validation=validation,
            processing_time_ms=round(elapsed, 1),
        )

        await self.event_logger.emit(AgentEvent(
            event_type=EventType.PIPELINE_COMPLETE,
            agent_name="Orchestrator",
            message=f"Pipeline complete: {emission.co2_kg:.1f} kgCO2e in {elapsed:.0f}ms",
            duration_ms=elapsed,
            data={
                "total_co2_kg": report.total_co2_kg,
                "recommendations": len(recommendations),
                "validation_score": validation.confidence_score,
            },
        ))

        return report

    async def process_batch(
        self,
        documents: list[LogisticsDocument],
    ) -> list[CarbonReport]:
        """Traite un lot de documents en parallèle.

        Args:
            documents: Liste de documents logistiques.

        Returns:
            Liste de CarbonReport.
        """
        await self.event_logger.emit(AgentEvent(
            event_type=EventType.PIPELINE_START,
            agent_name="Orchestrator",
            message=f"Starting batch processing: {len(documents)} documents",
            data={"batch_size": len(documents)},
        ))

        start = time.perf_counter()

        tasks = [self.process_document(doc) for doc in documents]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        reports: list[CarbonReport] = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error("Document %d failed: %s", i, str(result))
                await self.event_logger.emit(AgentEvent(
                    event_type=EventType.ERROR,
                    agent_name="Orchestrator",
                    message=f"Document {i} failed: {str(result)[:100]}",
                ))
                # Rapport vide pour les erreurs
                reports.append(CarbonReport(
                    document_id=documents[i].document_id,
                    shipments=[],
                    emissions=[],
                    total_co2_kg=0.0,
                    mode_comparisons=[],
                    recommendations=[],
                    validation=ValidationResult(is_valid=False, confidence_score=0.0),
                    processing_time_ms=0.0,
                ))
            else:
                reports.append(result)

        elapsed = (time.perf_counter() - start) * 1000

        await self.event_logger.emit(AgentEvent(
            event_type=EventType.PIPELINE_COMPLETE,
            agent_name="Orchestrator",
            message=f"Batch complete: {len(reports)} reports in {elapsed:.0f}ms",
            duration_ms=elapsed,
        ))

        return reports
