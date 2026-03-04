# EcoChain AI

**Optimisation de l'empreinte carbone Supply Chain par architecture Multi-Agent IA**

EcoChain AI analyse des documents logistiques (factures, bons de livraison), calcule les émissions CO2 Scope 3 avec les facteurs ADEME, et génère des recommandations de réduction via un pipeline multi-agent AGNO + Gemini 2.5 Flash.

---

## Lancement rapide

### 1. Prérequis

- **Python 3.12+**
- **Node.js 18+** (pour le frontend Next.js)
- **Clé API Google** → [Obtenir ici](https://aistudio.google.com/apikey)

### 2. Installation

```bash
# Cloner le repo
git clone https://github.com/<ton-user>/EcoChain.git
cd EcoChain

# Installer les dépendances Python (uv recommandé)
uv sync

# Ou avec pip
pip install -e ".[dev]"
```

### 3. Configurer la clé API

Crée un fichier `.env` à la racine :

```env
GOOGLE_API_KEY=ta-clé-api-ici
```

> La clé API est **obligatoire** : les agents AGNO (Extractor, Validator, Recommender) utilisent Gemini 2.5 Flash. Sans clé, le backend lèvera une erreur au démarrage ou lors de l'analyse.

### 4. Lancer l'application

**Terminal 1 — Backend API (FastAPI) :**

```bash
uv run uvicorn interfaces.api.main:app --reload --port 8000
```

```
INFO  | EcoChain AI API ready (AGNO agents)
INFO  | Uvicorn running on http://127.0.0.1:8000
```

**Terminal 2 — Frontend Next.js (recommandé) :**

```bash
cd interfaces/web && npm install && npm run dev
```

→ http://localhost:3000

**Alternative — Streamlit :**

```bash
uv run streamlit run interfaces/frontend/app.py --server.port 8501
```

→ http://localhost:8501

### 5. Variable d'environnement frontend

Pour le frontend Next.js, crée `interfaces/web/.env.local` si tu changes le port backend :

```env
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
```

---

## Comment utiliser

### Dashboard Next.js (recommandé)

1. **Upload PDF** — Glisse-dépose ou sélectionne un PDF depuis `interfaces/web/public/test-documents/` ou `data/pdfs/`
2. **Mock Documents** — Choisis `invoice_001.json` ou un autre, puis **Analyze One** ou **Batch**
3. **Analyze Uploaded PDF** — Lance le pipeline sur le PDF sélectionné
4. **Résultat** — Métriques CO2, graphique comparatif modal, recommandations, Agent Activity Log en temps réel (SSE)

### Documents PDF de test

5 PDFs pré-générés sont disponibles dans `interfaces/web/public/test-documents/` :

| Fichier | Trajet | Mode | Poids |
|---------|--------|------|-------|
| invoice_eco_001.pdf | Stuttgart → Torino | Road | 1200 kg |
| delivery_note_eco_002.pdf | Saint-Nazaire → Göteborg | Maritime | 3 t |
| invoice_eco_003.pdf | Shenzhen → Paris CDG | Air | 250 kg |
| delivery_note_eco_004.pdf | Tallinn → Duisburg | Rail | 36 t |
| invoice_eco_005.pdf | Ludwigshafen → Antwerpen | River | 22 t |

Régénérer les PDFs :

```bash
uv run python scripts/generate_pdfs.py
cp data/pdfs/*.pdf interfaces/web/public/test-documents/
```

---

## Logs agents en temps réel

### Dans le frontend

L’**Agent Activity Log** s’affiche en temps réel pendant l’analyse via SSE :
- Loader (cube PrismFlux + terminal) pendant le traitement
- Logs streamés au fil de l’eau : Extractor → Validator → CarbonCalculator → Recommender

### Endpoints API

```bash
# Stream SSE
curl -N http://localhost:8000/api/v1/events/stream

# Historique
curl http://localhost:8000/api/v1/events/history | python -m json.tool
```

### Test rapide API

```bash
curl -s -X POST http://localhost:8000/api/v1/documents/process \
  -H "Content-Type: application/json" \
  -d '{
    "document_type": "invoice",
    "raw_content": {
      "raw_text": "Commercial Invoice. From: Hamburg. To: Saint-Priest. Weight: 10120 kg. Distance: 1180 km. Mode: Road. Carrier: EuroRoad."
    },
    "source_filename": "test.pdf"
  }' | python -m json.tool
```

> Pour les documents JSON structurés, utilise les clés attendues par l’extracteur (origin, destination, weight_kg, distance_km, transport_mode, etc.) ou `raw_text` pour du texte OCR brut.

---

## Architecture

```
EcoChain/
├── application/
│   ├── agents/               # Agents AGNO (Gemini 2.5 Flash)
│   │   ├── extractor.py      # Extraction entités (structured output)
│   │   ├── validator.py      # Validation sémantique
│   │   ├── recommender.py    # Recommandations personnalisées
│   │   └── orchestrator.py  # Orchestration du pipeline
│   ├── calculators/
│   │   └── carbon_calculator.py
│   └── use_cases/
│       └── process_document.py
│
├── domain/
│   ├── models.py
│   └── constants.py          # Facteurs ADEME
│
├── infrastructure/
│   ├── logging/
│   │   └── event_logger.py   # Logger SSE
│   └── llm/
│       └── gemini_client.py  # (legacy, non utilisé par AGNO)
│
├── interfaces/
│   ├── api/                  # FastAPI
│   │   ├── main.py
│   │   ├── dependencies.py
│   │   └── routers/
│   │       ├── documents.py
│   │       └── events.py     # SSE stream + history
│   ├── frontend/             # Streamlit (alternatif)
│   │   └── app.py
│   └── web/                  # Next.js (frontend principal)
│       ├── src/
│       │   ├── app/          # Routes: /, /dashboard, /dashboard/documents, /dashboard/settings
│       │   ├── components/
│       │   └── lib/          # api.ts, pdf-extract.ts, documents-store
│       └── public/
│           └── test-documents/  # PDFs de test
│
├── data/
│   ├── mock/                 # Documents JSON
│   └── pdfs/                 # PDFs générés par scripts
│
├── scripts/
│   └── generate_pdfs.py
├── tests/
└── pyproject.toml
```

### Pipeline Multi-Agent

```
Document (PDF → raw_text) ou JSON
       │
       ▼
  ┌─────────────┐    ┌─────────────┐    ┌──────────────┐    ┌──────────────┐
  │  Extractor   │ →  │  Validator   │ →  │   Carbon     │ →  │ Recommender  │
  │  (AGNO +     │    │  (AGNO +     │    │  Calculator  │    │  (AGNO +     │
  │   Gemini)    │    │   Gemini)    │    │  (ADEME)     │    │   Gemini)    │
  └─────────────┘    └─────────────┘    └──────────────┘    └──────────────┘
                                                                    │
                                                                    ▼
                                              CarbonReport + mode_comparisons + recommendations
```

### Graphique "Comparaison modale"

Le graphique **Émissions par mode** est dynamique et basé sur les données extraites du PDF :
- Pour **ce trajet** (poids + distance du document), simulation des émissions si chaque mode avait été utilisé
- Barre **dorée** = mode actuel du document
- Barre **verte** = mode le moins émetteur

---

## API Endpoints

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `POST` | `/api/v1/documents/process` | Analyser un document |
| `POST` | `/api/v1/documents/batch` | Analyser N documents en parallèle |
| `GET` | `/api/v1/documents/{id}/results` | Récupérer les résultats |
| `GET` | `/api/v1/events/stream` | Stream SSE logs temps réel |
| `GET` | `/api/v1/events/history` | Historique des événements |
| `GET` | `/health` | Health check |
| `GET` | `/docs` | Swagger UI |

---

## Tests

```bash
uv run pytest tests/ -v

# Ou
pytest tests/ -v
```

---

## Facteurs d'émission CO2 (ADEME)

| Mode | Facteur (kgCO2e/t.km) | Exemple 10t × 1000km |
|------|------------------------|----------------------|
| Maritime | 0.0160 | 160 kgCO2e |
| Rail | 0.0225 | 225 kgCO2e |
| Fluvial | 0.0310 | 310 kgCO2e |
| Route | 0.0621 | 621 kgCO2e |
| Aérien | 1.0600 | 10 600 kgCO2e |

---

## Stack technique

| Composant | Technologie |
|-----------|-------------|
| **Backend** | Python 3.12, FastAPI, Pydantic v2 |
| **IA** | AGNO (multi-agent async), google-genai |
| **LLM** | Gemini 2.5 Flash |
| **Frontend** | Next.js 16, TypeScript, Tailwind, shadcn/ui, Recharts, Framer Motion |
| **PDF** | pdf.js (client), pypdf (serveur), reportlab (génération) |
| **Tests** | pytest, pytest-asyncio |
| **Qualité** | ruff, mypy (strict) |
