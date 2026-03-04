# EcoChain AI — Web (Next.js)

Frontend React/Next.js avec thème **Kodama Grove** (21st.dev).

## PDF Worker

Le worker pdf.js est copié dans `public/pdf.worker.min.mjs`. Si tu mets à jour `pdfjs-dist`, recopie-le :
```bash
cp node_modules/pdfjs-dist/build/pdf.worker.min.mjs public/
```

## Stack

- Next.js 16 (App Router)
- TypeScript
- Tailwind CSS + shadcn/ui
- Framer Motion
- Recharts
- pdf.js (extraction PDF côté client)
- react-dropzone

## Démarrage

```bash
# Depuis la racine du projet
cd interfaces/web
npm install
npm run dev
```

Ouvre [http://localhost:3000](http://localhost:3000).

## Backend

Le frontend appelle l'API FastAPI. Démarrer le backend :

```bash
uv run uvicorn interfaces.api.main:app --reload
```

Variable d'environnement : `NEXT_PUBLIC_BACKEND_URL=http://localhost:8000` (défaut).

## Routes

- `/` — Landing avec ContainerScroll (scroll animé)
- `/dashboard` — Analyse documents, upload PDF, métriques, recommandations

## Thème Kodama Grove

Palette définie dans `src/app/globals.css` : verts forêt, mousse, glow organique.
