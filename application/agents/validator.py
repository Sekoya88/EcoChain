"""EcoChain AI — Validator Agent (AGNO).

Agent AGNO pour la validation des données logistiques.
Combine 5 règles business déterministes + validation
sémantique LLM via Gemini.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime
from typing import Any

from dotenv import load_dotenv

load_dotenv()

from agno.agent import Agent
from agno.models.google import Gemini
from pydantic import BaseModel

from domain.constants import (
    MAX_DISTANCE_BY_MODE,
    MAX_WEIGHT_BY_MODE,
    SUPPORTED_CURRENCIES,
)
from domain.models import (
    ShipmentEntity,
    ValidationIssue,
    ValidationResult,
    ValidationSeverity,
)
from infrastructure.logging.event_logger import (
    AgentEvent,
    EventLogger,
    EventType,
    get_event_logger,
)

logger = logging.getLogger(__name__)

VALIDATION_INSTRUCTIONS = [
    "You are a logistics data quality auditor.",
    "Analyze the shipment data for semantic coherence and plausibility.",
    "Check whether the origin, destination, transport mode, weight, and distance make sense together.",
    "Return a JSON object with: is_coherent (bool) and issues (list of strings describing problems).",
    "For example: air transport for 50000kg is implausible, or Rotterdam to Shanghai by road is impossible.",
    "Be strict but fair. Only flag genuinely implausible combinations.",
]


class SemanticValidationOutput(BaseModel):
    """Output du LLM pour la validation sémantique."""
    is_coherent: bool
    issues: list[str]


def create_validator_agent() -> Agent:
    """Crée l'agent AGNO de validation sémantique.

    Returns:
        Agent AGNO configuré pour la validation.
    """
    return Agent(
        name="Validator",
        model=Gemini(id="gemini-2.5-flash"),
        instructions=VALIDATION_INSTRUCTIONS,
        structured_outputs=True,
        markdown=False,
    )


def _check_weight(shipment: ShipmentEntity) -> list[ValidationIssue]:
    """Vérifie la plausibilité du poids par mode de transport."""
    issues: list[ValidationIssue] = []
    max_weight = MAX_WEIGHT_BY_MODE.get(shipment.transport_mode)
    if max_weight and shipment.weight_kg > max_weight:
        issues.append(ValidationIssue(
            field="weight_kg",
            severity=ValidationSeverity.ERROR,
            message=f"Poids {shipment.weight_kg}kg depasse le max {max_weight}kg pour {shipment.transport_mode.value}",
            suggestion=f"Verifier le poids ou changer de mode de transport",
        ))
    if shipment.weight_kg < 1.0:
        issues.append(ValidationIssue(
            field="weight_kg",
            severity=ValidationSeverity.WARNING,
            message=f"Poids tres faible: {shipment.weight_kg}kg",
            suggestion="Verifier que le poids est en kg et non en tonnes",
        ))
    return issues


def _check_distance(shipment: ShipmentEntity) -> list[ValidationIssue]:
    """Vérifie la plausibilité de la distance par mode."""
    issues: list[ValidationIssue] = []
    max_dist = MAX_DISTANCE_BY_MODE.get(shipment.transport_mode)
    if max_dist and shipment.distance_km > max_dist:
        issues.append(ValidationIssue(
            field="distance_km",
            severity=ValidationSeverity.ERROR,
            message=f"Distance {shipment.distance_km}km depasse le max {max_dist}km pour {shipment.transport_mode.value}",
            suggestion="Verifier la distance ou le mode de transport",
        ))
    return issues


def _check_dates(shipment: ShipmentEntity) -> list[ValidationIssue]:
    """Vérifie la cohérence des dates."""
    issues: list[ValidationIssue] = []
    try:
        dep = datetime.strptime(shipment.departure_date, "%Y-%m-%d")
        arr = datetime.strptime(shipment.arrival_date, "%Y-%m-%d")
        delta_days = (arr - dep).days
        if delta_days > 90:
            issues.append(ValidationIssue(
                field="dates",
                severity=ValidationSeverity.WARNING,
                message=f"Duree de transport anormalement longue: {delta_days} jours",
                suggestion="Verifier les dates de depart et d'arrivee",
            ))
    except ValueError:
        issues.append(ValidationIssue(
            field="dates",
            severity=ValidationSeverity.ERROR,
            message="Format de date invalide",
            suggestion="Utiliser le format YYYY-MM-DD",
        ))
    return issues


def _check_currency(shipment: ShipmentEntity) -> list[ValidationIssue]:
    """Vérifie la devise."""
    issues: list[ValidationIssue] = []
    if shipment.currency not in SUPPORTED_CURRENCIES:
        issues.append(ValidationIssue(
            field="currency",
            severity=ValidationSeverity.WARNING,
            message=f"Devise non supportee: {shipment.currency}",
            suggestion=f"Devises supportees: {', '.join(SUPPORTED_CURRENCIES)}",
        ))
    return issues


def _check_coherence(shipment: ShipmentEntity) -> list[ValidationIssue]:
    """Vérifie la cohérence mode/distance."""
    issues: list[ValidationIssue] = []
    if shipment.transport_mode == "air" and shipment.distance_km < 200:
        issues.append(ValidationIssue(
            field="transport_mode",
            severity=ValidationSeverity.WARNING,
            message=f"Transport aerien pour seulement {shipment.distance_km}km semble inefficace",
            suggestion="Envisager le transport routier ou ferroviaire",
        ))
    if shipment.transport_mode == "maritime" and shipment.distance_km < 100:
        issues.append(ValidationIssue(
            field="transport_mode",
            severity=ValidationSeverity.WARNING,
            message=f"Transport maritime pour {shipment.distance_km}km est inhabituel",
            suggestion="Verifier le mode de transport",
        ))
    return issues


async def validate_shipment(
    shipment: ShipmentEntity,
    use_llm: bool = True,
    event_logger: EventLogger | None = None,
) -> ValidationResult:
    """Valide un ShipmentEntity avec règles déterministes + LLM.

    Args:
        shipment: Entité à valider.
        use_llm: Active la validation sémantique LLM.
        event_logger: Logger d'événements optionnel.

    Returns:
        ValidationResult avec score de confiance.
    """
    _logger = event_logger or get_event_logger()
    start = time.perf_counter()

    await _logger.emit(AgentEvent(
        event_type=EventType.AGENT_START,
        agent_name="Validator",
        message=f"Starting validation for {shipment.origin} -> {shipment.destination}",
    ))

    # Règles déterministes
    all_issues: list[ValidationIssue] = []
    rules = [
        ("weight", _check_weight),
        ("distance", _check_distance),
        ("dates", _check_dates),
        ("currency", _check_currency),
        ("coherence", _check_coherence),
    ]

    for rule_name, check_fn in rules:
        issues = check_fn(shipment)
        all_issues.extend(issues)
        if issues:
            await _logger.emit(AgentEvent(
                event_type=EventType.VALIDATION,
                agent_name="Validator",
                message=f"Rule '{rule_name}': {len(issues)} issue(s) found",
                data={"rule": rule_name, "issues": [i.message for i in issues]},
            ))

    # Validation sémantique LLM
    if use_llm:
        try:
            await _logger.emit(AgentEvent(
                event_type=EventType.LLM_CALL,
                agent_name="Validator",
                message="Calling Gemini for semantic validation",
                data={"model": "gemini-2.5-flash"},
            ))

            agent = create_validator_agent()
            prompt = (
                f"Validate this shipment:\n"
                f"Origin: {shipment.origin}\n"
                f"Destination: {shipment.destination}\n"
                f"Mode: {shipment.transport_mode.value}\n"
                f"Weight: {shipment.weight_kg}kg\n"
                f"Distance: {shipment.distance_km}km\n"
                f"Goods: {shipment.goods_description}"
            )

            result = await agent.arun(prompt, output_schema=SemanticValidationOutput)

            if isinstance(result.content, SemanticValidationOutput):
                if not result.content.is_coherent:
                    for issue_msg in result.content.issues:
                        all_issues.append(ValidationIssue(
                            field="semantic",
                            severity=ValidationSeverity.WARNING,
                            message=f"LLM: {issue_msg}",
                            suggestion="Review the shipment data",
                        ))

                await _logger.emit(AgentEvent(
                    event_type=EventType.LLM_RESPONSE,
                    agent_name="Validator",
                    message=f"Semantic validation: coherent={result.content.is_coherent}",
                    data={"coherent": result.content.is_coherent, "llm_issues": len(result.content.issues)},
                ))

        except Exception as e:
            logger.warning("LLM semantic validation failed: %s", str(e))
            await _logger.emit(AgentEvent(
                event_type=EventType.INFO,
                agent_name="Validator",
                message=f"LLM semantic validation skipped: {str(e)[:80]}",
            ))

    # Score de confiance
    error_count = sum(1 for i in all_issues if i.severity == ValidationSeverity.ERROR)
    warning_count = sum(1 for i in all_issues if i.severity == ValidationSeverity.WARNING)
    confidence = max(0.0, 100.0 - (error_count * 30.0) - (warning_count * 10.0))
    is_valid = error_count == 0

    elapsed = (time.perf_counter() - start) * 1000

    await _logger.emit(AgentEvent(
        event_type=EventType.AGENT_COMPLETE,
        agent_name="Validator",
        message=f"Validation complete: valid={is_valid}, confidence={confidence:.0f}%, {len(all_issues)} issues",
        duration_ms=elapsed,
        data={"valid": is_valid, "confidence": confidence, "errors": error_count, "warnings": warning_count},
    ))

    return ValidationResult(
        is_valid=is_valid,
        confidence_score=confidence,
        issues=all_issues,
    )
