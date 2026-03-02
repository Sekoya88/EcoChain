"""Tests d'intégration pour les endpoints API.

Utilise httpx.AsyncClient pour tester les routes FastAPI.
Les tests fonctionnent sans clé API (fallback déterministe).
"""

from __future__ import annotations

import pytest
import httpx
from httpx import ASGITransport

from interfaces.api.main import app
from interfaces.api.dependencies import reset_dependencies


@pytest.fixture(autouse=True)
def _reset() -> None:
    """Reset les dépendances avant chaque test."""
    reset_dependencies()


@pytest.fixture
async def client() -> httpx.AsyncClient:
    """Fixture client HTTP async pour les tests."""
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


class TestHealthEndpoints:
    """Tests des endpoints système."""

    @pytest.mark.asyncio
    async def test_health_check(self, client: httpx.AsyncClient) -> None:
        """Test GET /health retourne 200."""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_root(self, client: httpx.AsyncClient) -> None:
        """Test GET / retourne les infos de l'API."""
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "EcoChain AI"
        assert "docs" in data


class TestDocumentProcessing:
    """Tests des endpoints de traitement de documents."""

    @pytest.mark.asyncio
    async def test_process_document(self, client: httpx.AsyncClient) -> None:
        """Test POST /api/v1/documents/process avec un document valide."""
        payload = {
            "document_type": "invoice",
            "raw_content": {
                "origin": "Hamburg",
                "destination": "Marseille",
                "total_weight_kg": 15000.0,
                "distance_km": 1450.0,
                "transport_mode": "road",
                "shipper_name": "TransEurope Logistics",
                "receiver_name": "MedFreight SAS",
                "departure_date": "2024-03-15",
                "arrival_date": "2024-03-17",
                "goods_description": "Composants électroniques",
                "currency": "EUR",
                "total_cost": 2500.0,
            },
            "source_filename": "test_invoice.json",
        }

        response = await client.post("/api/v1/documents/process", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["report"] is not None
        assert data["report"]["total_co2_kg"] > 0
        assert len(data["report"]["recommendations"]) == 3

    @pytest.mark.asyncio
    async def test_process_delivery_note(self, client: httpx.AsyncClient) -> None:
        """Test traitement d'un bon de livraison."""
        payload = {
            "document_type": "delivery_note",
            "raw_content": {
                "shipper": "Nordic Supply — Gothenburg",
                "consignee": "Alpine Cargo — Zurich",
                "origin_warehouse": "Entrepôt Gothenburg",
                "destination_warehouse": "Entrepôt Zurich",
                "gross_weight_kg": 5000.0,
                "estimated_distance_km": 1900.0,
                "transport_type": "road",
                "ship_date": "2024-06-01",
                "expected_delivery": "2024-06-04",
                "goods": "Équipements photovoltaïques",
            },
            "source_filename": "test_delivery.json",
        }

        response = await client.post("/api/v1/documents/process", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    @pytest.mark.asyncio
    async def test_get_results_not_found(self, client: httpx.AsyncClient) -> None:
        """Test GET /results pour un document inexistant → 404."""
        response = await client.get("/api/v1/documents/nonexistent-id/results")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_batch_process(self, client: httpx.AsyncClient) -> None:
        """Test POST /api/v1/documents/batch avec 2 documents."""
        payload = {
            "documents": [
                {
                    "document_type": "invoice",
                    "raw_content": {
                        "origin": "Paris",
                        "destination": "Berlin",
                        "total_weight_kg": 8000.0,
                        "distance_km": 1050.0,
                        "transport_mode": "road",
                        "shipper_name": "Acme",
                        "receiver_name": "Beta",
                        "departure_date": "2024-01-01",
                        "arrival_date": "2024-01-03",
                        "goods_description": "Electronics",
                        "currency": "EUR",
                        "total_cost": 1500.0,
                    },
                },
                {
                    "document_type": "invoice",
                    "raw_content": {
                        "origin": "Rotterdam",
                        "destination": "Shanghai",
                        "total_weight_kg": 50000.0,
                        "distance_km": 19500.0,
                        "transport_mode": "maritime",
                        "shipper_name": "Atlantic",
                        "receiver_name": "Pacific",
                        "departure_date": "2024-02-01",
                        "arrival_date": "2024-03-15",
                        "goods_description": "Machinery",
                        "currency": "USD",
                        "total_cost": 25000.0,
                    },
                },
            ]
        }

        response = await client.post("/api/v1/documents/batch", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["total_documents"] == 2
        assert len(data["reports"]) == 2
        assert data["total_co2_kg"] > 0

    @pytest.mark.asyncio
    async def test_empty_batch_rejected(self, client: httpx.AsyncClient) -> None:
        """Test que le batch vide est rejeté (validation Pydantic)."""
        payload = {"documents": []}
        response = await client.post("/api/v1/documents/batch", json=payload)
        assert response.status_code == 422  # Validation error
