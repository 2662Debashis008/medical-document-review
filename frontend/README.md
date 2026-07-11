# Medical Document Review Frontend

Next.js workbench for uploading, extracting, reviewing, and exporting prescription and X-ray documents.

## Setup

```powershell
npm install
npm run dev
```

Open `http://localhost:3000`.

Set `NEXT_PUBLIC_API_BASE_URL` when the FastAPI backend is not running at `http://127.0.0.1:8000`.

## Features

- Dashboard statistics and recent uploads
- Upload for JPG, JPEG, PNG, PDF, and TXT
- Prescription and X-ray document categories
- Document search, filters, preview, deletion
- AI extraction trigger
- Editable JSON review data
- Approve, reject, and needs-changes workflow
- Metadata display
- JSON and CSV export links
- API status and prompt information
