"""Tests unitaires pour le CarbonCalculator.

Couvre tous les modes de transport, cas limites, comparaisons
et benchmarks sectoriels. 14 tests au total.
"""

from __future__ import annotations

import pytest

from application.calculators.carbon_calculator import CarbonCalculator
from domain.constants import EMISSION_FACTORS, SECTOR_BENCHMARK_CO2_KG
from domain.models import ShipmentEntity, TransportMode


@pytest.fixture
def calculator() -> CarbonCalculator:
    """Fixture CarbonCalculator avec facteurs ADEME par défaut."""
    return CarbonCalculator()


@pytest.fixture
def sample_shipment() -> ShipmentEntity:
    """Fixture expédition routière standard."""
    return ShipmentEntity(
        origin="Hamburg",
        destination="Marseille",
        weight_kg=15000.0,
        distance_km=1450.0,
        transport_mode=TransportMode.ROAD,
        shipper="TransEurope Logistics",
        receiver="MedFreight SAS",
        departure_date="2024-03-15",
        arrival_date="2024-03-17",
        goods_description="Composants électroniques",
    )


# ──────────────────────────────────────────────────
# Tests : calculate_emission
# ──────────────────────────────────────────────────


class TestCalculateEmission:
    """Tests pour la méthode calculate_emission."""

    def test_road_emission(self, calculator: CarbonCalculator) -> None:
        """Test émission routière : 10t × 1000km × 0.0621 = 621 kgCO2e."""
        result = calculator.calculate_emission(10.0, 1000.0, TransportMode.ROAD)
        assert result == pytest.approx(621.0, rel=1e-3)

    def test_maritime_emission(self, calculator: CarbonCalculator) -> None:
        """Test émission maritime : 100t × 10000km × 0.0160 = 16000 kgCO2e."""
        result = calculator.calculate_emission(100.0, 10000.0, TransportMode.MARITIME)
        assert result == pytest.approx(16000.0, rel=1e-3)

    def test_air_emission(self, calculator: CarbonCalculator) -> None:
        """Test émission aérienne : 5t × 5000km × 1.06 = 26500 kgCO2e."""
        result = calculator.calculate_emission(5.0, 5000.0, TransportMode.AIR)
        assert result == pytest.approx(26500.0, rel=1e-3)

    def test_rail_emission(self, calculator: CarbonCalculator) -> None:
        """Test émission ferroviaire : 50t × 2000km × 0.0225 = 2250 kgCO2e."""
        result = calculator.calculate_emission(50.0, 2000.0, TransportMode.RAIL)
        assert result == pytest.approx(2250.0, rel=1e-3)

    def test_river_emission(self, calculator: CarbonCalculator) -> None:
        """Test émission fluviale : 200t × 500km × 0.031 = 3100 kgCO2e."""
        result = calculator.calculate_emission(200.0, 500.0, TransportMode.RIVER)
        assert result == pytest.approx(3100.0, rel=1e-3)

    def test_negative_weight_raises(self, calculator: CarbonCalculator) -> None:
        """Test erreur si poids négatif."""
        with pytest.raises(ValueError, match="poids doit être positif"):
            calculator.calculate_emission(-5.0, 1000.0, TransportMode.ROAD)

    def test_zero_distance_raises(self, calculator: CarbonCalculator) -> None:
        """Test erreur si distance nulle."""
        with pytest.raises(ValueError, match="distance doit être positive"):
            calculator.calculate_emission(10.0, 0.0, TransportMode.ROAD)

    def test_small_values(self, calculator: CarbonCalculator) -> None:
        """Test avec des petites valeurs (envoi léger, courte distance)."""
        result = calculator.calculate_emission(0.001, 1.0, TransportMode.ROAD)
        assert result > 0
        assert result < 1.0  # Devrait être très faible


# ──────────────────────────────────────────────────
# Tests : calculate_emission_from_shipment
# ──────────────────────────────────────────────────


class TestCalculateFromShipment:
    """Tests pour calculate_emission_from_shipment."""

    def test_from_shipment(
        self,
        calculator: CarbonCalculator,
        sample_shipment: ShipmentEntity,
    ) -> None:
        """Test calcul depuis un ShipmentEntity complet."""
        detail = calculator.calculate_emission_from_shipment(sample_shipment)
        # 15t × 1450km × 0.0621 = 1350.675 kgCO2e
        expected = 15.0 * 1450.0 * 0.0621
        assert detail.co2_kg == pytest.approx(expected, rel=1e-3)
        assert detail.transport_mode == TransportMode.ROAD
        assert detail.weight_tonnes == pytest.approx(15.0, rel=1e-3)


# ──────────────────────────────────────────────────
# Tests : calculate_scope3_total
# ──────────────────────────────────────────────────


class TestScope3Total:
    """Tests pour calculate_scope3_total."""

    def test_multiple_shipments(self, calculator: CarbonCalculator) -> None:
        """Test somme correcte de plusieurs expéditions."""
        shipments = [
            ShipmentEntity(
                origin="A", destination="B", weight_kg=10000.0,
                distance_km=1000.0, transport_mode=TransportMode.ROAD,
                shipper="S1", receiver="R1",
                departure_date="2024-01-01", arrival_date="2024-01-02",
                goods_description="Goods 1",
            ),
            ShipmentEntity(
                origin="C", destination="D", weight_kg=5000.0,
                distance_km=500.0, transport_mode=TransportMode.RAIL,
                shipper="S2", receiver="R2",
                departure_date="2024-01-01", arrival_date="2024-01-02",
                goods_description="Goods 2",
            ),
        ]

        emissions, total = calculator.calculate_scope3_total(shipments)
        assert len(emissions) == 2
        expected_road = 10.0 * 1000.0 * 0.0621  # 621.0
        expected_rail = 5.0 * 500.0 * 0.0225  # 56.25
        assert total == pytest.approx(expected_road + expected_rail, rel=1e-3)

    def test_empty_shipments(self, calculator: CarbonCalculator) -> None:
        """Test avec liste vide."""
        emissions, total = calculator.calculate_scope3_total([])
        assert emissions == []
        assert total == 0.0


# ──────────────────────────────────────────────────
# Tests : compare_transport_modes
# ──────────────────────────────────────────────────


class TestCompareTransportModes:
    """Tests pour compare_transport_modes."""

    def test_comparison_sorted(self, calculator: CarbonCalculator) -> None:
        """Test que les comparaisons sont triées par émission croissante."""
        comparisons = calculator.compare_transport_modes(10.0, 1000.0)
        co2_values = [c.co2_kg for c in comparisons]
        assert co2_values == sorted(co2_values)

    def test_current_mode_flagged(self, calculator: CarbonCalculator) -> None:
        """Test que le mode actuel est correctement flaggé."""
        comparisons = calculator.compare_transport_modes(
            10.0, 1000.0, current_mode=TransportMode.ROAD
        )
        current_modes = [c for c in comparisons if c.is_current]
        assert len(current_modes) == 1
        assert current_modes[0].mode == TransportMode.ROAD
        assert current_modes[0].saving_vs_current_pct == pytest.approx(0.0, abs=0.1)

    def test_savings_calculated(self, calculator: CarbonCalculator) -> None:
        """Test que les économies sont calculées par rapport au mode actuel."""
        comparisons = calculator.compare_transport_modes(
            10.0, 1000.0, current_mode=TransportMode.AIR
        )
        # Le maritime et le ferroviaire devraient montrer des économies > 90%
        maritime = next(c for c in comparisons if c.mode == TransportMode.MARITIME)
        assert maritime.saving_vs_current_pct > 90.0


# ──────────────────────────────────────────────────
# Tests : benchmark_vs_sector
# ──────────────────────────────────────────────────


class TestBenchmarkSector:
    """Tests pour benchmark_vs_sector."""

    def test_above_benchmark(self, calculator: CarbonCalculator) -> None:
        """Test quand l'émission dépasse le benchmark."""
        result = calculator.benchmark_vs_sector(300.0)
        assert result["is_above_benchmark"] is True
        assert result["ecart_kg"] == pytest.approx(150.0, rel=1e-3)
        assert result["ratio_vs_benchmark_pct"] == pytest.approx(200.0, rel=1e-1)

    def test_below_benchmark(self, calculator: CarbonCalculator) -> None:
        """Test quand l'émission est sous le benchmark."""
        result = calculator.benchmark_vs_sector(50.0)
        assert result["is_above_benchmark"] is False
        assert result["ecart_kg"] < 0
