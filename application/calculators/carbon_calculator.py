"""EcoChain AI — Carbon Calculator.

Classe CarbonCalculator POO pure — calcul déterministe des émissions
CO2 Scope 3 pour le transport de marchandises. Aucun appel LLM,
aucun I/O, 100% testable et synchrone.

Formule ADEME : CO2 (kgCO2e) = poids (tonnes) × distance (km) × facteur d'émission (kgCO2e/t.km)
"""

from __future__ import annotations

from domain.constants import EMISSION_FACTORS, SECTOR_BENCHMARK_CO2_KG
from domain.models import (
    EmissionDetail,
    ModeComparison,
    ShipmentEntity,
    TransportMode,
)


class CarbonCalculator:
    """Calculateur d'empreinte carbone Scope 3 — transport de marchandises.

    Module Python pur, synchrone, sans aucun I/O. Utilise les facteurs
    d'émission ADEME (Base Carbone) pour le calcul Well-to-Wheel.

    Formule : CO2 (kgCO2e) = poids_tonnes × distance_km × facteur_émission
    """

    def __init__(
        self,
        emission_factors: dict[TransportMode, float] | None = None,
    ) -> None:
        """Initialise le CarbonCalculator.

        Args:
            emission_factors: Facteurs d'émission personnalisés.
                Si None, utilise les facteurs ADEME par défaut.
        """
        self._factors = emission_factors or EMISSION_FACTORS

    @property
    def emission_factors(self) -> dict[TransportMode, float]:
        """Retourne les facteurs d'émission utilisés.

        Returns:
            Dictionnaire mode → facteur kgCO2e/t.km.
        """
        return dict(self._factors)

    def get_factor(self, mode: TransportMode) -> float:
        """Retourne le facteur d'émission pour un mode donné.

        Args:
            mode: Mode de transport.

        Returns:
            Facteur d'émission en kgCO2e/t.km.

        Raises:
            ValueError: Si le mode n'est pas supporté.
        """
        factor = self._factors.get(mode)
        if factor is None:
            msg = f"Mode de transport non supporté: {mode}"
            raise ValueError(msg)
        return factor

    def calculate_emission(
        self,
        weight_tonnes: float,
        distance_km: float,
        mode: TransportMode,
    ) -> float:
        """Calcule l'émission CO2 pour un envoi unique.

        Formule : CO2 = poids_tonnes × distance_km × facteur_émission

        Args:
            weight_tonnes: Poids de la marchandise en tonnes.
            distance_km: Distance parcourue en km.
            mode: Mode de transport utilisé.

        Returns:
            Émission en kgCO2e.

        Raises:
            ValueError: Si le poids ou la distance est négatif/nul,
                ou si le mode n'est pas supporté.
        """
        if weight_tonnes <= 0:
            msg = f"Le poids doit être positif, reçu: {weight_tonnes}"
            raise ValueError(msg)
        if distance_km <= 0:
            msg = f"La distance doit être positive, reçue: {distance_km}"
            raise ValueError(msg)

        factor = self.get_factor(mode)
        return round(weight_tonnes * distance_km * factor, 4)

    def calculate_emission_from_shipment(
        self,
        shipment: ShipmentEntity,
    ) -> EmissionDetail:
        """Calcule l'émission CO2 à partir d'une entité ShipmentEntity.

        Args:
            shipment: Entité d'expédition complète.

        Returns:
            EmissionDetail avec tous les paramètres de calcul.
        """
        factor = self.get_factor(shipment.transport_mode)
        co2 = round(shipment.weight_tonnes * shipment.distance_km * factor, 4)

        return EmissionDetail(
            shipment_id=shipment.shipment_id,
            transport_mode=shipment.transport_mode,
            weight_tonnes=shipment.weight_tonnes,
            distance_km=shipment.distance_km,
            emission_factor=factor,
            co2_kg=co2,
        )

    def calculate_scope3_total(
        self,
        shipments: list[ShipmentEntity],
    ) -> tuple[list[EmissionDetail], float]:
        """Calcule les émissions Scope 3 totales pour une liste d'expéditions.

        Args:
            shipments: Liste des expéditions à calculer.

        Returns:
            Tuple (liste des EmissionDetail, total CO2 en kgCO2e).
        """
        emissions: list[EmissionDetail] = []
        total_co2 = 0.0

        for shipment in shipments:
            detail = self.calculate_emission_from_shipment(shipment)
            emissions.append(detail)
            total_co2 += detail.co2_kg

        return emissions, round(total_co2, 4)

    def compare_transport_modes(
        self,
        weight_tonnes: float,
        distance_km: float,
        current_mode: TransportMode | None = None,
    ) -> list[ModeComparison]:
        """Compare les émissions entre tous les modes de transport.

        Utile pour identifier le mode le moins émetteur et quantifier
        les économies potentielles lors d'un transfert modal.

        Args:
            weight_tonnes: Poids en tonnes.
            distance_km: Distance en km.
            current_mode: Mode actuellement utilisé (optionnel).

        Returns:
            Liste des ModeComparison triée par émission croissante.

        Raises:
            ValueError: Si le poids ou la distance est invalide.
        """
        if weight_tonnes <= 0:
            msg = f"Le poids doit être positif, reçu: {weight_tonnes}"
            raise ValueError(msg)
        if distance_km <= 0:
            msg = f"La distance doit être positive, reçue: {distance_km}"
            raise ValueError(msg)

        # Calcul de référence si un mode actuel est spécifié
        current_co2 = 0.0
        if current_mode is not None:
            current_factor = self._factors.get(current_mode, 0.0)
            current_co2 = weight_tonnes * distance_km * current_factor

        comparisons: list[ModeComparison] = []
        for mode, factor in self._factors.items():
            co2 = round(weight_tonnes * distance_km * factor, 4)

            saving_pct = 0.0
            if current_mode is not None and current_co2 > 0:
                saving_pct = round((current_co2 - co2) / current_co2 * 100, 1)

            comparisons.append(ModeComparison(
                mode=mode,
                co2_kg=co2,
                is_current=(mode == current_mode),
                saving_vs_current_pct=saving_pct,
            ))

        comparisons.sort(key=lambda c: c.co2_kg)
        return comparisons

    def benchmark_vs_sector(
        self,
        total_co2_kg: float,
        benchmark_kg: float = SECTOR_BENCHMARK_CO2_KG,
    ) -> dict[str, float]:
        """Compare l'empreinte totale par rapport au benchmark sectoriel.

        Args:
            total_co2_kg: Émission totale calculée en kgCO2e.
            benchmark_kg: Benchmark sectoriel de référence.

        Returns:
            Dictionnaire avec total, benchmark, ratio et écart.
        """
        ratio = (total_co2_kg / benchmark_kg * 100) if benchmark_kg > 0 else 0.0
        ecart = total_co2_kg - benchmark_kg

        return {
            "total_co2_kg": round(total_co2_kg, 2),
            "benchmark_co2_kg": round(benchmark_kg, 2),
            "ratio_vs_benchmark_pct": round(ratio, 1),
            "ecart_kg": round(ecart, 2),
            "is_above_benchmark": total_co2_kg > benchmark_kg,
        }
