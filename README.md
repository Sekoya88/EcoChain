# � EcoChain AI

**Optimisation de l'empreinte carbone Supply Chain par architecture Multi-Agent IA**

EcoChain AI analyse des documents logistiques (factures, bons de livraison), calcule les émissions CO2 Scope 3 avec les facteurs ADEME, et génère des recommandations de réduction via un pipeline multi-agent AGNO + Gemini 2.5 Flash.

---

## 🚀 Lancement rapide

### 1. Prérequis

- **Python 3.12+**
- **Clé API Google** → [Obtenir ici](https://aistudio.google.com/apikey)

### 2. Installation

```bash
# Cloner le repo
git clone https://github.com/<ton-user>/EcoChain.git
cd EcoChain

# Créer l'environnement virtuel et installer les dépendances
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### 3. Configurer la clé API

```bash
# Copier le fichier d'exemple
cp .env.example .env

# Éditer .env et ajouter ta clé API Google
nano .env   # ou code .env
```

Le fichier `.env` doit contenir :

```env
GOOGLE_API_KEY=ta-clé-api-ici
```

> ⚠️ **Sans clé API**, les agents AGNO utilisent un **fallback déterministe** (pas de LLM). Les résultats marchent mais sont moins précis.

### 4. Lancer l'application

Tu as besoin de **2 terminaux** :

**Terminal 1 — Backend API (FastAPI) :**

```bash
source .venv/bin/activate
uvicorn interfaces.api.main:app --reload --port 8000
```

Tu devrais voir :

```
INFO  | EcoChain AI API ready (AGNO agents)
INFO  | Uvicorn running on http://0.0.0.0:8000
```

**Terminal 2 — Frontend (Streamlit) :**

```bash
source .venv/bin/activate
streamlit run interfaces/frontend/app.py --server.port 8501
```

Tu devrais voir :

```
You can now view your Streamlit app in your browser.
Local URL: http://localhost:8501
```

### 5. Ouvrir dans le navigateur

**→ [http://localhost:8501](http://localhost:8501)**

---

## 🔍 Comment utiliser

1. **Sidebar gauche** → Sélectionne un document (15 documents de test dispo)
2. **"Analyze Document"** → Lance le pipeline multi-agent
3. **Observe** le pipeline stepper en temps réel (Extract → Validate → Calculate → Recommend)
4. **Résultat** → Métriques CO2, graphiques, recommandations, logs agents

### Upload PDF

Tu peux aussi uploader un PDF de test depuis `data/pdfs/` via le bouton "Browse files" dans la sidebar.

Pour générer de nouveaux PDFs de test :

```bash
python scripts/generate_pdfs.py
```

---

## 📊 Voir les logs agents en temps réel

### Option 1 : Dans le frontend

Les logs s'affichent en bas du rapport après analyse. Chaque agent a sa couleur :

- 🔵 **Extractor** — Extraction des données du document
- 🟡 **Validator** — Validation des règles métier
- 🟢 **CarbonCalculator** — Calcul CO2 (facteurs ADEME)
- 🟣 **Recommender** — Génération des recommandations IA

### Option 2 : Endpoint SSE (streaming temps réel)

```bash
# Stream les événements en direct dans le terminal
curl -N http://localhost:8000/api/v1/events/stream
```

### Option 3 : Historique des événements

```bash
# Récupérer les derniers logs
curl http://localhost:8000/api/v1/events/history | python -m json.tool
```

### Option 4 : Logs du backend (terminal 1)

Le terminal backend affiche tous les logs structurés avec timestamps :

```
2024-06-15 10:30:12 | INFO | Extractor | Extraction réussie: Hamburg → Marseille
2024-06-15 10:30:13 | INFO | Validator | 5 règles vérifiées, score: 95%
2024-06-15 10:30:14 | INFO | CarbonCalculator | CO2: 1350.7 kgCO2e (route)
2024-06-15 10:30:16 | INFO | Recommender | 3 recommandations générées
```

---

## 🔑 Vérifier que la clé API est utilisée

### Test rapide

```bash
# Envoie un document de test au backend
curl -s -X POST http://localhost:8000/api/v1/documents/process \
  -H "Content-Type: application/json" \
  -d '{
    "document_type": "invoice",
    "raw_content": {
      "origin": "Paris",
      "destination": "Berlin",
      "total_weight_kg": 5000,
      "distance_km": 1050,
      "transport_mode": "road",
      "shipper_name": "Test Corp",
      "receiver_name": "Demo GmbH",
      "departure_date": "2024-01-01",
      "arrival_date": "2024-01-03",
      "goods_description": "Test goods",
      "currency": "EUR",
      "total_cost": 1500
    }
  }' | python -m json.tool
```

**Si la clé API fonctionne :** Les recommandations seront détaillées et contextuelles (générées par Gemini).

**Si la clé API NE fonctionne PAS :** Les recommandations seront génériques (3 recommandations de fallback prédéfinies) et tu verras dans les logs backend : `WARNING | Using deterministic fallback`.

---

## 🏛️ Architecture

```
EcoChain/
├── application/              # Couche Application
│   ├── agents/               # Agents AGNO (Gemini 2.5 Flash)
│   │   ├── extractor.py      # Agent 1: Extraction données
│   │   ├── validator.py      # Agent 2: Validation règles métier
│   │   ├── recommender.py    # Agent 3: Recommandations IA
│   │   └── orchestrator.py   # Orchestrateur du pipeline
│   ├── calculators/
│   │   └── carbon_calculator.py  # Calcul CO2 (facteurs ADEME)
│   └── use_cases/
│       └── process_document.py   # Use case principal
│
├── domain/                   # Couche Domaine
│   ├── models.py             # Modèles Pydantic v2
│   └── constants.py          # Facteurs ADEME, benchmarks
│
├── infrastructure/           # Couche Infrastructure
│   └── logging/
│       └── event_logger.py   # Logger SSE temps réel
│
├── interfaces/               # Couche Interfaces
│   ├── api/                  # Backend FastAPI
│   │   ├── main.py           # App FastAPI + middleware
│   │   ├── dependencies.py   # Injection de dépendances
│   │   └── routers/          # Endpoints REST + SSE
│   └── frontend/
│       └── app.py            # Dashboard Streamlit
│
├── data/
│   ├── mock/                 # 10 documents JSON de test
│   └── pdfs/                 # 5 PDFs générés (reportlab)
│
├── tests/                    # 36 tests (unit + intégration)
├── scripts/
│   └── generate_pdfs.py      # Générateur de PDFs de test
├── docs/
│   └── architecture.drawio   # Diagramme d'architecture
└── pyproject.toml            # Config project + dépendances
```

### Pipeline Multi-Agent

```
Document JSON/PDF
       │
       ▼
  ┌─────────────┐    ┌─────────────┐    ┌──────────────┐    ┌──────────────┐
  │  Extractor   │ →  │  Validator   │ →  │   Carbon     │ →  │ Recommender  │
  │  (AGNO +     │    │  (5 règles   │    │  Calculator  │    │  (AGNO +     │
  │   Gemini)    │    │   + Gemini)  │    │  (ADEME)     │    │   Gemini)    │
  └─────────────┘    └─────────────┘    └──────────────┘    └──────────────┘
                                                                    │
                                                                    ▼
                                                          Rapport CO2 + Recommandations
```

---

## 📡 API Endpoints

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `POST` | `/api/v1/documents/process` | Analyser un document |
| `POST` | `/api/v1/documents/batch` | Analyser N documents en parallèle |
| `GET` | `/api/v1/documents/{id}/results` | Récupérer les résultats |
| `GET` | `/api/v1/events/stream` | Stream SSE logs temps réel |
| `GET` | `/api/v1/events/history` | Historique des événements |
| `GET` | `/health` | Health check |
| `GET` | `/docs` | Documentation Swagger |

---

## 🧪 Tests

```bash
# Tous les tests (36)
pytest tests/ -v

# Tests unitaires seulement
pytest tests/unit/ -v

# Tests d'intégration
pytest tests/integration/ -v
```

---

## 🌱 Facteurs d'émission CO2 (ADEME)

| Mode | Facteur (kgCO2e/t.km) | Exemple 10t × 1000km |
|------|------------------------|----------------------|
| � Maritime | 0.0160 | 160 kgCO2e |
| � Rail | 0.0225 | 225 kgCO2e |
| 🛥️ Fluvial | 0.0310 | 310 kgCO2e |
| 🚛 Route | 0.0621 | 621 kgCO2e |
| ✈️ Aérien | 1.0600 | 10,600 kgCO2e |

---

## ⚙️ Stack technique

| Composant | Technologie |
|-----------|-------------|
| **Langage** | Python 3.12 (type hints stricts) |
| **Framework IA** | AGNO (multi-agent async) |
| **LLM** | Gemini 2.5 Flash (fallback: déterministe) |
| **Backend** | FastAPI (async) + Pydantic v2 |
| **Frontend** | Streamlit + Plotly |
| **Tests** | pytest + pytest-asyncio (36 tests) |
| **Qualité** | ruff, mypy (strict) |
