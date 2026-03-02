"""Tests unitaires pour les domain models Pydantic v2.

Couvre la validation, les contraintes, les enums et les model validators.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from domain.models import (
    CarbonReport,
    DocumentType,
    EmissionDetail,
    LogisticsDocument,
    ModeComparison,
    Recommendation,
    ShipmentEntity,
    TransportMode,
    ValidationIssue,
    ValidationResult,
    ValidationSeverity,
)


class TestTransportMode:
    """Tests pour l'enum TransportMode."""

    def test_all_modes_exist(self) -> None:
        """Vérifie que les 5 modes de transport existent."""
        assert len(TransportMode) == 5
        assert TransportMode.ROAD == "road"
        assert TransportMode.MARITIME == "maritime"
        assert TransportMode.AIR == "air"
        assert TransportMode.RAIL == "rail"
        assert TransportMode.RIVER == "river"


class TestShipmentEntity:
    """Tests pour le modèle ShipmentEntity."""

    def test_valid_shipment(self) -> None:
        """Test création d'un ShipmentEntity valide."""
        shipment = ShipmentEntity(
            origin="Paris",
            destination="Berlin",
            weight_kg=5000.0,
            distance_km=1050.0,
            transport_mode=TransportMode.ROAD,
            shipper="Acme Corp",
            receiver="Beta GmbH",
            departure_date="2024-03-01",
            arrival_date="2024-03-03",
            goods_description="Matériel informatique",
        )
        assert shipment.weight_tonnes == pytest.approx(5.0)
        assert shipment.currency == "EUR"  # Défaut

    def test_weight_kg_too_high(self) -> None:
        """Test rejet si poids > 500 000 kg."""
        with pytest.raises(ValidationError, match="maximum physiquement plausible"):
            ShipmentEntity(
                origin="A", destination="B", weight_kg=600000.0,
                distance_km=100.0, transport_mode=TransportMode.ROAD,
                shipper="S", receiver="R",
                departure_date="2024-01-01", arrival_date="2024-01-02",
                goods_description="Test",
            )

    def test_distance_too_high(self) -> None:
        """Test rejet si distance > 45 000 km."""
        with pytest.raises(ValidationError, match="maximum terrestre"):
            ShipmentEntity(
                origin="A", destination="B", weight_kg=1000.0,
                distance_km=50000.0, transport_mode=TransportMode.ROAD,
                shipper="S", receiver="R",
                departure_date="2024-01-01", arrival_date="2024-01-02",
                goods_description="Test",
            )

    def test_negative_weight_rejected(self) -> None:
        """Test rejet si poids négatif."""
        with pytest.raises(ValidationError):
            ShipmentEntity(
                origin="A", destination="B", weight_kg=-100.0,
                distance_km=100.0, transport_mode=TransportMode.ROAD,
                shipper="S", receiver="R",
                departure_date="2024-01-01", arrival_date="2024-01-02",
                goods_description="Test",
            )

    def test_arrival_before_departure(self) -> None:
        """Test rejet si date d'arrivée antérieure au départ."""
        with pytest.raises(ValidationError, match="antérieure"):
            ShipmentEntity(
                origin="A", destination="B", weight_kg=1000.0,
                distance_km=100.0, transport_mode=TransportMode.ROAD,
                shipper="S", receiver="R",
                departure_date="2024-06-15",
                arrival_date="2024-06-10",
                goods_description="Test",
            )

    def test_invalid_currency_pattern(self) -> None:
        """Test rejet si la devise ne respecte pas le pattern ISO 4217."""
        with pytest.raises(ValidationError):
            ShipmentEntity(
                origin="A", destination="B", weight_kg=1000.0,
                distance_km=100.0, transport_mode=TransportMode.ROAD,
                shipper="S", receiver="R",
                departure_date="2024-01-01", arrival_date="2024-01-02",
                goods_description="Test",
                currency="euro",  # Doit être 3 lettres majuscules
            )

    def test_frozen_immutable(self) -> None:
        """Test que le modèle est immutable (frozen=True)."""
        shipment = ShipmentEntity(
            origin="A", destination="B", weight_kg=1000.0,
            distance_km=100.0, transport_mode=TransportMode.ROAD,
            shipper="S", receiver="R",
            departure_date="2024-01-01", arrival_date="2024-01-02",
            goods_description="Test",
        )
        with pytest.raises(ValidationError):
            shipment.origin = "NewPlace"  # type: ignore[misc]


class TestValidationResult:
    """Tests pour ValidationResult."""

    def test_valid_result(self) -> None:
        """Test création d'un ValidationResult valide."""
        result = ValidationResult(is_valid=True, confidence_score=95.0)
        assert result.is_valid is True
        assert result.confidence_score == 95.0
        assert result.issues == []

    def test_confidence_bounds(self) -> None:
        """Test que le score est borné 0-100."""
        with pytest.raises(ValidationError):
            ValidationResult(is_valid=True, confidence_score=150.0)

        with pytest.raises(ValidationError):
            ValidationResult(is_valid=True, confidence_score=-10.0)


class TestRecommendation:
    """Tests pour Recommendation."""

    def test_valid_recommendation(self) -> None:
        """Test création d'une recommandation valide."""
        rec = Recommendation(
            title="Transfert modal routier → ferroviaire",
            description="Transférer les envois vers le ferroviaire pour réduire les émissions.",
            potential_saving_pct=35.0,
            priority=1,
            category="modal_shift",
        )
        assert rec.priority == 1
        assert rec.potential_saving_pct == 35.0

    def test_priority_bounds(self) -> None:
        """Test que la priorité est bornée 1-3."""
        with pytest.raises(ValidationError):
            Recommendation(
                title="Test", description="Description test valide",
                potential_saving_pct=10.0, priority=5,
                category="test",
            )


class TestLogisticsDocument:
    """Tests pour LogisticsDocument."""

    def test_auto_uuid(self) -> None:
        """Test que l'ID est auto-généré."""
        doc = LogisticsDocument(
            document_type=DocumentType.INVOICE,
            raw_content={"key": "value"},
            source_filename="test.json",
        )
        assert len(doc.document_id) > 0
        assert doc.document_type == DocumentType.INVOICE
