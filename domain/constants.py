"""EcoChain AI — Facteurs d'émission carbone.

Facteurs d'émission ADEME pour le transport de marchandises (Scope 3).
Source : Base Carbone ADEME — Transport de marchandises.
Unité : kgCO2e par tonne-kilomètre.

Ces valeurs représentent les émissions moyennes incluant la fabrication
du véhicule, la production de carburant et la combustion (Well-to-Wheel).
"""

from __future__ import annotations

from domain.models import TransportMode

# Facteurs d'émission ADEME — kgCO2e / tonne.km (Well-to-Wheel)
# Source : Base Carbone ADEME v22, catégorie "Transport de marchandises"
EMISSION_FACTORS: dict[TransportMode, float] = {
    TransportMode.ROAD: 0.0621,       # Poids lourd articulé 40t, France, moyenne
    TransportMode.MARITIME: 0.0160,    # Porte-conteneurs moyen, international
    TransportMode.AIR: 1.0600,         # Avion cargo, court/moyen-courrier
    TransportMode.RAIL: 0.0225,        # Train fret, réseau ferré France
    TransportMode.RIVER: 0.0310,       # Transport fluvial, France
}

# Benchmarks sectoriels pour la comparaison (kgCO2e par envoi moyen)
# Basés sur des moyennes industrielles européennes
SECTOR_BENCHMARK_CO2_KG: float = 150.0  # Émission moyenne par envoi dans le secteur

# Distances maximales réalistes par mode de transport (km)
MAX_DISTANCE_BY_MODE: dict[TransportMode, float] = {
    TransportMode.ROAD: 5_000.0,       # Europe continentale max
    TransportMode.MARITIME: 40_000.0,  # Routes maritimes les plus longues
    TransportMode.AIR: 20_000.0,       # Vols cargo les plus longs
    TransportMode.RAIL: 15_000.0,      # Transsibérien et routes eurasiatiques
    TransportMode.RIVER: 2_000.0,      # Réseaux fluviaux européens
}

# Poids maximum typique par mode de transport (kg)
MAX_WEIGHT_BY_MODE: dict[TransportMode, float] = {
    TransportMode.ROAD: 25_000.0,      # Capacité poids lourd 40t
    TransportMode.MARITIME: 400_000_000.0,  # Porte-conteneurs ultra-large
    TransportMode.AIR: 120_000.0,      # Avion cargo Boeing 777F
    TransportMode.RAIL: 5_000_000.0,   # Train de fret complet
    TransportMode.RIVER: 3_000_000.0,  # Convoi poussé fluvial
}

# Noms lisibles pour l'affichage frontend
TRANSPORT_MODE_LABELS: dict[TransportMode, str] = {
    TransportMode.ROAD: "🚛 Routier",
    TransportMode.MARITIME: "🚢 Maritime",
    TransportMode.AIR: "✈️ Aérien",
    TransportMode.RAIL: "🚆 Ferroviaire",
    TransportMode.RIVER: "🚢 Fluvial",
}

# Devises supportées
SUPPORTED_CURRENCIES: frozenset[str] = frozenset({
    "EUR", "USD", "GBP", "CHF", "JPY", "CNY", "CAD", "AUD",
})
