"""EcoChain AI — Recommender Agent (AGNO).

Agent AGNO pour la génération de recommandations
de réduction CO2 personnalisées via Gemini 2.5 Flash.
"""

from __future__ import annotations

import logging
import time
from typing import Any

from dotenv import load_dotenv

load_dotenv()

from agno.agent import Agent
from agno.models.google import Gemini
from pydantic import BaseModel

from domain.models import (
    EmissionDetail,
    Recommendation,
    ShipmentEntity,
    TransportMode,
)
from infrastructure.logging.event_logger import (
    AgentEvent,
    EventLogger,
    EventType,
    get_event_logger,
)

logger = logging.getLogger(__name__)

RECOMMENDER_INSTRUCTIONS = [
    "You are a supply chain sustainability expert.",
    "Analyze the shipment and its carbon emissions to generate exactly 3 reduction recommendations.",
    "Each recommendation must have:",
    "- title: concise action title",
    "- description: detailed explanation (2-3 sentences)",
    "- potential_saving_pct: estimated CO2 reduction percentage (realistic, 5-80%)",
    "- priority: 1 (high), 2 (medium), or 3 (low)",
    "- category: one of 'modal_shift', 'consolidation', 'route_optimization', 'load_optimization', 'energy_transition'",
    "Prioritize by impact. Consider: modal shift (road->rail/maritime), consolidation, route optimization, energy alternatives.",
    "Be specific to the shipment context. Do not give generic advice.",
    "Always return exactly 3 recommendations, ordered by priority (1 first).",
]


class RecommendationList(BaseModel):
    """Output structuré pour les recommandations."""
    recommendations: list[Recommendation]


def create_recommender_agent() -> Agent:
    """Crée l'agent AGNO de recommandation.

    Returns:
        Agent AGNO configuré pour les recommandations.
    """
    return Agent(
        name="Recommender",
        model=Gemini(id="gemini-2.5-flash"),
        instructions=RECOMMENDER_INSTRUCTIONS,
        structured_outputs=True,
        markdown=False,
    )


def _deterministic_recommendations(
    shipment: ShipmentEntity,
    emission: EmissionDetail,
) -> list[Recommendation]:
    """Recommandations déterministes de secours.

    Args:
        shipment: Expédition analysée.
        emission: Détail d'émission calculé.

    Returns:
        3 recommandations standards.
    """
    recs: list[Recommendation] = []

    if shipment.transport_mode == TransportMode.ROAD:
        recs.append(Recommendation(
            title="Transfert modal routier vers ferroviaire",
            description=(
                f"Le trajet {shipment.origin}-{shipment.destination} de {shipment.distance_km}km "
                f"peut etre effectue par rail, reduisant les emissions de ~64% par rapport au routier."
            ),
            potential_saving_pct=64.0,
            priority=1,
            category="modal_shift",
        ))
    elif shipment.transport_mode == TransportMode.AIR:
        recs.append(Recommendation(
            title="Transfert modal aerien vers maritime",
            description=(
                f"Le transport aerien genere {emission.co2_kg:.0f}kg CO2. Le maritime reduirait "
                f"les emissions de plus de 98% sur cette route."
            ),
            potential_saving_pct=98.0,
            priority=1,
            category="modal_shift",
        ))
    else:
        recs.append(Recommendation(
            title="Optimisation du taux de remplissage",
            description=(
                f"Augmenter le taux de remplissage du {shipment.transport_mode.value} "
                f"de 70% a 95% peut reduire les emissions par tonne transportee de ~25%."
            ),
            potential_saving_pct=25.0,
            priority=1,
            category="load_optimization",
        ))

    recs.append(Recommendation(
        title="Consolidation des expeditions",
        description=(
            f"Regrouper les expeditions vers {shipment.destination} permet de reduire "
            f"le nombre de trajets et les emissions globales d'environ 20%."
        ),
        potential_saving_pct=20.0,
        priority=2,
        category="consolidation",
    ))

    recs.append(Recommendation(
        title="Transition vers les biocarburants",
        description=(
            f"L'adoption de biocarburants HVO100 pour le transport "
            f"{shipment.transport_mode.value} peut reduire les emissions de ~80%."
        ),
        potential_saving_pct=80.0,
        priority=3,
        category="energy_transition",
    ))

    return recs[:3]


async def generate_recommendations(
    shipment: ShipmentEntity,
    emission: EmissionDetail,
    event_logger: EventLogger | None = None,
) -> list[Recommendation]:
    """Génère 3 recommandations de réduction CO2.

    Tente l'agent AGNO, puis fallback déterministe.

    Args:
        shipment: Expédition analysée.
        emission: Détail d'émission.
        event_logger: Logger optionnel.

    Returns:
        Liste de 3 recommandations.
    """
    _logger = event_logger or get_event_logger()
    start = time.perf_counter()

    await _logger.emit(AgentEvent(
        event_type=EventType.AGENT_START,
        agent_name="Recommender",
        message=f"Generating recommendations for {shipment.origin} -> {shipment.destination}",
    ))

    try:
        agent = create_recommender_agent()

        prompt = (
            f"Analyze this shipment and its carbon footprint:\n"
            f"Route: {shipment.origin} -> {shipment.destination}\n"
            f"Mode: {shipment.transport_mode.value}\n"
            f"Weight: {shipment.weight_kg}kg ({shipment.weight_tonnes:.1f}t)\n"
            f"Distance: {shipment.distance_km}km\n"
            f"Goods: {shipment.goods_description}\n"
            f"CO2 emissions: {emission.co2_kg:.1f}kg CO2e\n"
            f"Emission factor: {emission.emission_factor} kgCO2e/t.km\n\n"
            f"Generate exactly 3 personalized reduction recommendations."
        )

        await _logger.emit(AgentEvent(
            event_type=EventType.LLM_CALL,
            agent_name="Recommender",
            message="Calling Gemini for personalized recommendations",
            data={"model": "gemini-2.5-flash", "co2_kg": emission.co2_kg},
        ))

        result = await agent.arun(prompt, output_schema=RecommendationList)
        elapsed = (time.perf_counter() - start) * 1000

        if isinstance(result.content, RecommendationList):
            recs = result.content.recommendations[:3]
            await _logger.emit(AgentEvent(
                event_type=EventType.AGENT_COMPLETE,
                agent_name="Recommender",
                message=f"Generated {len(recs)} recommendations via LLM",
                duration_ms=elapsed,
                data={
                    "method": "agno_gemini",
                    "categories": [r.category for r in recs],
                },
            ))
            return recs

    except Exception as e:
        elapsed = (time.perf_counter() - start) * 1000
        logger.warning("LLM recommendation failed, using fallback: %s", str(e))
        await _logger.emit(AgentEvent(
            event_type=EventType.INFO,
            agent_name="Recommender",
            message=f"LLM failed, switching to deterministic: {str(e)[:80]}",
            duration_ms=elapsed,
        ))

    # Fallback
    recs = _deterministic_recommendations(shipment, emission)
    elapsed = (time.perf_counter() - start) * 1000
    await _logger.emit(AgentEvent(
        event_type=EventType.AGENT_COMPLETE,
        agent_name="Recommender",
        message=f"Generated {len(recs)} recommendations via deterministic fallback",
        duration_ms=elapsed,
        data={"method": "deterministic"},
    ))
    return recs
