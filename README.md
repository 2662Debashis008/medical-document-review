# Medical Document Review

Full-stack FastAPI and Next.js application for medical document upload, AI extraction, human review, metadata tracking, and export.

## Supported Documents

- Prescription image, text, and multi-page PDF
- X-ray image
- X-ray image-only multi-page PDF
- X-ray report text and multi-page report PDF

## Architecture

- `backend/`: FastAPI, SQLite, SQLAlchemy, Alembic, storage, preprocessing, MedGemma/Bifrost integration, parsing, review, metadata, export
- `frontend/`: Next.js, React, TypeScript, Tailwind CSS, React Query, Axios, Zustand, React Hook Form, Zod
- `docs/`: architecture, API, database, workflow, deployment notes
- `diagrams/`: architecture, API, database, workflow diagrams

## Run Locally

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

## Docker

```powershell
docker compose up --build
```

## Backend Tests

```powershell
cd backend
.\venv\Scripts\python.exe -m pytest -q
```

## Important Workflow

1. Upload a prescription or X-ray document.
2. The backend validates and preprocesses the file.
3. Extraction sends the correct prompt and image/text payload to MedGemma/Bifrost.
4. The parser validates structured JSON.
5. A reviewer edits, approves, rejects, or requests changes.
6. Reviewed records can be exported as JSON or CSV.
