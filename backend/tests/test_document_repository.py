from database.session import SessionLocal
from repositories.document_repository import DocumentRepository

db = SessionLocal()

sample = {
    "document_category": "prescription",
    "file_type": "pdf",
    "original_filename": "sample.pdf",
    "stored_filename": "abc123.pdf",
    "storage_path": "storage/prescriptions/pdfs/abc123.pdf",
    "status": "uploaded"
}

# Create document
document = DocumentRepository.create(db, sample)

print("Created Document")
print(document.id)

# Get all documents
documents = DocumentRepository.get_all(db)

print("\nTotal Documents Before Delete:")
print(len(documents))

# Delete the created document
DocumentRepository.delete(db, document.id)

# Get all documents again
documents = DocumentRepository.get_all(db)

print("\nTotal Documents After Delete:")
print(len(documents))

db.close()