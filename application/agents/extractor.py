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
from pydantic import BaseModel, Field

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
    "- weight_kg: total gross weight in kilograms (MUST be > 0, use 1.0 if unknown)",
    "- distance_km: distance in kilometers (MUST be > 0, use 1.0 if unknown)",
    "- transport_mode: one of 'road', 'maritime', 'air', 'rail', 'river'",
    "- shipper: name of the shipping company",
    "- receiver: name of the receiving company",
    "- departure_date: in YYYY-MM-DD format",
    "- arrival_date: in YYYY-MM-DD format",
    "- goods_description: description of the goods",
    "- currency: ISO 4217 code (default EUR)",
    "NEVER return 0 for weight_kg or distance_km. Use at least 1.0 when unclear.",
    "For transport_mode, infer from keywords: 'camion/truck' -> road, 'navire/vessel' -> maritime, etc.",
    "Always return valid JSON matching the expected schema.",
]


class ExtractShipmentSchema(BaseModel):
    """Schema LLM compatible (sans exclusiveMinimum rejeté par Gemini)."""

    origin: str = Field(min_length=1)
    destination: str = Field(min_length=1)
    weight_kg: float = Field(ge=0.001, description="Must be > 0")
    distance_km: float = Field(ge=0.001, description="Must be > 0")
    transport_mode: str = Field(pattern="^(road|maritime|air|rail|river)$")
    shipper: str = Field(min_length=1)
    receiver: str = Field(min_length=1)
    departure_date: str = Field()
    arrival_date: str = Field()
    goods_description: str = Field(min_length=1)
    currency: str = Field(default="EUR", pattern=r"^[A-Z]{3}$")


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


async def extract_shipment(
    raw_content: dict[str, Any],
    event_logger: EventLogger | None = None,
) -> ShipmentEntity:
    """Extrait un ShipmentEntity depuis un document JSON brut via LLM.

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

    agent = create_extractor_agent()

    # Schema ExtractShipmentSchema (ge=0.001) compatible Gemini — évite exclusiveMinimum
    content = (
        raw_content.get("raw_text", "")
        if "raw_text" in raw_content
        else json.dumps(raw_content, indent=2, ensure_ascii=False)
    )
    prompt = "Extract shipment data from this logistics document:\n\n" + content

    await _logger.emit(AgentEvent(
        event_type=EventType.LLM_CALL,
        agent_name="Extractor",
        message="Calling Gemini 2.5 Flash for structured extraction",
        data={"model": "gemini-2.5-flash", "input_keys": list(raw_content.keys())},
    ))

    try:
        result = await agent.arun(prompt, output_schema=ExtractShipmentSchema)
    except Exception as e:
        logger.error("LLM extraction failed: %s", str(e))
        await _logger.emit(AgentEvent(
            event_type=EventType.ERROR,
            agent_name="Extractor",
            message=f"LLM extraction failed: {str(e)[:150]}",
            duration_ms=(time.perf_counter() - start) * 1000,
        ))
        raise
    elapsed = (time.perf_counter() - start) * 1000

    extracted = result.content
    if not isinstance(extracted, ExtractShipmentSchema):
        if isinstance(result.content, str):
            extracted = ExtractShipmentSchema.model_validate(json.loads(result.content))
        else:
            raise ValueError(f"LLM extraction failed: unexpected response type {type(result.content)}")

    # Convert to ShipmentEntity (sanitize: ensure > 0 for domain model)
    weight = max(extracted.weight_kg, 1.0)
    distance = max(extracted.distance_km, 1.0)
    mode = TransportMode(extracted.transport_mode)

    entity = ShipmentEntity(
        origin=extracted.origin,
        destination=extracted.destination,
        weight_kg=weight,
        distance_km=distance,
        transport_mode=mode,
        shipper=extracted.shipper,
        receiver=extracted.receiver,
        departure_date=extracted.departure_date,
        arrival_date=extracted.arrival_date,
        goods_description=extracted.goods_description,
        currency=extracted.currency,
    )

    await _logger.emit(AgentEvent(
        event_type=EventType.AGENT_COMPLETE,
        agent_name="Extractor",
        message=f"Extraction complete via LLM: {entity.origin} -> {entity.destination}",
        duration_ms=elapsed,
        data={"method": "agno_gemini", "mode": entity.transport_mode.value},
    ))
    return entity
