# Documents PDF de test — EcoChain AI

Ces PDFs sont générés par `scripts/generate_pdfs.py`. Utilise-les pour tester l’extraction et le calcul CO2 sur le dashboard.

## Fichiers

| Fichier | Trajet | Mode | Poids | Distance |
|---------|--------|------|-------|----------|
| `invoice_eco_001.pdf` | Stuttgart → Torino | Road | 1200 kg | 620 km |
| `delivery_note_eco_002.pdf` | Saint-Nazaire → Göteborg | Maritime | 3000 kg | 2800 km |
| `invoice_eco_003.pdf` | Shenzhen → Paris CDG | Air | 250 kg | 9500 km |
| `delivery_note_eco_004.pdf` | Tallinn → Duisburg | Rail | 36 t | 1850 km |
| `invoice_eco_005.pdf` | Ludwigshafen → Antwerpen | River | 22 t | 580 km |

## Usage

1. Glisse-dépose un PDF sur la zone d’upload du dashboard
2. Ou clique pour sélectionner un fichier depuis `interfaces/web/public/test-documents/`

## Régénérer

```bash
uv run python scripts/generate_pdfs.py
cp data/pdfs/*.pdf interfaces/web/public/test-documents/
```
