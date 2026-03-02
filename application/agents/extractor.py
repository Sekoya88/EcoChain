"""EcoChain AI — Extractor Agent (AGNO).

Agent AGNO natif pour l'extraction d'entités logistiques
typées depuis des documents OCR JSON non structurés.
Utilise Gemini 2.5 Flash avec structured output.
"""

from __future__ import annotations

import logging
import time
from typing import Any

from dotenv import load_dotenv

load_dotenv()

from agno.agent import Agent
from agno.models.google import Gemini

from domain.models import ShipmentEntity, TransportMode
from infrastructure.logging.event_logger import (
    AgentEvent,
    EventLogger,
    EventType,
    get_event_logger,
)

logger = logging.getLogger(__name__)

EXTRACTION_INSTRUCTIONS = [
    "You are a logistics data extraction specialist.",
    "Your task is to extract structured shipment data from raw OCR JSON documents.",
    "Extract the following fields precisely:",
    "- origin: city or warehouse of departure",
    "- destination: city or warehouse of arrival",
    "- weight_kg: total gross weight in kilograms (numeric)",
    "- distance_km: distance in kilometers (numeric)",
    "- transport_mode: one of 'road', 'maritime', 'air', 'rail', 'river'",
    "- shipper: name of the shipping company",
    "- receiver: name of the receiving company",
    "- departure_date: in YYYY-MM-DD format",
    "- arrival_date: in YYYY-MM-DD format",
    "- goods_description: description of the goods",
    "- currency: ISO 4217 code (default EUR)",
    "If a field is not found, use reasonable defaults based on the document context.",
    "For transport_mode, infer from keywords: 'camion/truck' -> road, 'navire/vessel' -> maritime, etc.",
    "Always return valid JSON matching the expected schema.",
]


def create_extractor_agent() -> Agent:
    """Crée l'agent AGNO d'extraction.

    Returns:
        Agent AGNO configuré pour l'extraction d'entités.
    """
    return Agent(
        name="Extractor",
        model=Gemini(id="gemini-2.5-flash"),
        instructions=EXTRACTION_INSTRUCTIONS,
        structured_outputs=True,
        markdown=False,
    )


def _deterministic_extract(raw_content: dict[str, Any]) -> ShipmentEntity:
    """Extraction déterministe de secours sans LLM.

    Mappage heuristique des champs courants vers ShipmentEntity.

    Args:
        raw_content: Document JSON brut.

    Returns:
        ShipmentEntity extraite par heuristique.
    """
    mode_mapping: dict[str, TransportMode] = {
        "road": TransportMode.ROAD,
        "truck": TransportMode.ROAD,
        "camion": TransportMode.ROAD,
        "routier": TransportMode.ROAD,
        "maritime": TransportMode.MARITIME,
        "sea": TransportMode.MARITIME,
        "navire": TransportMode.MARITIME,
        "vessel": TransportMode.MARITIME,
        "air": TransportMode.AIR,
        "avion": TransportMode.AIR,
        "aérien": TransportMode.AIR,
        "flight": TransportMode.AIR,
        "rail": TransportMode.RAIL,
        "train": TransportMode.RAIL,
        "ferroviaire": TransportMode.RAIL,
        "river": TransportMode.RIVER,
        "fluvial": TransportMode.RIVER,
        "barge": TransportMode.RIVER,
    }

    raw_mode = str(
        raw_content.get(
            "transport_mode",
            raw_content.get("transport_type", "road"),
        )
    ).lower()

    transport_mode = TransportMode.ROAD
    for key, mode in mode_mapping.items():
        if key in raw_mode:
            transport_mode = mode
            break

    return ShipmentEntity(
        origin=str(
            raw_content.get(
                "origin",
                raw_content.get("origin_warehouse", "Unknown"),
            )
        ),
        destination=str(
            raw_content.get(
                "destination",
                raw_content.get("destination_warehouse", "Unknown"),
            )
        ),
        weight_kg=float(
            raw_content.get(
                "total_weight_kg",
                raw_content.get("gross_weight_kg", 1000.0),
            )
        ),
        distance_km=float(
            raw_content.get(
                "distance_km",
                raw_content.get("estimated_distance_km", 500.0),
            )
        ),
        transport_mode=transport_mode,
        shipper=str(
            raw_content.get(
                "shipper_name",
                raw_content.get("shipper", "Unknown Shipper"),
            )
        ),
        receiver=str(
            raw_content.get(
                "receiver_name",
                raw_content.get("consignee", raw_content.get("receiver", "Unknown Receiver")),
            )
        ),
        departure_date=str(
            raw_content.get(
                "departure_date",
                raw_content.get("ship_date", "2024-01-01"),
            )
        ),
        arrival_date=str(
            raw_content.get(
                "arrival_date",
                raw_content.get("expected_delivery", "2024-01-02"),
            )
        ),
        goods_description=str(
            raw_content.get(
                "goods_description",
                raw_content.get("goods", "Marchandises diverses"),
            )
        ),
        currency=str(raw_content.get("currency", "EUR")),
    )


async def extract_shipment(
    raw_content: dict[str, Any],
    event_logger: EventLogger | None = None,
) -> ShipmentEntity:
    """Extrait un ShipmentEntity depuis un document JSON brut.

    Tente d'abord l'extraction via AGNO/Gemini, puis fallback déterministe.

    Args:
        raw_content: Document JSON brut.
        event_logger: Logger d'événements optionnel.

    Returns:
        ShipmentEntity extrait.
    """
    _logger = event_logger or get_event_logger()
    import json

    await _logger.emit(AgentEvent(
        event_type=EventType.AGENT_START,
        agent_name="Extractor",
        message="Starting entity extraction from raw document",
    ))

    start = time.perf_counter()

    try:
        agent = create_extractor_agent()

        prompt = (
            "Extract shipment data from this logistics document:\n\n"
            f"{json.dumps(raw_content, indent=2, ensure_ascii=False)}"
        )

        await _logger.emit(AgentEvent(
            event_type=EventType.LLM_CALL,
            agent_name="Extractor",
            message="Calling Gemini 2.5 Flash for structured extraction",
            data={"model": "gemini-2.5-flash", "input_keys": list(raw_content.keys())},
        ))

        result = await agent.arun(prompt, output_schema=ShipmentEntity)
        elapsed = (time.perf_counter() - start) * 1000

        if isinstance(result.content, ShipmentEntity):
            await _logger.emit(AgentEvent(
                event_type=EventType.AGENT_COMPLETE,
                agent_name="Extractor",
                message=f"Extraction complete via LLM: {result.content.origin} -> {result.content.destination}",
                duration_ms=elapsed,
                data={"method": "agno_gemini", "mode": result.content.transport_mode.value},
            ))
            return result.content

        # Parsing response si string JSON
        await _logger.emit(AgentEvent(
            event_type=EventType.LLM_RESPONSE,
            agent_name="Extractor",
            message="LLM returned non-structured response, parsing JSON",
            data={"content_type": type(result.content).__name__},
        ))

        if isinstance(result.content, str):
            data = json.loads(result.content)
            entity = ShipmentEntity(**data)
            elapsed = (time.perf_counter() - start) * 1000
            await _logger.emit(AgentEvent(
                event_type=EventType.AGENT_COMPLETE,
                agent_name="Extractor",
                message=f"Extraction complete via JSON parse: {entity.origin} -> {entity.destination}",
                duration_ms=elapsed,
                data={"method": "agno_json_parse"},
            ))
            return entity

    except Exception as e:
        elapsed = (time.perf_counter() - start) * 1000
        logger.warning("LLM extraction failed, using deterministic fallback: %s", str(e))
        await _logger.emit(AgentEvent(
            event_type=EventType.INFO,
            agent_name="Extractor",
            message=f"LLM extraction failed, switching to deterministic fallback: {str(e)[:100]}",
            duration_ms=elapsed,
        ))

    # Fallback déterministe
    entity = _deterministic_extract(raw_content)
    elapsed = (time.perf_counter() - start) * 1000
    await _logger.emit(AgentEvent(
        event_type=EventType.AGENT_COMPLETE,
        agent_name="Extractor",
        message=f"Extraction complete via deterministic fallback: {entity.origin} -> {entity.destination}",
        duration_ms=elapsed,
        data={"method": "deterministic", "mode": entity.transport_mode.value},
    ))
    return entity
