# Deployment Guide

## Local Development

Backend:

```powershell
cd backend
.\venv\Scripts\python.exe -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Frontend:

```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`.

## Environment

Create `backend/.env` with:

```env
DATABASE_URL=sqlite:///./medical_document.db
MEDGEMMA_API_URL=https://your-bifrost-endpoint
MEDGEMMA_API_KEY=your-api-key
MODEL_NAME=medgemma:4b
```

The frontend uses `NEXT_PUBLIC_API_BASE_URL`, defaulting to `http://127.0.0.1:8000`.

## Docker Compose

```powershell
docker compose up --build
```

Backend runs on `http://localhost:8000`; frontend runs on `http://localhost:3000`.

## Known Limitations

- X-ray PDF routing is automatic: PDFs with embedded text use the report prompt, image-only PDFs use page-by-page X-ray image extraction.
- MedGemma/Bifrost must return JSON compatible with the schemas in `backend/schemas/workflow.py`.
- SQLite is suitable for this local workflow; move to a server database before multi-user production deployment.

## Future Azure Foundry Notes

Place the Azure Foundry provider behind the same `MedGemmaProvider.infer` interface and keep prompt selection, parsing, metadata, and review workflow unchanged.
