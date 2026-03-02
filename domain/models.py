"""EcoChain AI — Domain Models.

Pydantic v2 models for the EcoChain AI supply chain carbon footprint system.
All models use strict validation, frozen immutability where applicable,
and Google-style docstrings.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum
from typing import Annotated

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)


class TransportMode(StrEnum):
    """Modes de transport pour le fret logistique.

    Valeurs alignées sur les catégories ADEME Scope 3.
    """

    ROAD = "road"
    MARITIME = "maritime"
    AIR = "air"
    RAIL = "rail"
    RIVER = "river"


class DocumentType(StrEnum):
    """Types de documents logistiques supportés."""

    INVOICE = "invoice"
    DELIVERY_NOTE = "delivery_note"
    BILL_OF_LADING = "bill_of_lading"
    PACKING_LIST = "packing_list"


class ValidationSeverity(StrEnum):
    """Niveaux de sévérité pour les résultats de validation."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class LogisticsDocument(BaseModel):
    """Document logistique brut simulant le résultat d'un OCR.

    Attributes:
        document_id: Identifiant unique du document.
        document_type: Type de document logistique.
        raw_content: Contenu brut JSON simulant l'OCR.
        source_filename: Nom du fichier source simulé.
        created_at: Date de création du document.
    """

    model_config = ConfigDict(frozen=True)

    document_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Identifiant unique du document",
    )
    document_type: DocumentType = Field(
        description="Type de document logistique",
    )
    raw_content: dict[str, str | float | int | list[str] | dict[str, str]] = Field(
        description="Contenu brut JSON du document simulé OCR",
    )
    source_filename: str = Field(
        description="Nom du fichier source",
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="Date de création",
    )


# Constrained numeric types for physical plausibility
PositiveFloat = Annotated[float, Field(gt=0, description="Valeur strictement positive")]
NonNegativeFloat = Annotated[float, Field(ge=0, description="Valeur positive ou nulle")]
Percentage = Annotated[float, Field(ge=0, le=100, description="Pourcentage entre 0 et 100")]


class ShipmentEntity(BaseModel):
    """Entité d'expédition extraite d'un document logistique.

    Représente un envoi unique avec toutes les informations nécessaires
    au calcul de l'empreinte carbone.

    Attributes:
        shipment_id: Identifiant unique de l'expédition.
        origin: Ville ou lieu d'expédition.
        destination: Ville ou lieu de destination.
        weight_kg: Poids de la marchandise en kilogrammes.
        distance_km: Distance parcourue en kilomètres.
        transport_mode: Mode de transport utilisé.
        shipper: Nom de l'expéditeur.
        receiver: Nom du destinataire.
        departure_date: Date de départ.
        arrival_date: Date d'arrivée prévue ou effective.
        goods_description: Description de la marchandise.
        currency: Devise de la facture.
        total_cost: Coût total du transport.
    """

    model_config = ConfigDict(frozen=True)

    shipment_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Identifiant unique de l'expédition",
    )
    origin: str = Field(min_length=1, description="Lieu d'expédition")
    destination: str = Field(min_length=1, description="Lieu de destination")
    weight_kg: PositiveFloat
    distance_km: PositiveFloat
    transport_mode: TransportMode
    shipper: str = Field(min_length=1, description="Nom de l'expéditeur")
    receiver: str = Field(min_length=1, description="Nom du destinataire")
    departure_date: str = Field(description="Date de départ ISO 8601")
    arrival_date: str = Field(description="Date d'arrivée ISO 8601")
    goods_description: str = Field(min_length=1, description="Description de la marchandise")
    currency: str = Field(
        default="EUR",
        pattern=r"^[A-Z]{3}$",
        description="Code devise ISO 4217",
    )
    total_cost: NonNegativeFloat = Field(default=0.0, description="Coût total en devise")

    @property
    def weight_tonnes(self) -> float:
        """Convertit le poids en tonnes métriques."""
        return self.weight_kg / 1000.0

    @field_validator("weight_kg")
    @classmethod
    def validate_weight_physical_limit(cls, v: float) -> float:
        """Vérifie que le poids est physiquement plausible (< 500 000 kg).

        Args:
            v: Poids en kg.

        Returns:
            Le poids validé.

        Raises:
            ValueError: Si le poids dépasse 500 000 kg.
        """
        max_weight_kg = 500_000.0
        if v > max_weight_kg:
            msg = f"Le poids {v} kg dépasse le maximum physiquement plausible ({max_weight_kg} kg)"
            raise ValueError(msg)
        return v

    @field_validator("distance_km")
    @classmethod
    def validate_distance_physical_limit(cls, v: float) -> float:
        """Vérifie que la distance est physiquement plausible (< 45 000 km).

        Args:
            v: Distance en km.

        Returns:
            La distance validée.

        Raises:
            ValueError: Si la distance dépasse la demi-circonférence terrestre.
        """
        max_distance_km = 45_000.0  # Demi-circonférence terrestre
        if v > max_distance_km:
            msg = f"La distance {v} km dépasse le maximum terrestre ({max_distance_km} km)"
            raise ValueError(msg)
        return v

    @model_validator(mode="after")
    def validate_dates_chronological(self) -> ShipmentEntity:
        """Vérifie que la date de départ précède la date d'arrivée.

        Returns:
            L'instance validée.

        Raises:
            ValueError: Si la date d'arrivée est antérieure à la date de départ.
        """
        try:
            dep = datetime.fromisoformat(self.departure_date)
            arr = datetime.fromisoformat(self.arrival_date)
            if arr < dep:
                msg = (
                    f"La date d'arrivée ({self.arrival_date}) est antérieure "
                    f"à la date de départ ({self.departure_date})"
                )
                raise ValueError(msg)
        except ValueError as e:
            if "antérieure" in str(e):
                raise
            # Si le format de date est invalide, on laisse passer
            # car l'agent Validator le vérifiera
        return self


class ValidationIssue(BaseModel):
    """Issue de validation identifiée sur une entité.

    Attributes:
        field: Nom du champ concerné.
        severity: Niveau de sévérité.
        message: Description humaine du problème.
        suggestion: Suggestion de correction.
    """

    model_config = ConfigDict(frozen=True)

    field: str = Field(description="Champ concerné")
    severity: ValidationSeverity = Field(description="Sévérité du problème")
    message: str = Field(description="Description du problème")
    suggestion: str = Field(default="", description="Suggestion de correction")


class ValidationResult(BaseModel):
    """Résultat global de la validation d'un document.

    Attributes:
        is_valid: Indique si le document est globalement valide.
        confidence_score: Score de confiance de la validation (0-100).
        issues: Liste des problèmes identifiés.
        validated_at: Date de la validation.
    """

    model_config = ConfigDict(frozen=True)

    is_valid: bool = Field(description="Document globalement valide")
    confidence_score: Percentage = Field(description="Score de confiance 0-100")
    issues: list[ValidationIssue] = Field(
        default_factory=list,
        description="Liste des problèmes identifiés",
    )
    validated_at: datetime = Field(
        default_factory=datetime.now,
        description="Date de validation",
    )


class EmissionDetail(BaseModel):
    """Détail de l'émission CO2 par envoi.

    Attributes:
        shipment_id: Identifiant de l'expédition.
        transport_mode: Mode de transport utilisé.
        weight_tonnes: Poids en tonnes.
        distance_km: Distance en km.
        emission_factor: Facteur d'émission utilisé (kgCO2e/t.km).
        co2_kg: Émission calculée en kgCO2e.
    """

    model_config = ConfigDict(frozen=True)

    shipment_id: str = Field(description="ID de l'expédition")
    transport_mode: TransportMode = Field(description="Mode de transport")
    weight_tonnes: PositiveFloat
    distance_km: PositiveFloat
    emission_factor: PositiveFloat = Field(description="kgCO2e/t.km")
    co2_kg: NonNegativeFloat = Field(description="Émission totale en kgCO2e")


class ModeComparison(BaseModel):
    """Comparaison des émissions entre modes de transport.

    Attributes:
        mode: Mode de transport.
        co2_kg: Émission estimée en kgCO2e.
        is_current: Indique si c'est le mode actuellement utilisé.
        saving_vs_current_pct: Économie en % par rapport au mode actuel.
    """

    model_config = ConfigDict(frozen=True)

    mode: TransportMode = Field(description="Mode de transport")
    co2_kg: NonNegativeFloat = Field(description="Émission en kgCO2e")
    is_current: bool = Field(default=False, description="Mode actuellement utilisé")
    saving_vs_current_pct: float = Field(
        default=0.0,
        description="Économie en % vs mode actuel (négatif = plus émetteur)",
    )


class Recommendation(BaseModel):
    """Recommandation de réduction d'émissions CO2.

    Attributes:
        title: Titre court de la recommandation.
        description: Description détaillée et actionnable.
        potential_saving_pct: Potentiel de réduction en pourcentage.
        priority: Priorité (1 = haute, 2 = moyenne, 3 = basse).
        category: Catégorie (modal_shift, consolidation, route_optimization, etc.).
    """

    model_config = ConfigDict(frozen=True)

    title: str = Field(min_length=1, description="Titre court")
    description: str = Field(min_length=10, description="Description actionnable")
    potential_saving_pct: Percentage = Field(description="Réduction potentielle en %")
    priority: int = Field(ge=1, le=3, description="Priorité 1-3")
    category: str = Field(min_length=1, description="Catégorie de la recommandation")


class CarbonReport(BaseModel):
    """Rapport carbone complet pour un document logistique.

    Agrège extraction, validation, calcul CO2, comparaisons et recommandations.

    Attributes:
        report_id: Identifiant unique du rapport.
        document_id: ID du document source.
        shipments: Liste des expéditions extraites.
        validation: Résultat de la validation.
        emissions: Liste des détails d'émission par expédition.
        total_co2_kg: Total des émissions en kgCO2e.
        mode_comparisons: Comparaison via les différents modes.
        recommendations: Liste des recommandations de réduction.
        processing_time_ms: Temps de traitement en millisecondes.
        created_at: Date de création du rapport.
    """

    model_config = ConfigDict(frozen=True)

    report_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Identifiant unique du rapport",
    )
    document_id: str = Field(description="ID du document source")
    shipments: list[ShipmentEntity] = Field(description="Expéditions extraites")
    validation: ValidationResult = Field(description="Résultat de validation")
    emissions: list[EmissionDetail] = Field(description="Détails d'émission par envoi")
    total_co2_kg: NonNegativeFloat = Field(description="Total émissions kgCO2e")
    mode_comparisons: list[ModeComparison] = Field(
        default_factory=list,
        description="Comparaison des modes de transport",
    )
    recommendations: list[Recommendation] = Field(
        default_factory=list,
        description="Recommandations de réduction",
    )
    processing_time_ms: NonNegativeFloat = Field(
        default=0.0,
        description="Temps de traitement en ms",
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="Date de création du rapport",
    )


class ProcessingError(BaseModel):
    """Erreur structurée retournée en cas d'échec du traitement.

    Attributes:
        error_code: Code d'erreur machine-readable.
        message: Message d'erreur humainement compréhensible.
        details: Détails additionnels optionnels.
        document_id: ID du document concerné.
    """

    model_config = ConfigDict(frozen=True)

    error_code: str = Field(description="Code d'erreur")
    message: str = Field(description="Message d'erreur")
    details: str = Field(default="", description="Détails additionnels")
    document_id: str = Field(default="", description="ID du document concerné")
