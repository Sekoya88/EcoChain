"""EcoChain AI — Mock Data Generator.

Génère 10 documents logistiques JSON réalistes simulant le résultat
d'un OCR sur des factures fournisseurs et bons de livraison.
Les données sont variées en termes de modes de transport, distances,
poids, et origines/destinations.
"""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any

from domain.models import DocumentType, LogisticsDocument


# Données de référence pour la génération
_COMPANIES: list[dict[str, str]] = [
    {"name": "TransEurope Logistics GmbH", "city": "Hamburg", "country": "Germany"},
    {"name": "Mediterranean Freight SAS", "city": "Marseille", "country": "France"},
    {"name": "Nordic Supply Chain AB", "city": "Gothenburg", "country": "Sweden"},
    {"name": "Iberian Transport SL", "city": "Barcelona", "country": "Spain"},
    {"name": "Alpine Cargo AG", "city": "Zurich", "country": "Switzerland"},
    {"name": "Atlantic Shipping Ltd", "city": "Rotterdam", "country": "Netherlands"},
    {"name": "Baltic Trade OÜ", "city": "Tallinn", "country": "Estonia"},
    {"name": "Central Logistics sp. z o.o.", "city": "Warsaw", "country": "Poland"},
    {"name": "Adriatic Freight S.r.l.", "city": "Trieste", "country": "Italy"},
    {"name": "Channel Express PLC", "city": "Dover", "country": "United Kingdom"},
    {"name": "Rhine Barging BV", "city": "Duisburg", "country": "Germany"},
    {"name": "Silk Road Cargo KFT", "city": "Budapest", "country": "Hungary"},
    {"name": "Danube Logistics SRL", "city": "Constanta", "country": "Romania"},
    {"name": "Fjord Shipping AS", "city": "Bergen", "country": "Norway"},
    {"name": "Lusitania Freight Lda", "city": "Lisbon", "country": "Portugal"},
]

_GOODS: list[dict[str, str | float]] = [
    {"description": "Composants électroniques haute densité", "unit_weight": 0.5},
    {"description": "Pièces automobiles (transmissions)", "unit_weight": 45.0},
    {"description": "Textiles et vêtements de luxe", "unit_weight": 2.0},
    {"description": "Produits pharmaceutiques thermosensibles", "unit_weight": 1.5},
    {"description": "Machines industrielles CNC", "unit_weight": 2500.0},
    {"description": "Denrées alimentaires réfrigérées", "unit_weight": 15.0},
    {"description": "Matériaux de construction (acier profilé)", "unit_weight": 500.0},
    {"description": "Produits chimiques en fûts (non dangereux)", "unit_weight": 200.0},
    {"description": "Meubles en kit (panneaux MDF)", "unit_weight": 30.0},
    {"description": "Équipements photovoltaïques (panneaux solaires)", "unit_weight": 22.0},
]

_ROUTES: list[dict[str, str | float | str]] = [
    {"origin": "Hamburg", "destination": "Marseille", "distance": 1450.0, "mode": "road"},
    {"origin": "Rotterdam", "destination": "Shanghai", "distance": 19500.0, "mode": "maritime"},
    {"origin": "Paris", "destination": "New York", "distance": 5830.0, "mode": "air"},
    {"origin": "Duisburg", "destination": "Constanta", "distance": 1800.0, "mode": "river"},
    {"origin": "Barcelona", "destination": "Warsaw", "distance": 2200.0, "mode": "rail"},
    {"origin": "Marseille", "destination": "Algiers", "distance": 800.0, "mode": "maritime"},
    {"origin": "Gothenburg", "destination": "Trieste", "distance": 1900.0, "mode": "road"},
    {"origin": "Zurich", "destination": "Budapest", "distance": 850.0, "mode": "rail"},
    {"origin": "Dover", "destination": "Lisbon", "distance": 1700.0, "mode": "road"},
    {"origin": "Tallinn", "destination": "Bergen", "distance": 1600.0, "mode": "maritime"},
]


def _generate_invoice_content(
    route: dict[str, Any],
    goods: dict[str, Any],
    shipper: dict[str, str],
    receiver: dict[str, str],
    quantity: int,
) -> dict[str, str | float | int | list[str] | dict[str, str]]:
    """Génère le contenu brut d'une facture simulée OCR.

    Args:
        route: Informations de route (origin, destination, distance, mode).
        goods: Informations sur la marchandise (description, unit_weight).
        shipper: Informations sur l'expéditeur.
        receiver: Informations sur le destinataire.
        quantity: Quantité de marchandise.

    Returns:
        Dictionnaire simulant le résultat OCR d'une facture.
    """
    total_weight = float(goods["unit_weight"]) * quantity
    unit_price = round(random.uniform(50.0, 500.0), 2)
    total_cost = round(unit_price * quantity, 2)
    departure_month = random.randint(1, 11)
    departure_day = random.randint(1, 28)
    transit_days = random.randint(1, 21)

    return {
        "document_header": "FACTURE / INVOICE",
        "invoice_number": f"INV-2024-{random.randint(10000, 99999)}",
        "date": f"2024-{departure_month:02d}-{departure_day:02d}",
        "shipper_name": shipper["name"],
        "shipper_address": f"{shipper['city']}, {shipper['country']}",
        "receiver_name": receiver["name"],
        "receiver_address": f"{receiver['city']}, {receiver['country']}",
        "origin": str(route["origin"]),
        "destination": str(route["destination"]),
        "goods_description": str(goods["description"]),
        "quantity": quantity,
        "unit_weight_kg": float(goods["unit_weight"]),
        "total_weight_kg": total_weight,
        "transport_mode": str(route["mode"]),
        "distance_km": float(route["distance"]),
        "departure_date": f"2024-{departure_month:02d}-{departure_day:02d}",
        "arrival_date": (
            f"2024-{min(departure_month + (departure_day + transit_days) // 28, 12):02d}"
            f"-{(departure_day + transit_days) % 28 + 1:02d}"
        ),
        "currency": "EUR",
        "unit_price": unit_price,
        "total_cost": total_cost,
        "incoterms": random.choice(["EXW", "FOB", "CIF", "DDP", "DAP"]),
        "notes": f"Ref transport: TR-{random.randint(1000, 9999)}",
    }


def _generate_delivery_note_content(
    route: dict[str, Any],
    goods: dict[str, Any],
    shipper: dict[str, str],
    receiver: dict[str, str],
    quantity: int,
) -> dict[str, str | float | int | list[str] | dict[str, str]]:
    """Génère le contenu brut d'un bon de livraison simulé OCR.

    Args:
        route: Informations de route.
        goods: Informations sur la marchandise.
        shipper: Informations sur l'expéditeur.
        receiver: Informations sur le destinataire.
        quantity: Quantité de marchandise.

    Returns:
        Dictionnaire simulant le résultat OCR d'un bon de livraison.
    """
    total_weight = float(goods["unit_weight"]) * quantity
    departure_month = random.randint(1, 11)
    departure_day = random.randint(1, 28)
    transit_days = random.randint(1, 14)

    return {
        "document_header": "BON DE LIVRAISON / DELIVERY NOTE",
        "delivery_note_number": f"DN-2024-{random.randint(10000, 99999)}",
        "date": f"2024-{departure_month:02d}-{departure_day:02d}",
        "shipper": f"{shipper['name']} — {shipper['city']}",
        "consignee": f"{receiver['name']} — {receiver['city']}",
        "origin_warehouse": f"Entrepôt {route['origin']}",
        "destination_warehouse": f"Entrepôt {route['destination']}",
        "goods": str(goods["description"]),
        "packages_count": quantity,
        "gross_weight_kg": total_weight,
        "net_weight_kg": round(total_weight * 0.95, 1),
        "volume_m3": round(total_weight * 0.003, 2),
        "transport_type": str(route["mode"]),
        "estimated_distance_km": float(route["distance"]),
        "ship_date": f"2024-{departure_month:02d}-{departure_day:02d}",
        "expected_delivery": (
            f"2024-{min(departure_month + (departure_day + transit_days) // 28, 12):02d}"
            f"-{(departure_day + transit_days) % 28 + 1:02d}"
        ),
        "carrier": f"Carrier-{random.choice(['Alpha', 'Beta', 'Gamma', 'Delta'])}",
        "tracking_ref": f"TRK{random.randint(100000000, 999999999)}",
    }


def generate_mock_documents(count: int = 10, seed: int = 42) -> list[LogisticsDocument]:
    """Génère une liste de documents logistiques mock réalistes.

    Produit un mix de factures et de bons de livraison avec des données
    variées couvrant tous les modes de transport.

    Args:
        count: Nombre de documents à générer (défaut: 10).
        seed: Graine pour la reproductibilité (défaut: 42).

    Returns:
        Liste de LogisticsDocument avec contenu JSON réaliste.
    """
    random.seed(seed)
    documents: list[LogisticsDocument] = []

    for i in range(count):
        route = _ROUTES[i % len(_ROUTES)]
        goods = _GOODS[i % len(_GOODS)]
        shipper = _COMPANIES[i % len(_COMPANIES)]
        receiver = _COMPANIES[(i + 5) % len(_COMPANIES)]
        quantity = random.randint(1, 200)

        # Alterner entre factures et bons de livraison
        if i % 2 == 0:
            doc_type = DocumentType.INVOICE
            content = _generate_invoice_content(route, goods, shipper, receiver, quantity)
            filename = f"invoice_{i + 1:03d}.json"
        else:
            doc_type = DocumentType.DELIVERY_NOTE
            content = _generate_delivery_note_content(route, goods, shipper, receiver, quantity)
            filename = f"delivery_note_{i + 1:03d}.json"

        doc = LogisticsDocument(
            document_type=doc_type,
            raw_content=content,  # type: ignore[arg-type]
            source_filename=filename,
        )
        documents.append(doc)

    return documents


def save_mock_documents(
    documents: list[LogisticsDocument],
    output_dir: str = "data/mock",
) -> list[Path]:
    """Sauvegarde les documents mock en fichiers JSON individuels.

    Args:
        documents: Liste de documents à sauvegarder.
        output_dir: Répertoire de sortie.

    Returns:
        Liste des chemins de fichiers créés.

    Raises:
        OSError: Si le répertoire ne peut pas être créé.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    saved_paths: list[Path] = []
    for doc in documents:
        filepath = output_path / doc.source_filename
        with filepath.open("w", encoding="utf-8") as f:
            json.dump(
                doc.model_dump(mode="json"),
                f,
                indent=2,
                ensure_ascii=False,
                default=str,
            )
        saved_paths.append(filepath)

    return saved_paths


def generate_and_save(
    count: int = 10,
    output_dir: str = "data/mock",
    seed: int = 42,
) -> list[Path]:
    """Génère et sauvegarde les documents mock en une seule opération.

    Args:
        count: Nombre de documents à générer.
        output_dir: Répertoire de sortie.
        seed: Graine pour la reproductibilité.

    Returns:
        Liste des chemins de fichiers créés.
    """
    documents = generate_mock_documents(count=count, seed=seed)
    return save_mock_documents(documents, output_dir=output_dir)


if __name__ == "__main__":
    paths = generate_and_save()
    print(f"✅ {len(paths)} documents mock générés dans data/mock/")
    for p in paths:
        print(f"  → {p}")
