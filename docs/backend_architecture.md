# Backend Architecture

## Folder Structure

```text
backend/
├── api/routes/          FastAPI endpoints
├── services/            Business workflows
├── providers/           External AI provider clients
├── parsers/             AI response parsing and validation
├── prompts/             Prompt files and prompt versions
├── models/              SQLAlchemy models
├── schemas/             Pydantic request/response schemas
├── database/            Engine, sessions, schema initialization
├── storage/             Original and processed files
├── config/              Settings, logging, storage paths
├── middleware/          Request logging
├── utils/               File, image, PDF, UUID helpers
├── tests/               Backend tests
├── logs/                Application logs
├── migrations/          Alembic migrations
├── main.py
├── requirements.txt
└── .env
```

## Processing Flow

```mermaid
sequenceDiagram
    participant User
    participant API
    participant Storage
    participant Preprocess
    participant MedGemma
    participant Parser
    participant SQLite

    User->>API: POST /upload
    API->>Storage: Save original file
    API->>Preprocess: Normalize image/PDF/text
    API->>SQLite: Save document metadata
    User->>API: POST /extract
    API->>Preprocess: Rebuild processed inputs
    API->>MedGemma: Send prompt + inputs
    MedGemma-->>API: Raw model response
    API->>Parser: Parse and validate JSON
    API->>SQLite: Save extraction and run metadata
    User->>API: PUT /review/{id}
    API->>SQLite: Save review status and reviewed data
```
